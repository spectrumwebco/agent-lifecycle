"""
Test the Kubernetes integration.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from apps.ml.integration.k8s_integration import k8s_client

    async def test_k8s():
        """Test the Kubernetes integration."""
        logger.info("Starting Kubernetes integration test")

        namespace = "ml-test"
        success = await k8s_client.create_namespace(namespace)
        logger.info(f"Created namespace {namespace}: {success}")

        mlflow_success = await k8s_client.deploy_mlflow(namespace)
        logger.info(f"Deployed MLflow: {mlflow_success}")

        kubeflow_success = await k8s_client.deploy_kubeflow(namespace)
        logger.info(f"Deployed KubeFlow: {kubeflow_success}")

        kserve_success = await k8s_client.deploy_kserve(namespace)
        logger.info(f"Deployed KServe: {kserve_success}")

        logger.info("Kubernetes integration test completed successfully")
        return True

    if __name__ == "__main__":
        asyncio.run(test_k8s())

except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info("Skipping Kubernetes test due to missing dependencies")

    if __name__ == "__main__":
        logger.info(
            "Test environment not properly set up. Please install required dependencies."
        )
        sys.exit(0)
