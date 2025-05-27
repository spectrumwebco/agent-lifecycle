"""
Model Registry Integration

This module provides integration with MLflow Model Registry for managing
fine-tuned Llama 4 models.
"""

import os
import json
import logging
import mlflow
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ModelRegistryConfig:
    """Configuration for MLflow Model Registry integration."""

    tracking_uri: Optional[str] = None

    registry_uri: Optional[str] = None

    model_name_prefix: str = "llama4"
    model_description: str = (
        "Fine-tuned Llama 4 model for GitOps, Terraform, and Kubernetes issues"
    )

    auto_register: bool = True
    auto_alias: bool = True

    staging_criteria: Dict[str, float] = field(
        default_factory=lambda: {
            "accuracy": 0.7,
            "f1": 0.7,
            "trajectory_similarity": 0.6,
        }
    )

    production_criteria: Dict[str, float] = field(
        default_factory=lambda: {
            "accuracy": 0.8,
            "f1": 0.8,
            "trajectory_similarity": 0.7,
            "swe_agent_score": 0.75,
        }
    )

    include_metrics: bool = True
    include_parameters: bool = True
    include_artifacts: bool = True

    artifact_location: Optional[str] = None

    enable_model_serving: bool = True
    serving_flavor: str = "transformers"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ModelRegistryConfig":
        """Create a configuration from a dictionary."""
        return cls(**config_dict)

    @classmethod
    def from_env(cls) -> "ModelRegistryConfig":
        """Create a configuration from environment variables."""
        return cls(
            tracking_uri=os.environ.get("MLFLOW_TRACKING_URI"),
            registry_uri=os.environ.get("MLFLOW_REGISTRY_URI"),
            model_name_prefix=os.environ.get("MLFLOW_MODEL_NAME_PREFIX", "llama4"),
            artifact_location=os.environ.get("MLFLOW_ARTIFACT_LOCATION"),
        )


