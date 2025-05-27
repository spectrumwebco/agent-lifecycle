"""
Example of using the ML infrastructure API client for KubeFlow pipelines.
"""

import os
import asyncio
import logging
from typing import Dict, Any, List

from ml_infrastructure.api.client import MLInfrastructureAPIClient


async def run_kubeflow_example():
    """
    Run a KubeFlow pipeline example using the ML infrastructure API client.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("KubeFlowExample")

    api_key = os.environ.get("ML_INFRASTRUCTURE_API_KEY", "")
    base_url = os.environ.get(
        "ML_INFRASTRUCTURE_API_URL", "http://ml-infrastructure-api.example.com"
    )

    client = MLInfrastructureAPIClient(
        base_url=base_url,
        api_key=api_key,
    )

    logger.info("Creating pipeline run...")
    pipeline_run_result = await client.create_pipeline_run(
        pipeline_id="llama4-fine-tuning-pipeline",
        run_name="llama4-fine-tuning-run",
        parameters={
            "model-type": "llama4-maverick",
            "data-path": "/data/training/combined_training_data.json",
            "epochs": "3",
            "learning-rate": "5e-5",
            "batch-size": "8",
        },
    )

    run_id = pipeline_run_result["run_id"]
    logger.info(f"Created pipeline run with ID: {run_id}")

    logger.info("Monitoring pipeline run status...")
    max_attempts = 10
    attempt = 0

    while attempt < max_attempts:
        run_status = await client.get_pipeline_run(run_id)
        status = run_status["status"]

        logger.info(f"Pipeline run status: {status}")

        if status in ["Succeeded", "Failed", "Error", "Skipped", "Terminated"]:
            break

        await asyncio.sleep(60)  # Check every minute
        attempt += 1

    if status == "Succeeded":
        logger.info("Pipeline run completed successfully!")

        model_path = run_status.get("outputs", {}).get("model-path", "")

        if model_path:
            logger.info(f"Model path: {model_path}")

            logger.info("Creating KServe model...")
            kserve_result = await client.create_kserve_model(
                name="llama4-maverick-fine-tuned",
                model_uri=model_path,
                model_format="pytorch",
                resources={
                    "limits": {
                        "cpu": "4",
                        "memory": "16Gi",
                        "nvidia.com/gpu": "1",
                    },
                    "requests": {
                        "cpu": "2",
                        "memory": "8Gi",
                    },
                },
                env=[
                    {
                        "name": "MODEL_NAME",
                        "value": "llama4-maverick-fine-tuned",
                    },
                ],
            )

            logger.info(f"Created KServe model: {kserve_result['name']}")
        else:
            logger.error("Model path not found in pipeline run outputs")
    else:
        logger.error(f"Pipeline run did not complete successfully. Status: {status}")

    logger.info("KubeFlow example completed!")


if __name__ == "__main__":
    asyncio.run(run_kubeflow_example())
