"""
Integration with ML infrastructure.

This module provides integration between the RLLM framework and the
existing ML infrastructure, including MLflow, KubeFlow, and KServe.
"""

import os
import logging
from typing import Dict, List, Any, Optional
import json

from ...ml.integration.eventstream_integration import (
    event_stream,
    Event,
    EventType,
    EventSource,
)
from ...ml.integration.k8s_integration import k8s_client
from ..config.rllm_config import RLLMConfig


class MLIntegration:
    """Integration with ML infrastructure."""

    def __init__(
        self,
        config: Optional[RLLMConfig] = None,
        logger: Optional[logging.Logger] = None,
        experiment_name: str = "rllm",
    ):
        """
        Initialize ML integration.

        Args:
            config: RLLM configuration
            logger: Logger
            experiment_name: MLflow experiment name
        """
        self.config = config or RLLMConfig()
        self.logger = logger or logging.getLogger("MLIntegration")

        self.event_stream = event_stream
        self.k8s_client = k8s_client
        
        # Initialize MLflow monitoring
        self.experiment_name = experiment_name
        self.mlflow_monitoring = None
        
        self.mlflow_setup_done = False
        
        self.logger.info("Initialized ML integration")

    async def setup_mlflow(self, experiment_name: str = "rllm") -> bool:
        """
        Set up MLflow for experiment tracking.

        Args:
            experiment_name: MLflow experiment name

        Returns:
            Success status
        """
        try:
            from ..monitoring.mlflow_monitoring import MLflowMonitoring
            
            tracking_uri = None
            if self.event_stream:
                tracking_uri = await self.event_stream.get_app_context(
                    "mlflow_tracking_uri"
                )
            
            self.mlflow_monitoring = MLflowMonitoring(
                config=self.config,
                experiment_name=experiment_name,
                tracking_uri=tracking_uri,
                logger=self.logger,
            )
            
            success = await self.mlflow_monitoring.initialize()
            
            if success:
                self.logger.info(f"Set up MLflow with experiment: {experiment_name}")
            else:
                self.logger.error("Failed to set up MLflow")
            
            return success
        except ImportError:
            self.logger.warning("MLflow not available, skipping setup")
            return False
        except Exception as e:
            self.logger.error(f"Error setting up MLflow: {e}")
            return False

    async def log_training_start(
        self, run_id: str, config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Log training start to MLflow.

        Args:
            run_id: Training run ID
            config: Training configuration

        Returns:
            MLflow run ID or None if failed
        """
        if not self.mlflow_monitoring:
            success = await self.setup_mlflow()
            if not success:
                self.logger.warning("Failed to set up MLflow, skipping logging")
                return None
        
        try:
            tags = {
                "run_id": run_id,
                "source": "rllm_training",
            }
            
            mlflow_run_id = await self.mlflow_monitoring.start_run(
                run_name=f"rllm_training_{run_id}",
                tags=tags,
            )
            
            if not mlflow_run_id:
                self.logger.error("Failed to start MLflow run")
                return None
            
            if self.event_stream:
                event_data = {
                    "action": "rllm_training_start",
                    "run_id": run_id,
                    "mlflow_run_id": mlflow_run_id,
                    "config": config,
                }

                await self.event_stream.publish(
                    Event.new(
                        EventType.STATE_UPDATE, EventSource.ML, event_data
                    )
                )

            self.logger.info(
                f"Logged training start to MLflow: {mlflow_run_id}"
            )

            return mlflow_run_id
        except Exception as e:
            self.logger.error(f"Error logging training start to MLflow: {e}")
            return None

    async def log_training_metrics(
        self,
        run_id: str,
        metrics: Dict[str, float],
        step: Optional[int] = None,
    ) -> bool:
        """
        Log training metrics to MLflow.

        Args:
            run_id: MLflow run ID
            metrics: Training metrics
            step: Training step

        Returns:
            Success status
        """
        if not self.mlflow_monitoring:
            success = await self.setup_mlflow()
            if not success:
                self.logger.warning("Failed to set up MLflow, skipping logging")
                return False
        
        try:
            success = await self.mlflow_monitoring.log_metrics(
                metrics=metrics,
                step=step,
                run_id=run_id,
            )
            
            if not success:
                self.logger.error("Failed to log metrics to MLflow")
                return False
            
            if self.event_stream:
                event_data = {
                    "action": "rllm_training_metrics",
                    "run_id": run_id,
                    "metrics": metrics,
                    "step": step,
                }

                await self.event_stream.publish(
                    Event.new(
                        EventType.STATE_UPDATE, EventSource.ML, event_data
                    )
                )

            self.logger.info(
                f"Logged training metrics to MLflow: {run_id}"
            )

            return True
        except Exception as e:
            self.logger.error(f"Error logging training metrics to MLflow: {e}")
            return False

    async def log_training_end(
        self, run_id: str, metrics: Dict[str, float], artifacts: List[str]
    ) -> bool:
        """
        Log training end to MLflow.

        Args:
            run_id: MLflow run ID
            metrics: Final training metrics
            artifacts: Paths to artifacts to log

        Returns:
            Success status
        """
        if not self.mlflow_monitoring:
            success = await self.setup_mlflow()
            if not success:
                self.logger.warning("Failed to set up MLflow, skipping logging")
                return False
        
        try:
            success = await self.mlflow_monitoring.log_metrics(
                metrics=metrics,
                run_id=run_id,
            )
            
            if not success:
                self.logger.error("Failed to log metrics to MLflow")
                return False
            
            for artifact_path in artifacts:
                if os.path.exists(artifact_path):
                    success = await self.mlflow_monitoring.log_artifact(
                        artifact_path=artifact_path,
                        run_id=run_id,
                    )
                    
                    if not success:
                        self.logger.warning(
                            f"Failed to log artifact: {artifact_path}"
                        )
                else:
                    self.logger.warning(
                        f"Artifact not found: {artifact_path}"
                    )
            
            success = await self.mlflow_monitoring.end_run(run_id=run_id)
            
            if not success:
                self.logger.error("Failed to end MLflow run")
                return False
            
            if self.event_stream:
                event_data = {
                    "action": "rllm_training_end",
                    "run_id": run_id,
                    "metrics": metrics,
                    "artifacts": artifacts,
                }

                await self.event_stream.publish(
                    Event.new(
                        EventType.STATE_UPDATE, EventSource.ML, event_data
                    )
                )

            self.logger.info(f"Logged training end to MLflow: {run_id}")

            return True
        except Exception as e:
            self.logger.error(f"Error logging training end to MLflow: {e}")
            return False

    async def deploy_model(
        self,
        model_path: str,
        model_name: str,
        namespace: str = "ml-infrastructure",
        storage_uri: Optional[str] = None,
    ) -> bool:
        """
        Deploy model to KServe.

        Args:
            model_path: Path to model
            model_name: Model name
            namespace: Kubernetes namespace
            storage_uri: Storage URI for model (if None, will use model_path)

        Returns:
            Success status
        """
        if not self.k8s_client:
            self.logger.warning(
                "Kubernetes client not available, skipping model deployment"
            )
            return False

        try:
            from .k8s.k8s_deployment import K8sDeployment
            
            k8s_deployment = K8sDeployment(logger=self.logger)
            
            await k8s_deployment.create_namespace(namespace)
            
            # Deploy model using KServe InferenceService
            success = await k8s_deployment.deploy_inference_service(
                model_path=model_path,
                model_name=model_name,
                namespace=namespace,
                storage_uri=storage_uri,
            )

            if success:
                self.logger.info(
                    f"Model deployed successfully: {model_name} in namespace {namespace}"
                )

                status = await k8s_deployment.get_inference_service_status(
                    model_name=model_name,
                    namespace=namespace,
                )
                
                if status and "url" in status:
                    model_url = status["url"]
                    self.logger.info(f"Model URL: {model_url}")
                
                if self.event_stream:
                    event_data = {
                        "action": "rllm_model_deployed",
                        "model_name": model_name,
                        "model_path": model_path,
                        "namespace": namespace,
                        "status": status,
                    }

                    await self.event_stream.publish(
                        Event.new(
                            EventType.STATE_UPDATE, EventSource.ML, event_data
                        )
                    )
            else:
                self.logger.error(
                    f"Failed to deploy model: {model_name} in namespace {namespace}"
                )

            return success
        except Exception as e:
            self.logger.error(f"Error deploying model: {e}")
            return False
