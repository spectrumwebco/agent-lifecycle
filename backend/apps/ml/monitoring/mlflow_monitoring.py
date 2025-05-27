"""
MLflow monitoring for RLLM training.

This module provides MLflow integration for monitoring RLLM training
progress, logging metrics, and storing models and artifacts.
"""

import os
import logging
import mlflow
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from ..config.rllm_config import RLLMConfig


class MLflowMonitoring:
    """MLflow monitoring for RLLM training."""

    def __init__(
        self,
        config: Optional[RLLMConfig] = None,
        experiment_name: Optional[str] = None,
        tracking_uri: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize MLflow monitoring.

        Args:
            config: RLLM configuration
            experiment_name: MLflow experiment name
            tracking_uri: MLflow tracking URI
            logger: Logger
        """
        self.config = config or RLLMConfig()
        self.experiment_name = experiment_name or "rllm-training"
        self.tracking_uri = tracking_uri
        self.logger = logger or logging.getLogger("MLflowMonitoring")
        self.active_run_id = None
        self.initialized = False

    async def initialize(self) -> bool:
        """
        Initialize MLflow.

        Returns:
            Whether initialization was successful
        """
        try:
            if self.tracking_uri:
                mlflow.set_tracking_uri(self.tracking_uri)
                self.logger.info(f"Set MLflow tracking URI to {self.tracking_uri}")
            
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(self.experiment_name)
                self.logger.info(f"Created MLflow experiment: {self.experiment_name}")
            else:
                experiment_id = experiment.experiment_id
                self.logger.info(f"Using existing MLflow experiment: {self.experiment_name}")
            
            mlflow.set_experiment(self.experiment_name)
            self.initialized = True
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize MLflow: {e}")
            return False

    async def start_run(
        self,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Start MLflow run.

        Args:
            run_name: Run name
            tags: Run tags

        Returns:
            Run ID or None if failed
        """
        if not self.initialized:
            success = await self.initialize()
            if not success:
                return None

        try:
            if not run_name:
                timestamp = int(datetime.now().timestamp())
                run_name = f"rllm-run-{timestamp}"
            
            tags = tags or {}
            tags.update({
                "model_id": self.config.model.model_id,
                "max_seq_length": str(self.config.model.max_seq_length),
                "use_lora": str(self.config.model.use_lora),
                "learning_rate": str(self.config.training.learning_rate),
                "num_train_epochs": str(self.config.training.num_train_epochs),
                "batch_size": str(self.config.training.per_device_train_batch_size),
            })
            
            run = mlflow.start_run(run_name=run_name, tags=tags)
            self.active_run_id = run.info.run_id
            
            self._log_config_params()
            
            self.logger.info(f"Started MLflow run: {run_name} (ID: {self.active_run_id})")
            
            return self.active_run_id
        except Exception as e:
            self.logger.error(f"Failed to start MLflow run: {e}")
            return None

    def _log_config_params(self) -> None:
        """Log configuration parameters to MLflow."""
        try:
            for key, value in self.config.model.model_dump().items():
                if isinstance(value, (str, int, float, bool)):
                    mlflow.log_param(f"model.{key}", value)
            
            for key, value in self.config.training.model_dump().items():
                if isinstance(value, (str, int, float, bool)):
                    mlflow.log_param(f"training.{key}", value)
            
            for key, value in self.config.reward.model_dump().items():
                if isinstance(value, (str, int, float, bool)):
                    mlflow.log_param(f"reward.{key}", value)
            
            for key, value in self.config.distributed.model_dump().items():
                if isinstance(value, (str, int, float, bool)):
                    mlflow.log_param(f"distributed.{key}", value)
            
            self.logger.debug("Logged configuration parameters to MLflow")
        except Exception as e:
            self.logger.error(f"Failed to log configuration parameters: {e}")

    async def log_metrics(
        self,
        metrics: Dict[str, float],
        step: Optional[int] = None,
        run_id: Optional[str] = None,
    ) -> bool:
        """
        Log metrics to MLflow.

        Args:
            metrics: Metrics to log
            step: Step number
            run_id: Run ID (if None, uses active run)

        Returns:
            Whether logging was successful
        """
        run_id = run_id or self.active_run_id
        if not run_id:
            self.logger.warning("No active MLflow run")
            return False

        try:
            mlflow.log_metrics(metrics, step=step)
            self.logger.debug(f"Logged metrics to MLflow: {metrics}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to log metrics: {e}")
            return False

    async def log_artifact(
        self, 
        artifact_path: str,
        run_id: Optional[str] = None
    ) -> bool:
        """
        Log artifact to MLflow.

        Args:
            artifact_path: Local path to artifact
            run_id: Run ID (if None, uses active run)

        Returns:
            Whether logging was successful
        """
        run_id = run_id or self.active_run_id
        if not run_id:
            self.logger.warning("No active MLflow run")
            return False

        try:
            mlflow.log_artifact(artifact_path)
            self.logger.info(f"Logged artifact to MLflow: {artifact_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to log artifact: {e}")
            return False

    async def log_model(
        self,
        model_path: str,
        model_name: str = "rllm-model",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Log model to MLflow.

        Args:
            model_path: Path to model
            model_name: Model name
            metadata: Model metadata

        Returns:
            Whether logging was successful
        """
        if not self.active_run_id:
            self.logger.warning("No active MLflow run")
            return False

        try:
            mlflow.log_artifact(model_path, artifact_path=model_name)
            
            if metadata:
                metadata_path = os.path.join(os.path.dirname(model_path), "metadata.json")
                with open(metadata_path, "w") as f:
                    import json
                    json.dump(metadata, f, indent=2)
                
                mlflow.log_artifact(metadata_path, artifact_path=model_name)
            
            self.logger.info(f"Logged model to MLflow: {model_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to log model: {e}")
            return False

    async def end_run(
        self,
        status: str = "FINISHED",
        run_id: Optional[str] = None,
    ) -> bool:
        """
        End MLflow run.

        Args:
            status: Run status
            run_id: Run ID (if None, uses active run)

        Returns:
            Whether ending the run was successful
        """
        run_id = run_id or self.active_run_id
        if not run_id:
            self.logger.warning("No active MLflow run to end")
            return False

        try:
            mlflow.end_run(status=status)
            self.logger.info(f"Ended MLflow run: {run_id}")
            self.active_run_id = None if run_id == self.active_run_id else self.active_run_id
            return True
        except Exception as e:
            self.logger.error(f"Failed to end MLflow run: {e}")
            return False

    async def get_run_info(self, run_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get run information.

        Args:
            run_id: Run ID (if None, uses active run)

        Returns:
            Run information or None if failed
        """
        run_id = run_id or self.active_run_id
        if not run_id:
            self.logger.warning("No run ID provided")
            return None

        try:
            client = mlflow.tracking.MlflowClient()
            run = client.get_run(run_id)
            
            run_info = {
                "run_id": run.info.run_id,
                "experiment_id": run.info.experiment_id,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
                "artifact_uri": run.info.artifact_uri,
                "metrics": run.data.metrics,
                "params": run.data.params,
                "tags": run.data.tags,
            }
            
            return run_info
        except Exception as e:
            self.logger.error(f"Failed to get run info: {e}")
            return None

    async def get_best_run(
        self,
        metric_name: str,
        experiment_name: Optional[str] = None,
        ascending: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Get best run based on metric.

        Args:
            metric_name: Metric name
            experiment_name: Experiment name (if None, uses current experiment)
            ascending: Whether to sort in ascending order

        Returns:
            Best run information or None if failed
        """
        experiment_name = experiment_name or self.experiment_name

        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                self.logger.warning(f"Experiment not found: {experiment_name}")
                return None
            
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=[f"metrics.{metric_name} {'ASC' if ascending else 'DESC'}"],
                max_results=1,
            )
            
            if len(runs) == 0:
                self.logger.warning(f"No runs found for experiment: {experiment_name}")
                return None
            
            best_run = runs.iloc[0]
            
            run_info = {
                "run_id": best_run.run_id,
                "experiment_id": best_run.experiment_id,
                "metrics": {
                    col.replace("metrics.", ""): best_run[col]
                    for col in best_run.index
                    if col.startswith("metrics.")
                },
                "params": {
                    col.replace("params.", ""): best_run[col]
                    for col in best_run.index
                    if col.startswith("params.")
                },
                "tags": {
                    col.replace("tags.", ""): best_run[col]
                    for col in best_run.index
                    if col.startswith("tags.")
                },
            }
            
            return run_info
        except Exception as e:
            self.logger.error(f"Failed to get best run: {e}")
            return None

    @staticmethod
    async def start_mlflow_ui(
        host: str = "0.0.0.0",
        port: int = 5000,
        tracking_uri: Optional[str] = None,
    ) -> bool:
        """
        Start MLflow UI.

        Args:
            host: Host to bind to
            port: Port to bind to
            tracking_uri: MLflow tracking URI

        Returns:
            Whether starting the UI was successful
        """
        try:
            import subprocess
            import sys
            
            cmd = [sys.executable, "-m", "mlflow", "ui", "--host", host, "--port", str(port)]
            
            if tracking_uri:
                cmd.extend(["--backend-store-uri", tracking_uri])
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            import time
            time.sleep(2)
            
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                logging.error(f"MLflow UI failed to start: {stderr}")
                return False
            
            logging.info(f"MLflow UI started at http://{host}:{port}")
            return True
        except Exception as e:
            logging.error(f"Failed to start MLflow UI: {e}")
            return False
