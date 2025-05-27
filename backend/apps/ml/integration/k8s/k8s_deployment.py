"""
Kubernetes deployment utilities for RLLM models.

This module provides utilities for deploying RLLM models to Kubernetes
using KServe InferenceService.
"""

import os
import logging
import yaml
import tempfile
from typing import Dict, Any, Optional, List

from kubernetes import client, config
from kubernetes.client.rest import ApiException


class K8sDeployment:
    """Kubernetes deployment utilities for RLLM models."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        mock_mode: bool = False,
    ):
        """
        Initialize Kubernetes deployment utilities.

        Args:
            logger: Logger
            mock_mode: Whether to run in mock mode (for testing without a Kubernetes cluster)
        """
        self.logger = logger or logging.getLogger("K8sDeployment")
        self.mock_mode = mock_mode
        
        try:
            config.load_incluster_config()
            self.logger.info("Using in-cluster Kubernetes configuration")
            self._k8s_available = True
        except config.ConfigException:
            try:
                config.load_kube_config()
                self.logger.info("Using kubeconfig for Kubernetes configuration")
                self._k8s_available = True
            except config.ConfigException:
                self.logger.warning("Failed to load Kubernetes config: Invalid kube-config file. No configuration found.")
                self.logger.info("Running in local-only mode")
                self._k8s_available = False
                self.mock_mode = True
        
        if self._k8s_available and not self.mock_mode:
            self.api_client = client.ApiClient()
            self.custom_api = client.CustomObjectsApi(self.api_client)
            self.core_api = client.CoreV1Api(self.api_client)
            self.logger.info("Initialized Kubernetes deployment utilities")
        else:
            self.api_client = None
            self.custom_api = None
            self.core_api = None
            self.logger.info("Initialized Kubernetes deployment utilities in mock mode")

    async def create_namespace(self, namespace: str) -> bool:
        """
        Create Kubernetes namespace if it doesn't exist.

        Args:
            namespace: Namespace name

        Returns:
            Success status
        """
        if self.mock_mode or not self._k8s_available:
            self.logger.info(f"[MOCK] Created namespace: {namespace}")
            return True
            
        try:
            namespaces = self.core_api.list_namespace()
            existing_namespaces = [ns.metadata.name for ns in namespaces.items]
            
            if namespace in existing_namespaces:
                self.logger.info(f"Namespace {namespace} already exists")
                return True
            
            namespace_manifest = {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {
                    "name": namespace,
                },
            }
            
            self.core_api.create_namespace(namespace_manifest)
            self.logger.info(f"Created namespace: {namespace}")
            
            return True
        except ApiException as e:
            self.logger.error(f"Error creating namespace: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error creating namespace: {e}")
            return False

    async def deploy_inference_service(
        self,
        model_path: str,
        model_name: str,
        namespace: str = "ml-infrastructure",
        storage_uri: Optional[str] = None,
    ) -> bool:
        """
        Deploy KServe InferenceService for RLLM model.

        Args:
            model_path: Path to model
            model_name: Model name
            namespace: Kubernetes namespace
            storage_uri: Storage URI for model (if None, will use model_path)

        Returns:
            Success status
        """
        if self.mock_mode or not self._k8s_available:
            self.logger.info(f"[MOCK] Deployed InferenceService: {model_name} in namespace {namespace}")
            return True
            
        try:
            await self.create_namespace(namespace)
            
            template_path = os.path.join(
                os.path.dirname(__file__),
                "kserve_inference_service.yaml",
            )
            
            with open(template_path, "r") as f:
                template = f.read()
            
            if not storage_uri:
                storage_uri = f"pvc://{model_path}"
            
            template = template.replace("{model_name}", model_name)
            template = template.replace("{namespace}", namespace)
            template = template.replace("{storage_uri}", storage_uri)
            
            inference_service = yaml.safe_load(template)
            
            try:
                self.custom_api.get_namespaced_custom_object(
                    group="serving.kserve.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="inferenceservices",
                    name=model_name,
                )
                
                self.custom_api.patch_namespaced_custom_object(
                    group="serving.kserve.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="inferenceservices",
                    name=model_name,
                    body=inference_service,
                )
                
                self.logger.info(
                    f"Updated InferenceService: {model_name} in namespace {namespace}"
                )
            except ApiException as e:
                if e.status == 404:
                    self.custom_api.create_namespaced_custom_object(
                        group="serving.kserve.io",
                        version="v1beta1",
                        namespace=namespace,
                        plural="inferenceservices",
                        body=inference_service,
                    )
                    
                    self.logger.info(
                        f"Created InferenceService: {model_name} in namespace {namespace}"
                    )
                else:
                    raise
            
            return True
        except ApiException as e:
            self.logger.error(f"Error deploying InferenceService: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error deploying InferenceService: {e}")
            return False

    async def get_inference_service_status(
        self,
        model_name: str,
        namespace: str = "ml-infrastructure",
    ) -> Optional[Dict[str, Any]]:
        """
        Get KServe InferenceService status.

        Args:
            model_name: Model name
            namespace: Kubernetes namespace

        Returns:
            InferenceService status or None if failed
        """
        if self.mock_mode or not self._k8s_available:
            self.logger.info(f"[MOCK] Getting InferenceService status: {model_name} in namespace {namespace}")
            return {
                "status": "Ready",
                "url": f"http://{model_name}.{namespace}.example.com",
                "conditions": [
                    {
                        "type": "Ready",
                        "status": "True",
                        "message": "Model is ready",
                    }
                ]
            }
            
        try:
            inference_service = self.custom_api.get_namespaced_custom_object(
                group="serving.kserve.io",
                version="v1beta1",
                namespace=namespace,
                plural="inferenceservices",
                name=model_name,
            )
            
            status = inference_service.get("status", {})
            
            return status
        except ApiException as e:
            self.logger.error(f"Error getting InferenceService status: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting InferenceService status: {e}")
            return None

    async def delete_inference_service(
        self,
        model_name: str,
        namespace: str = "ml-infrastructure",
    ) -> bool:
        """
        Delete KServe InferenceService.

        Args:
            model_name: Model name
            namespace: Kubernetes namespace

        Returns:
            Success status
        """
        if self.mock_mode or not self._k8s_available:
            self.logger.info(f"[MOCK] Deleted InferenceService: {model_name} in namespace {namespace}")
            return True
            
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="serving.kserve.io",
                version="v1beta1",
                namespace=namespace,
                plural="inferenceservices",
                name=model_name,
            )
            
            self.logger.info(
                f"Deleted InferenceService: {model_name} in namespace {namespace}"
            )
            
            return True
        except ApiException as e:
            if e.status == 404:
                self.logger.warning(
                    f"InferenceService not found: {model_name} in namespace {namespace}"
                )
                return True
            
            self.logger.error(f"Error deleting InferenceService: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error deleting InferenceService: {e}")
            return False

    async def list_inference_services(
        self,
        namespace: str = "ml-infrastructure",
    ) -> List[Dict[str, Any]]:
        """
        List KServe InferenceServices.

        Args:
            namespace: Kubernetes namespace

        Returns:
            List of InferenceServices
        """
        if self.mock_mode or not self._k8s_available:
            self.logger.info(f"[MOCK] Listing InferenceServices in namespace {namespace}")
            return [
                {
                    "metadata": {
                        "name": "mock-model",
                        "namespace": namespace,
                    },
                    "spec": {
                        "predictor": {
                            "model": {
                                "modelFormat": {
                                    "name": "pytorch",
                                },
                                "storageUri": "file:///tmp/mock-model",
                            }
                        }
                    },
                    "status": {
                        "url": f"http://mock-model.{namespace}.example.com",
                        "conditions": [
                            {
                                "type": "Ready",
                                "status": "True",
                                "message": "Model is ready",
                            }
                        ]
                    }
                }
            ]
            
        try:
            inference_services = self.custom_api.list_namespaced_custom_object(
                group="serving.kserve.io",
                version="v1beta1",
                namespace=namespace,
                plural="inferenceservices",
            )
            
            return inference_services.get("items", [])
        except ApiException as e:
            self.logger.error(f"Error listing InferenceServices: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error listing InferenceServices: {e}")
            return []
