"""
Kubernetes integration for ML app.

This module provides integration with the Kubernetes cluster,
allowing the ML app to deploy models, create services, and
monitor resources in the cluster.
"""

import logging
import os
import yaml
from pathlib import Path
from typing import Dict, Optional, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MLKubernetesClient")

try:
    pass
except ImportError:
    logger.warning("Pydantic package not available. Install with: pip install pydantic")

try:
    from kubernetes import client, config

    KUBERNETES_AVAILABLE = True
except ImportError:
    logger.warning(
        "Kubernetes package not available. Install with: pip install kubernetes"
    )
    KUBERNETES_AVAILABLE = False

try:
    from django.conf import settings

    DJANGO_AVAILABLE = True
except ImportError:
    logger.warning("Django settings not available")
    DJANGO_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .eventstream_integration import event_stream, Event, EventType, EventSource

    EVENTSTREAM_AVAILABLE = True
except ImportError:
    logger.warning("Eventstream integration not available")
    EVENTSTREAM_AVAILABLE = False


class KubernetesClient:
    """Client for interacting with Kubernetes."""

    def __init__(self):
        """Initialize the Kubernetes client."""
        self.logger = logging.getLogger("MLKubernetesClient")

        if not KUBERNETES_AVAILABLE:
            self.logger.warning(
                "Kubernetes package not available, running in mock mode"
            )
            self.core_v1 = None
            self.apps_v1 = None
            self.custom_objects = None
            return

        try:
            config.load_incluster_config()
        except config.ConfigException:
            try:
                config.load_kube_config()
            except Exception as e:
                self.logger.warning(f"Failed to load Kubernetes config: {e}")
                self.logger.info("Running in local-only mode")
                self.core_v1 = None
                self.apps_v1 = None
                self.custom_objects = None
                return

        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.custom_objects = client.CustomObjectsApi()

    async def create_namespace(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """Create a namespace in the cluster."""
        if not KUBERNETES_AVAILABLE or self.core_v1 is None:
            self.logger.info(f"Mock mode: Creating namespace {name}")
            return True

        try:
            body = client.V1Namespace(
                metadata=client.V1ObjectMeta(name=name, labels=labels or {})
            )
            self.core_v1.create_namespace(body)

            if EVENTSTREAM_AVAILABLE:
                event_data = {
                    "action": "create_namespace",
                    "namespace": name,
                    "labels": labels or {},
                }
                await event_stream.publish(
                    Event.new(EventType.STATE_UPDATE, EventSource.ML, event_data)
                )

            self.logger.info(f"Created namespace: {name}")
            return True
        except Exception as e:
            if hasattr(e, "status"):
                if e.status == 409:
                    self.logger.info(f"Namespace already exists: {name}")
                    return True
            self.logger.error(f"Error creating namespace: {e}")
            return False

    async def deploy_mlflow(self, namespace: str = "ml-infrastructure") -> bool:
        """Deploy MLflow to the cluster."""
        if not KUBERNETES_AVAILABLE or self.core_v1 is None:
            self.logger.info(f"Mock mode: Deploying MLflow to namespace {namespace}")
            return True

        try:
            await self.create_namespace(namespace)

            if DJANGO_AVAILABLE and hasattr(settings, "BASE_DIR"):
                k8s_dir = Path(settings.BASE_DIR).parent.parent / "k8s"
            else:
                k8s_dir = Path(BASE_DIR).parent.parent / "k8s"

            mlflow_path = k8s_dir / "mlflow" / "mlflow.yaml"

            if not mlflow_path.exists():
                self.logger.error(f"MLflow configuration not found at {mlflow_path}")
                return False

            with open(mlflow_path, "r") as f:
                mlflow_config = yaml.safe_load_all(f)
                for resource in mlflow_config:
                    resource_kind = resource.get("kind", "")
                    resource_name = resource.get("metadata", {}).get("name", "unknown")

                    if "metadata" in resource:
                        resource["metadata"]["namespace"] = namespace

                    self._apply_resource(resource, f"{resource_kind}/{resource_name}")

            if EVENTSTREAM_AVAILABLE:
                event_data = {
                    "action": "deploy_mlflow",
                    "namespace": namespace,
                    "status": "success",
                }
                await event_stream.publish(
                    Event.new(EventType.STATE_UPDATE, EventSource.ML, event_data)
                )

            self.logger.info(f"Deployed MLflow to namespace: {namespace}")
            return True
        except Exception as e:
            self.logger.error(f"Error deploying MLflow: {e}")
            return False

    async def deploy_kubeflow(self, namespace: str = "ml-infrastructure") -> bool:
        """Deploy KubeFlow to the cluster."""
        if not KUBERNETES_AVAILABLE or self.core_v1 is None:
            self.logger.info(f"Mock mode: Deploying KubeFlow to namespace {namespace}")
            return True

        try:
            await self.create_namespace(namespace)

            if DJANGO_AVAILABLE and hasattr(settings, "BASE_DIR"):
                k8s_dir = Path(settings.BASE_DIR).parent.parent / "k8s"
            else:
                k8s_dir = Path(BASE_DIR).parent.parent / "k8s"

            kubeflow_path = k8s_dir / "kubeflow" / "kubeflow.yaml"

            if not kubeflow_path.exists():
                self.logger.error(
                    f"KubeFlow configuration not found at {kubeflow_path}"
                )
                return False

            with open(kubeflow_path, "r") as f:
                kubeflow_config = yaml.safe_load_all(f)
                for resource in kubeflow_config:
                    resource_kind = resource.get("kind", "")
                    resource_name = resource.get("metadata", {}).get("name", "unknown")

                    if "metadata" in resource:
                        resource["metadata"]["namespace"] = namespace

                    self._apply_resource(resource, f"{resource_kind}/{resource_name}")

            if EVENTSTREAM_AVAILABLE:
                event_data = {
                    "action": "deploy_kubeflow",
                    "namespace": namespace,
                    "status": "success",
                }
                await event_stream.publish(
                    Event.new(EventType.STATE_UPDATE, EventSource.ML, event_data)
                )

            self.logger.info(f"Deployed KubeFlow to namespace: {namespace}")
            return True
        except Exception as e:
            self.logger.error(f"Error deploying KubeFlow: {e}")
            return False

    async def deploy_kserve(self, namespace: str = "ml-infrastructure") -> bool:
        """Deploy KServe to the cluster."""
        if not KUBERNETES_AVAILABLE or self.core_v1 is None:
            self.logger.info(f"Mock mode: Deploying KServe to namespace {namespace}")
            return True

        try:
            await self.create_namespace(namespace)

            if DJANGO_AVAILABLE and hasattr(settings, "BASE_DIR"):
                k8s_dir = Path(settings.BASE_DIR).parent.parent / "k8s"
            else:
                k8s_dir = Path(BASE_DIR).parent.parent / "k8s"

            kserve_path = k8s_dir / "kserve" / "kserve.yaml"

            if not kserve_path.exists():
                self.logger.error(f"KServe configuration not found at {kserve_path}")
                return False

            with open(kserve_path, "r") as f:
                kserve_config = yaml.safe_load_all(f)
                for resource in kserve_config:
                    resource_kind = resource.get("kind", "")
                    resource_name = resource.get("metadata", {}).get("name", "unknown")

                    if "metadata" in resource:
                        resource["metadata"]["namespace"] = namespace

                    self._apply_resource(resource, f"{resource_kind}/{resource_name}")

            if EVENTSTREAM_AVAILABLE:
                event_data = {
                    "action": "deploy_kserve",
                    "namespace": namespace,
                    "status": "success",
                }
                await event_stream.publish(
                    Event.new(EventType.STATE_UPDATE, EventSource.ML, event_data)
                )

            self.logger.info(f"Deployed KServe to namespace: {namespace}")
            return True
        except Exception as e:
            self.logger.error(f"Error deploying KServe: {e}")
            return False

    def _apply_resource(self, resource: Dict[str, Any], resource_id: str) -> None:
        """Apply a Kubernetes resource."""
        if not KUBERNETES_AVAILABLE or self.core_v1 is None:
            self.logger.info(f"Mock mode: Applying resource {resource_id}")
            return

        try:
            group = ""
            version = "v1"
            plural = ""
            kind = resource.get("kind", "").lower()
            api_version = resource.get("apiVersion", "v1")
            name = resource.get("metadata", {}).get("name", "")
            namespace = resource.get("metadata", {}).get("namespace", "default")

            if api_version != "v1":
                group_version = api_version.split("/")
                if len(group_version) == 2:
                    group, version = group_version
                else:
                    version = group_version[0]

            kind_to_plural = {
                "deployment": "deployments",
                "service": "services",
                "configmap": "configmaps",
                "secret": "secrets",
                "persistentvolumeclaim": "persistentvolumeclaims",
                "job": "jobs",
                "cronjob": "cronjobs",
                "statefulset": "statefulsets",
            }

            plural = kind_to_plural.get(kind, f"{kind}s")

            try:
                if group:
                    self.custom_objects.get_namespaced_custom_object(
                        group, version, namespace, plural, name
                    )
                    self.custom_objects.patch_namespaced_custom_object(
                        group, version, namespace, plural, name, resource
                    )
                    self.logger.info(f"Updated resource: {resource_id}")
                else:
                    if kind == "service":
                        self.core_v1.patch_namespaced_service(name, namespace, resource)
                    elif kind == "configmap":
                        self.core_v1.patch_namespaced_config_map(
                            name, namespace, resource
                        )

                    self.logger.info(f"Updated resource: {resource_id}")
            except Exception as e:
                if hasattr(e, "status"):
                    if e.status == 404:
                        if group:
                            self.custom_objects.create_namespaced_custom_object(
                                group, version, namespace, plural, resource
                            )
                        else:
                            if kind == "service":
                                self.core_v1.create_namespaced_service(
                                    namespace, resource
                                )
                            elif kind == "configmap":
                                self.core_v1.create_namespaced_config_map(
                                    namespace, resource
                                )

                        self.logger.info(f"Created resource: {resource_id}")
                    else:
                        raise
                else:
                    raise
        except Exception as e:
            self.logger.error(f"Error applying resource {resource_id}: {e}")


k8s_client = KubernetesClient()
