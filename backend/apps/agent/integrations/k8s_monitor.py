"""
Kubernetes monitoring integration for Django.

This module provides integration with Kubernetes API to monitor
cluster resources and feed events into Kafka.
"""

import json
import logging
import os
import threading
import time
from typing import Dict, Any, List, Optional, Union, Callable
from django.conf import settings
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class K8sMonitorConfig(BaseModel):
    """Kubernetes monitor configuration."""
    
    namespace: str = Field(default="default")
    poll_interval: int = Field(default=30)  # seconds
    resources_to_monitor: List[str] = Field(
        default=["pods", "services", "deployments", "statefulsets", "configmaps", "secrets"]
    )
    use_mock: bool = Field(default=False)

class K8sMonitor:
    """Monitor for Kubernetes resources."""
    
    def __init__(self, config: Optional[K8sMonitorConfig] = None, kafka_client=None):
        """Initialize the Kubernetes monitor."""
        self.config = config or self._get_default_config()
        self._kafka_client = kafka_client
        self._running = False
        self._monitor_thread = None
        
        self._in_kubernetes = os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/token')
        
        if not self._in_kubernetes:
            logger.warning("Not running in Kubernetes, using mock mode")
            self._use_mock = True
        else:
            self._use_mock = self.config.use_mock
        
        if self._use_mock:
            logger.warning("Kubernetes monitor running in mock mode")
    
    def _get_default_config(self) -> K8sMonitorConfig:
        """Get the default configuration from settings."""
        if os.environ.get('CI') == 'true':
            use_mock = True
        else:
            try:
                import subprocess
                result = subprocess.run(
                    ["kubectl", "version", "--client"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                use_mock = result.returncode != 0
            except (subprocess.SubprocessError, FileNotFoundError):
                use_mock = True
        
        return K8sMonitorConfig(
            namespace=getattr(settings, 'K8S_MONITOR_NAMESPACE', 'default'),
            poll_interval=getattr(settings, 'K8S_MONITOR_POLL_INTERVAL', 30),
            resources_to_monitor=getattr(
                settings, 
                'K8S_MONITOR_RESOURCES', 
                ["pods", "services", "deployments", "statefulsets", "configmaps", "secrets"]
            ),
            use_mock=use_mock
        )
    
    def _get_resource_status(self, resource_type: str) -> List[Dict[str, Any]]:
        """Get the status of a Kubernetes resource."""
        if self._use_mock:
            return self._get_mock_resource_status(resource_type)
        
        try:
            import subprocess
            result = subprocess.run(
                [
                    "kubectl", "get", resource_type,
                    "-n", self.config.namespace,
                    "-o", "json"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            import json
            resources = json.loads(result.stdout)
            
            return resources.get("items", [])
        except Exception as e:
            logger.error(f"Error getting {resource_type} status: {e}")
            return []
    
    def _get_mock_resource_status(self, resource_type: str) -> List[Dict[str, Any]]:
        """Get mock status for a Kubernetes resource."""
        if resource_type == "pods":
            return [
                {
                    "metadata": {
                        "name": "kafka-broker-0",
                        "namespace": "default",
                        "uid": "12345678-1234-1234-1234-123456789012"
                    },
                    "status": {
                        "phase": "Running",
                        "conditions": [
                            {
                                "type": "Ready",
                                "status": "True"
                            }
                        ]
                    }
                },
                {
                    "metadata": {
                        "name": "doris-fe-0",
                        "namespace": "default",
                        "uid": "12345678-1234-1234-1234-123456789013"
                    },
                    "status": {
                        "phase": "Running",
                        "conditions": [
                            {
                                "type": "Ready",
                                "status": "True"
                            }
                        ]
                    }
                }
            ]
        elif resource_type == "services":
            return [
                {
                    "metadata": {
                        "name": "kafka-broker",
                        "namespace": "default",
                        "uid": "12345678-1234-1234-1234-123456789014"
                    },
                    "spec": {
                        "type": "ClusterIP",
                        "ports": [
                            {
                                "port": 9092,
                                "targetPort": 9092
                            }
                        ]
                    }
                },
                {
                    "metadata": {
                        "name": "doris-fe",
                        "namespace": "default",
                        "uid": "12345678-1234-1234-1234-123456789015"
                    },
                    "spec": {
                        "type": "ClusterIP",
                        "ports": [
                            {
                                "port": 9030,
                                "targetPort": 9030
                            }
                        ]
                    }
                }
            ]
        elif resource_type == "deployments":
            return [
                {
                    "metadata": {
                        "name": "kafka-broker",
                        "namespace": "default",
                        "uid": "12345678-1234-1234-1234-123456789016"
                    },
                    "status": {
                        "replicas": 1,
                        "availableReplicas": 1,
                        "readyReplicas": 1
                    }
                },
                {
                    "metadata": {
                        "name": "zookeeper",
                        "namespace": "default",
                        "uid": "12345678-1234-1234-1234-123456789017"
                    },
                    "status": {
                        "replicas": 1,
                        "availableReplicas": 1,
                        "readyReplicas": 1
                    }
                }
            ]
        else:
            return []
    
    def _monitor_loop(self):
        """Monitor loop for Kubernetes resources."""
        while self._running:
            try:
                for resource_type in self.config.resources_to_monitor:
                    resources = self._get_resource_status(resource_type)
                    
                    if not resources:
                        continue
                    
                    if self._kafka_client:
                        from .kafka import KafkaMessage
                        
                        message = KafkaMessage(
                            topic=f"k8s-{resource_type}",
                            value={
                                "timestamp": int(time.time()),
                                "resource_type": resource_type,
                                "namespace": self.config.namespace,
                                "resources": resources
                            }
                        )
                        
                        self._kafka_client.produce(message)
                    
                    logger.debug(f"Monitored {len(resources)} {resource_type} in {self.config.namespace} namespace")
            
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
            
            time.sleep(self.config.poll_interval)
    
    def start_monitor(self) -> bool:
        """Start the monitor loop."""
        if self._running:
            logger.warning("Monitor already running")
            return True
        
        self._running = True
        
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        
        logger.info(f"Started Kubernetes monitor for {self.config.namespace} namespace")
        return True
    
    def stop_monitor(self) -> bool:
        """Stop the monitor loop."""
        if not self._running:
            logger.warning("Monitor not running")
            return True
        
        self._running = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None
        
        logger.info(f"Stopped Kubernetes monitor for {self.config.namespace} namespace")
        return True
    
    def get_resource_status(self, resource_type: str) -> List[Dict[str, Any]]:
        """Get the status of a Kubernetes resource."""
        return self._get_resource_status(resource_type)
    
    def __enter__(self):
        """Context manager entry."""
        self.start_monitor()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitor()
