"""
Simple test script for RLLM integration components.

This script tests individual components without relying on the full import chain.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test_simple")


async def test_code_readability_reward():
    """Test the code readability reward function."""
    from backend.apps.ml.rewards.code_readability_reward import CodeReadabilityReward
    
    logger.info("Testing code readability reward...")
    
    reward = CodeReadabilityReward(weight=1.0, enabled=True)
    
    sample_response = """
    Here's a solution to the issue:
    
    ```
    def calculate_total(items):
        total = 0
        for item in items:
            total += item.price
        return total
    ```
    
    This function iterates through each item and adds its price to the total.
    """
    
    sample_reference = """
    The solution should calculate the total price of all items.
    """
    
    sample_metadata = {
        "issue_id": "123",
        "issue_title": "Calculate total price",
    }
    
    score = reward.calculate(
        response=sample_response,
        reference=sample_reference,
        metadata=sample_metadata,
    )
    
    logger.info(f"Code readability score: {score}")
    
    return score


async def test_mlflow_monitoring():
    """Test MLflow monitoring."""
    from backend.apps.ml.monitoring.mlflow_monitoring import MLflowMonitoring
    
    logger.info("Testing MLflow monitoring...")
    
    mlflow_monitoring = MLflowMonitoring(
        experiment_name="test_experiment",
        logger=logger,
    )
    
    success = await mlflow_monitoring.initialize()
    logger.info(f"MLflow initialization: {success}")
    
    if not success:
        logger.error("Failed to initialize MLflow")
        return False
    
    run_id = await mlflow_monitoring.start_run(run_name="test_run")
    logger.info(f"MLflow run ID: {run_id}")
    
    if not run_id:
        logger.error("Failed to start MLflow run")
        return False
    
    metrics = {
        "reward": 0.8,
        "loss": 0.2,
        "accuracy": 0.9,
    }
    
    success = await mlflow_monitoring.log_metrics(metrics=metrics, run_id=run_id)
    logger.info(f"MLflow log metrics: {success}")
    
    success = await mlflow_monitoring.end_run(run_id=run_id)
    logger.info(f"MLflow end run: {success}")
    
    return success


async def test_k8s_deployment():
    """Test Kubernetes deployment utilities."""
    from backend.apps.ml.integration.k8s.k8s_deployment import K8sDeployment
    
    logger.info("Testing Kubernetes deployment utilities...")
    
    k8s_deployment = K8sDeployment(logger=logger)
    
    namespace = "test-namespace"
    success = await k8s_deployment.create_namespace(namespace=namespace)
    logger.info(f"Namespace creation: {success}")
    
    return success


async def main():
    """Run the test script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple test for RLLM integration components")
    parser.add_argument(
        "--test-rewards",
        action="store_true",
        help="Test code readability reward",
    )
    parser.add_argument(
        "--test-mlflow",
        action="store_true",
        help="Test MLflow monitoring",
    )
    parser.add_argument(
        "--test-kubernetes",
        action="store_true",
        help="Test Kubernetes deployment",
    )
    parser.add_argument(
        "--test-all",
        action="store_true",
        help="Test all components",
    )
    
    args = parser.parse_args()
    
    if args.test_all or args.test_rewards:
        score = await test_code_readability_reward()
        logger.info(f"Code readability test result: {score}")
    
    if args.test_all or args.test_mlflow:
        success = await test_mlflow_monitoring()
        logger.info(f"MLflow monitoring test result: {success}")
    
    if args.test_all or args.test_kubernetes:
        success = await test_k8s_deployment()
        logger.info(f"Kubernetes deployment test result: {success}")


if __name__ == "__main__":
    asyncio.run(main())
