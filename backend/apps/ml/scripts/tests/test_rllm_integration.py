"""
Test script for RLLM integration.

This script tests the RLLM integration components, including:
1. Custom reward functions
2. MLflow monitoring
3. Kubernetes deployment
"""

import os
import sys
import asyncio
import logging
import argparse
from typing import Dict, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.apps.ml.config.rllm_config import RLLMConfig
from backend.apps.ml.rewards.issue_rewards import RewardCalculator
from backend.apps.ml.rewards.code_readability_reward import CodeReadabilityReward
from backend.apps.ml.monitoring.mlflow_monitoring import MLflowMonitoring
from backend.apps.ml.integration.k8s.k8s_deployment import K8sDeployment
from backend.apps.ml.integration.ml_integration import MLIntegration


async def test_custom_reward_functions():
    """Test custom reward functions."""
    logging.info("Testing custom reward functions...")
    
    config = RLLMConfig()
    config.reward.code_quality_weight = 0.3
    config.reward.code_readability_weight = 0.3
    
    reward_calculator = RewardCalculator(config=config)
    
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
    
    rewards = reward_calculator.calculate_reward(
        response=sample_response,
        reference=sample_reference,
        metadata=sample_metadata,
    )
    
    logging.info(f"Rewards: {rewards}")
    
    code_readability_reward = CodeReadabilityReward(weight=1.0, enabled=True)
    readability_score = code_readability_reward.calculate(
        response=sample_response,
        reference=sample_reference,
        metadata=sample_metadata,
    )
    
    logging.info(f"Code readability score: {readability_score}")
    
    return rewards


async def test_mlflow_monitoring():
    """Test MLflow monitoring."""
    logging.info("Testing MLflow monitoring...")
    
    mlflow_monitoring = MLflowMonitoring(
        config=RLLMConfig(),
        experiment_name="rllm_test",
        logger=logging.getLogger("MLflowMonitoring"),
    )
    
    success = await mlflow_monitoring.initialize()
    logging.info(f"MLflow initialization: {success}")
    
    if not success:
        logging.error("Failed to initialize MLflow")
        return False
    
    run_id = await mlflow_monitoring.start_run(run_name="test_run")
    logging.info(f"MLflow run ID: {run_id}")
    
    if not run_id:
        logging.error("Failed to start MLflow run")
        return False
    
    metrics = {
        "reward": 0.8,
        "loss": 0.2,
        "accuracy": 0.9,
    }
    
    success = await mlflow_monitoring.log_metrics(metrics=metrics, run_id=run_id)
    logging.info(f"MLflow log metrics: {success}")
    
    artifact_path = "/tmp/test_artifact.txt"
    with open(artifact_path, "w") as f:
        f.write("Test artifact")
    
    success = await mlflow_monitoring.log_artifact(
        artifact_path=artifact_path, run_id=run_id
    )
    logging.info(f"MLflow log artifact: {success}")
    
    success = await mlflow_monitoring.end_run(run_id=run_id)
    logging.info(f"MLflow end run: {success}")
    
    return success


async def test_kubernetes_deployment():
    """Test Kubernetes deployment."""
    logging.info("Testing Kubernetes deployment...")
    
    try:
        k8s_deployment = K8sDeployment(logger=logging.getLogger("K8sDeployment"))
        
        namespace = "rllm-test"
        success = await k8s_deployment.create_namespace(namespace=namespace)
        logging.info(f"Namespace creation: {success}")
        
        if not success:
            logging.error(f"Failed to create namespace: {namespace}")
            return False
        
        model_name = "rllm-test-model"
        model_path = "/tmp/rllm-test-model"
        
        os.makedirs(model_path, exist_ok=True)
        
        with open(os.path.join(model_path, "model.pt"), "w") as f:
            f.write("Test model")
        
        success = await k8s_deployment.deploy_inference_service(
            model_path=model_path,
            model_name=model_name,
            namespace=namespace,
        )
        logging.info(f"InferenceService deployment: {success}")
        
        if not success:
            logging.error(f"Failed to deploy InferenceService: {model_name}")
            return False
        
        status = await k8s_deployment.get_inference_service_status(
            model_name=model_name,
            namespace=namespace,
        )
        logging.info(f"InferenceService status: {status}")
        
        inference_services = await k8s_deployment.list_inference_services(
            namespace=namespace,
        )
        logging.info(f"InferenceServices: {inference_services}")
        
        success = await k8s_deployment.delete_inference_service(
            model_name=model_name,
            namespace=namespace,
        )
        logging.info(f"InferenceService deletion: {success}")
        
        return True
    except Exception as e:
        logging.error(f"Error testing Kubernetes deployment: {e}")
        return False


async def test_ml_integration():
    """Test ML integration."""
    logging.info("Testing ML integration...")
    
    ml_integration = MLIntegration(
        config=RLLMConfig(),
        logger=logging.getLogger("MLIntegration"),
    )
    
    success = await ml_integration.setup_mlflow(experiment_name="rllm_test")
    logging.info(f"MLflow setup: {success}")
    
    if not success:
        logging.error("Failed to set up MLflow")
        return False
    
    run_id = "test_run"
    config = {
        "model_name": "rllm-test",
        "batch_size": 32,
        "learning_rate": 1e-5,
    }
    
    mlflow_run_id = await ml_integration.log_training_start(
        run_id=run_id,
        config=config,
    )
    logging.info(f"MLflow run ID: {mlflow_run_id}")
    
    if not mlflow_run_id:
        logging.error("Failed to log training start")
        return False
    
    metrics = {
        "reward": 0.8,
        "loss": 0.2,
        "accuracy": 0.9,
    }
    
    success = await ml_integration.log_training_metrics(
        run_id=mlflow_run_id,
        metrics=metrics,
        step=1,
    )
    logging.info(f"Log training metrics: {success}")
    
    artifact_path = "/tmp/test_artifact.txt"
    with open(artifact_path, "w") as f:
        f.write("Test artifact")
    
    success = await ml_integration.log_training_end(
        run_id=mlflow_run_id,
        metrics=metrics,
        artifacts=[artifact_path],
    )
    logging.info(f"Log training end: {success}")
    
    model_name = "rllm-test-model"
    model_path = "/tmp/rllm-test-model"
    
    os.makedirs(model_path, exist_ok=True)
    
    with open(os.path.join(model_path, "model.pt"), "w") as f:
        f.write("Test model")
    
    success = await ml_integration.deploy_model(
        model_path=model_path,
        model_name=model_name,
        namespace="rllm-test",
    )
    logging.info(f"Model deployment: {success}")
    
    return success


async def main():
    """Run the test script."""
    parser = argparse.ArgumentParser(description="Test RLLM integration")
    parser.add_argument(
        "--test-rewards",
        action="store_true",
        help="Test custom reward functions",
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
        "--test-integration",
        action="store_true",
        help="Test ML integration",
    )
    parser.add_argument(
        "--test-all",
        action="store_true",
        help="Test all components",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    if args.test_all or args.test_rewards:
        rewards = await test_custom_reward_functions()
        logging.info(f"Custom reward functions test result: {rewards}")
    
    if args.test_all or args.test_mlflow:
        success = await test_mlflow_monitoring()
        logging.info(f"MLflow monitoring test result: {success}")
    
    if args.test_all or args.test_kubernetes:
        success = await test_kubernetes_deployment()
        logging.info(f"Kubernetes deployment test result: {success}")
    
    if args.test_all or args.test_integration:
        success = await test_ml_integration()
        logging.info(f"ML integration test result: {success}")


if __name__ == "__main__":
    asyncio.run(main())
