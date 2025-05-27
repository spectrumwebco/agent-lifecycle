"""
Kubernetes integration for RLLM models.

This package provides utilities for deploying RLLM models to Kubernetes
using KServe InferenceService.
"""

from .k8s_deployment import K8sDeployment

__all__ = [
    "K8sDeployment",
]
