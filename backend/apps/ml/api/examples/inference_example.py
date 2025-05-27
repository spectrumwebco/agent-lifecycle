"""
Example of using the ML infrastructure API client for inference.
"""

import os
import asyncio
import logging
from typing import Dict, Any, List

from ml_infrastructure.api.client import MLInfrastructureAPIClient


async def run_inference_example():
    """
    Run an inference example using the ML infrastructure API client.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("InferenceExample")

    api_key = os.environ.get("ML_INFRASTRUCTURE_API_KEY", "")
    base_url = os.environ.get(
        "ML_INFRASTRUCTURE_API_URL", "http://ml-infrastructure-api.example.com"
    )

    client = MLInfrastructureAPIClient(
        base_url=base_url,
        api_key=api_key,
    )

    logger.info("Listing available models...")
    models = await client.get_models(model_type="llama4-maverick")

    if not models:
        logger.error("No models found")
        return

    model_id = models[0]["model_id"]
    logger.info(f"Found model with ID: {model_id}")

    logger.info("Listing inference services...")
    services = await client.list_inference_services(model_id=model_id)

    service_id = None
    if services:
        service_id = services[0]["service_id"]
        logger.info(f"Found existing service with ID: {service_id}")
    else:
        logger.info("Creating inference service...")
        service_result = await client.create_inference_service(
            model_id=model_id,
            service_name="llama4-maverick-inference",
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

    logger.info("Making predictions...")

    test_inputs = [
        "Repository: kubernetes/kubernetes\nTopics: kubernetes, k8s, container, orchestration\nIssue Title: Fix pod scheduling issue in multi-zone clusters\nIssue Description:\nWhen deploying pods across multiple zones, the scheduler is not respecting zone anti-affinity rules.\n",
        "Repository: terraform-aws-modules/terraform-aws-vpc\nTopics: terraform, aws, vpc, infrastructure\nIssue Title: Support for IPv6-only subnets\nIssue Description:\nNeed to add support for IPv6-only subnets in the VPC module as AWS now supports this configuration.\n",
        "Repository: fluxcd/flux2\nTopics: gitops, kubernetes, cd, automation\nIssue Title: Helm release not respecting timeout value\nIssue Description:\nWhen specifying a timeout value for Helm releases, the controller seems to ignore it and uses the default timeout instead.\n",
    ]

    for i, test_input in enumerate(test_inputs):
        logger.info(f"Making prediction {i+1}/{len(test_inputs)}...")

        prediction_result = await client.predict(
            service_id=service_id,
            input_text=test_input,
            parameters={
                "max_tokens": 1024,
                "temperature": 0.7,
                "top_p": 0.9,
            },
        )

        logger.info(f"Input: {test_input[:100]}...")
        logger.info(f"Output: {prediction_result['output']}")
        logger.info("---")

    logger.info("Inference example completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_inference_example())
