"""
Example of using the ML infrastructure API client for fine-tuning.
"""

import os
import asyncio
import logging
from typing import Dict, Any

from ml_infrastructure.api.client import MLInfrastructureAPIClient


async def run_fine_tuning_example():
    """
    Run a fine-tuning example using the ML infrastructure API client.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("FineTuningExample")

    api_key = os.environ.get("ML_INFRASTRUCTURE_API_KEY", "")
    base_url = os.environ.get(
        "ML_INFRASTRUCTURE_API_URL", "http://ml-infrastructure-api.example.com"
    )

    client = MLInfrastructureAPIClient(
        base_url=base_url,
        api_key=api_key,
    )

    logger.info("Uploading training data...")
    upload_result = await client.upload_training_data(
        file_path="./data/training_data.json",
        dataset_name="llama4-fine-tuning-dataset",
    )

    dataset_id = upload_result["dataset_id"]
    logger.info(f"Uploaded training data with dataset ID: {dataset_id}")

    logger.info("Creating experiment...")
    experiment_result = await client.create_experiment(
        name="llama4-fine-tuning-experiment",
        tags={
            "model_type": "llama4-maverick",
            "task": "fine-tuning",
            "domain": "software-engineering",
        },
    )

    experiment_id = experiment_result["experiment_id"]
    logger.info(f"Created experiment with ID: {experiment_id}")

    logger.info("Creating fine-tuning job...")
    job_result = await client.create_fine_tuning_job(
        model_type="llama4-maverick",
        training_data_path=f"s3://datasets/{dataset_id}/training_data.json",
        hyperparameters={
            "learning_rate": 5e-5,
            "batch_size": 8,
            "epochs": 3,
            "gradient_accumulation_steps": 4,
        },
    )

    job_id = job_result["job_id"]
    logger.info(f"Created fine-tuning job with ID: {job_id}")

    logger.info("Monitoring job status...")
    max_attempts = 10
    attempt = 0

    while attempt < max_attempts:
        job_status = await client.get_fine_tuning_job(job_id)
        status = job_status["status"]

        logger.info(f"Job status: {status}")

        if status in ["completed", "failed", "cancelled"]:
            break

        await asyncio.sleep(60)  # Check every minute
        attempt += 1

    if status == "completed":
        logger.info("Fine-tuning job completed successfully!")

        logger.info("Creating inference service...")
        service_result = await client.create_inference_service(
            model_id=job_status["model_id"],
            service_name="llama4-maverick-fine-tuned",
            replicas=1,
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
        )

        service_id = service_result["service_id"]
        logger.info(f"Created inference service with ID: {service_id}")

        logger.info("Testing the model...")
        test_input = "Repository: kubernetes/kubernetes\nTopics: kubernetes, k8s, container, orchestration\nIssue Title: Fix pod scheduling issue in multi-zone clusters\nIssue Description:\nWhen deploying pods across multiple zones, the scheduler is not respecting zone anti-affinity rules.\n"

        prediction_result = await client.predict(
            service_id=service_id,
            input_text=test_input,
            parameters={
                "max_tokens": 1024,
                "temperature": 0.7,
                "top_p": 0.9,
            },
        )

        logger.info(f"Prediction result: {prediction_result['output']}")
    else:
        logger.error(f"Fine-tuning job did not complete successfully. Status: {status}")


if __name__ == "__main__":
    asyncio.run(run_fine_tuning_example())