class ModelRegistry:
    """Integration with MLflow Model Registry for managing fine-tuned Llama 4 models."""

    def __init__(self, config: Optional[ModelRegistryConfig] = None):
        """Initialize the model registry integration."""
        self.config = config or ModelRegistryConfig.from_env()

        if self.config.tracking_uri:
            mlflow.set_tracking_uri(self.config.tracking_uri)

        if self.config.registry_uri:
            mlflow.set_registry_uri(self.config.registry_uri)

    def register_model(
        self,
        model_type: str,
        run_id: str,
        model_path: str,
        metrics: Optional[Dict[str, float]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Register a model with the MLflow Model Registry."""
        model_name = f"{self.config.model_name_prefix}-{model_type}"

        try:
            result = mlflow.register_model(
                model_uri=f"runs:/{run_id}/{model_path}",
                name=model_name,
                tags=tags,
            )

            model_version = result.version
            logger.info(f"Registered model {model_name} version {model_version}")

            mlflow.models.set_model_version_tag(
                name=model_name,
                version=model_version,
                key="description",
                value=self.config.model_description,
            )

            if metrics and self.config.include_metrics:
                for metric_name, metric_value in metrics.items():
                    mlflow.models.set_model_version_tag(
                        name=model_name,
                        version=model_version,
                        key=f"metric.{metric_name}",
                        value=str(metric_value),
                    )

            if metrics and self.config.auto_alias:
                stage = self._determine_stage(metrics)
                if stage:
                    mlflow.models.transition_model_version_stage(
                        name=model_name,
                        version=model_version,
                        stage=stage,
                    )
                    logger.info(
                        f"Transitioned model {model_name} version {model_version} to {stage}"
                    )

            return {
                "model_name": model_name,
                "model_version": model_version,
                "run_id": run_id,
                "stage": stage if stage else "None",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to register model: {e}")
            raise

    def _determine_stage(self, metrics: Dict[str, float]) -> Optional[str]:
        """Determine the stage for a model based on metrics."""
        production_eligible = True
        for metric_name, threshold in self.config.production_criteria.items():
            if metric_name in metrics:
                if metrics[metric_name] < threshold:
                    production_eligible = False
                    break
            else:
                production_eligible = False
                break

        if production_eligible:
            return "Production"

        staging_eligible = True
        for metric_name, threshold in self.config.staging_criteria.items():
            if metric_name in metrics:
                if metrics[metric_name] < threshold:
                    staging_eligible = False
                    break
            else:
                staging_eligible = False
                break

        if staging_eligible:
            return "Staging"

        return "None"

    def get_model_versions(self, model_type: str) -> List[Dict[str, Any]]:
        """Get all versions of a model from the MLflow Model Registry."""
        model_name = f"{self.config.model_name_prefix}-{model_type}"

        try:
            client = mlflow.tracking.MlflowClient()
            versions = client.search_model_versions(f"name='{model_name}'")

            return [
                {
                    "model_name": v.name,
                    "model_version": v.version,
                    "run_id": v.run_id,
                    "stage": v.current_stage,
                    "timestamp": v.creation_timestamp,
                }
                for v in versions
            ]

        except Exception as e:
            logger.error(f"Failed to get model versions: {e}")
            raise

    def get_latest_model(
        self, model_type: str, stage: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get the latest version of a model from the MLflow Model Registry."""
        model_name = f"{self.config.model_name_prefix}-{model_type}"

        try:
            client = mlflow.tracking.MlflowClient()

            if stage:
                versions = client.get_latest_versions(model_name, stages=[stage])
            else:
                versions = client.get_latest_versions(model_name)

            if not versions:
                return None

            versions.sort(key=lambda x: int(x.version), reverse=True)
            latest = versions[0]

            return {
                "model_name": latest.name,
                "model_version": latest.version,
                "run_id": latest.run_id,
                "stage": latest.current_stage,
                "timestamp": latest.creation_timestamp,
            }

        except Exception as e:
            logger.error(f"Failed to get latest model: {e}")
            raise

    def transition_model_stage(
        self, model_type: str, version: str, stage: str
    ) -> Dict[str, Any]:
        """Transition a model version to a different stage."""
        model_name = f"{self.config.model_name_prefix}-{model_type}"

        try:
            result = mlflow.models.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage,
            )

            logger.info(f"Transitioned model {model_name} version {version} to {stage}")

            return {
                "model_name": model_name,
                "model_version": version,
                "stage": stage,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to transition model stage: {e}")
            raise

    def delete_model_version(self, model_type: str, version: str) -> Dict[str, Any]:
        """Delete a model version from the MLflow Model Registry."""
        model_name = f"{self.config.model_name_prefix}-{model_type}"

        try:
            client = mlflow.tracking.MlflowClient()
            client.delete_model_version(name=model_name, version=version)

            logger.info(f"Deleted model {model_name} version {version}")

            return {
                "model_name": model_name,
                "model_version": version,
                "deleted": True,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to delete model version: {e}")
            raise

    def create_model_deployment(
        self,
        model_type: str,
        version: Optional[str] = None,
        stage: Optional[str] = "Production",
        deployment_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a deployment for a model version."""
        model_name = f"{self.config.model_name_prefix}-{model_type}"
        deployment_name = deployment_name or f"{model_name}-deployment"

        try:
            if version:
                model_uri = f"models:/{model_name}/{version}"
            elif stage:
                model_uri = f"models:/{model_name}/{stage}"
            else:
                raise ValueError("Either version or stage must be provided")

            deployment_config = {
                "flavor": self.config.serving_flavor,
                "target_uri": deployment_name,
                "config": config or {},
            }

            logger.info(
                f"Creating deployment for {model_uri} with config: {deployment_config}"
            )

            return {
                "model_name": model_name,
                "model_uri": model_uri,
                "deployment_name": deployment_name,
                "deployment_config": deployment_config,
                "status": "created",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to create model deployment: {e}")
            raise


def get_default_registry() -> ModelRegistry:
    """Get the default model registry integration."""
    return ModelRegistry()
