"""
API client for ML infrastructure.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union


class MLInfrastructureClient:
    """
    Client for interacting with ML infrastructure.
    """

    def __init__(
        self,
        base_url: str = "http://ml-infrastructure-api.example.com",
        api_key: Optional[str] = None,
    ):
        """
        Initialize ML infrastructure client.

        Args:
            base_url: Base URL for the API
            api_key: API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
        }

        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("MLInfrastructureClient")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a request to the API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request data
            files: Files to upload

        Returns:
            Response data
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method == "POST":
                if files:
                    headers = {
                        k: v for k, v in self.headers.items() if k != "Content-Type"
                    }
                    response = requests.post(
                        url, headers=headers, params=params, data=data, files=files
                    )
                else:
                    response = requests.post(
                        url, headers=self.headers, params=params, json=data
                    )
            elif method == "PUT":
                response = requests.put(
                    url, headers=self.headers, params=params, json=data
                )
            elif method == "DELETE":
                response = requests.delete(
                    url, headers=self.headers, params=params, json=data
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request: {str(e)}")
            raise

    def get_models(self, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available models.

        Args:
            model_type: Filter by model type

        Returns:
            List of models
        """
        params = {}
        if model_type:
            params["model_type"] = model_type

        return self._make_request("GET", "models", params=params)

    def get_model(self, model_id: str) -> Dict[str, Any]:
        """
        Get model details.

        Args:
            model_id: Model ID

        Returns:
            Model details
        """
        return self._make_request("GET", f"models/{model_id}")

    def create_fine_tuning_job(
        self,
        model_type: str,
        training_data_path: str,
        validation_data_path: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a fine-tuning job.

        Args:
            model_type: Model type
            training_data_path: Path to training data
            validation_data_path: Path to validation data
            hyperparameters: Hyperparameters for fine-tuning

        Returns:
            Job details
        """
        data = {
            "model_type": model_type,
            "training_data_path": training_data_path,
        }

        if validation_data_path:
            data["validation_data_path"] = validation_data_path

        if hyperparameters:
            data["hyperparameters"] = hyperparameters

        return self._make_request("POST", "fine-tuning/jobs", data=data)

    def get_fine_tuning_job(self, job_id: str) -> Dict[str, Any]:
        """
        Get fine-tuning job details.

        Args:
            job_id: Job ID

        Returns:
            Job details
        """
        return self._make_request("GET", f"fine-tuning/jobs/{job_id}")

    def list_fine_tuning_jobs(
        self,
        model_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        List fine-tuning jobs.

        Args:
            model_type: Filter by model type
            status: Filter by status
            limit: Maximum number of jobs to return

        Returns:
            List of jobs
        """
        params = {"limit": limit}

        if model_type:
            params["model_type"] = model_type

        if status:
            params["status"] = status

        return self._make_request("GET", "fine-tuning/jobs", params=params)

    def cancel_fine_tuning_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a fine-tuning job.

        Args:
            job_id: Job ID

        Returns:
            Job details
        """
        return self._make_request("POST", f"fine-tuning/jobs/{job_id}/cancel")

    def upload_training_data(
        self,
        file_path: str,
        dataset_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload training data.

        Args:
            file_path: Path to training data file
            dataset_name: Name of the dataset

        Returns:
            Upload details
        """
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {}

            if dataset_name:
                data["dataset_name"] = dataset_name

            return self._make_request("POST", "datasets/upload", data=data, files=files)

    def list_datasets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List available datasets.

        Args:
            limit: Maximum number of datasets to return

        Returns:
            List of datasets
        """
        params = {"limit": limit}
        return self._make_request("GET", "datasets", params=params)

    def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get dataset details.

        Args:
            dataset_id: Dataset ID

        Returns:
            Dataset details
        """
        return self._make_request("GET", f"datasets/{dataset_id}")

    def delete_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """
        Delete a dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            Deletion details
        """
        return self._make_request("DELETE", f"datasets/{dataset_id}")

    def create_inference_service(
        self,
        model_id: str,
        service_name: str,
        replicas: int = 1,
        resources: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create an inference service.

        Args:
            model_id: Model ID
            service_name: Service name
            replicas: Number of replicas
            resources: Resource requirements

        Returns:
            Service details
        """
        data = {
            "model_id": model_id,
            "service_name": service_name,
            "replicas": replicas,
        }

        if resources:
            data["resources"] = resources

        return self._make_request("POST", "inference/services", data=data)

    def get_inference_service(self, service_id: str) -> Dict[str, Any]:
        """
        Get inference service details.

        Args:
            service_id: Service ID

        Returns:
            Service details
        """
        return self._make_request("GET", f"inference/services/{service_id}")

    def list_inference_services(
        self,
        model_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        List inference services.

        Args:
            model_id: Filter by model ID
            limit: Maximum number of services to return

        Returns:
            List of services
        """
        params = {"limit": limit}

        if model_id:
            params["model_id"] = model_id

        return self._make_request("GET", "inference/services", params=params)

    def delete_inference_service(self, service_id: str) -> Dict[str, Any]:
        """
        Delete an inference service.

        Args:
            service_id: Service ID

        Returns:
            Deletion details
        """
        return self._make_request("DELETE", f"inference/services/{service_id}")

    def predict(
        self,
        service_id: str,
        input_text: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a prediction using an inference service.

        Args:
            service_id: Service ID
            input_text: Input text
            parameters: Prediction parameters

        Returns:
            Prediction result
        """
        data = {
            "input_text": input_text,
        }

        if parameters:
            data["parameters"] = parameters

        return self._make_request(
            "POST", f"inference/services/{service_id}/predict", data=data
        )

    def get_experiments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get MLFlow experiments.

        Args:
            limit: Maximum number of experiments to return

        Returns:
            List of experiments
        """
        params = {"limit": limit}
        return self._make_request("GET", "mlflow/experiments", params=params)

    def get_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get MLFlow experiment details.

        Args:
            experiment_id: Experiment ID

        Returns:
            Experiment details
        """
        return self._make_request("GET", f"mlflow/experiments/{experiment_id}")

    def create_experiment(
        self,
        name: str,
        artifact_location: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create MLFlow experiment.

        Args:
            name: Experiment name
            artifact_location: Artifact location
            tags: Experiment tags

        Returns:
            Experiment details
        """
        data = {
            "name": name,
        }

        if artifact_location:
            data["artifact_location"] = artifact_location

        if tags:
            data["tags"] = tags

        return self._make_request("POST", "mlflow/experiments", data=data)

    def get_runs(
        self,
        experiment_id: str,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get MLFlow runs.

        Args:
            experiment_id: Experiment ID
            status: Filter by status
            limit: Maximum number of runs to return

        Returns:
            List of runs
        """
        params = {
            "experiment_id": experiment_id,
            "limit": limit,
        }

        if status:
            params["status"] = status

        return self._make_request("GET", "mlflow/runs", params=params)

    def get_run(self, run_id: str) -> Dict[str, Any]:
        """
        Get MLFlow run details.

        Args:
            run_id: Run ID

        Returns:
            Run details
        """
        return self._make_request("GET", f"mlflow/runs/{run_id}")

    def create_run(
        self,
        experiment_id: str,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create MLFlow run.

        Args:
            experiment_id: Experiment ID
            run_name: Run name
            tags: Run tags

        Returns:
            Run details
        """
        data = {
            "experiment_id": experiment_id,
        }

        if run_name:
            data["run_name"] = run_name

        if tags:
            data["tags"] = tags

        return self._make_request("POST", "mlflow/runs", data=data)

    def log_metrics(
        self,
        run_id: str,
        metrics: Dict[str, float],
        step: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Log metrics to MLFlow run.

        Args:
            run_id: Run ID
            metrics: Metrics to log
            step: Step number

        Returns:
            Log details
        """
        data = {
            "metrics": metrics,
        }

        if step is not None:
            data["step"] = step

        return self._make_request("POST", f"mlflow/runs/{run_id}/metrics", data=data)

    def log_params(
        self,
        run_id: str,
        params: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Log parameters to MLFlow run.

        Args:
            run_id: Run ID
            params: Parameters to log

        Returns:
            Log details
        """
        data = {
            "params": params,
        }

        return self._make_request("POST", f"mlflow/runs/{run_id}/params", data=data)

    def log_artifact(
        self,
        run_id: str,
        file_path: str,
        artifact_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log artifact to MLFlow run.

        Args:
            run_id: Run ID
            file_path: Path to artifact file
            artifact_path: Path within artifact directory

        Returns:
            Log details
        """
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {}

            if artifact_path:
                data["artifact_path"] = artifact_path

            return self._make_request(
                "POST", f"mlflow/runs/{run_id}/artifacts", data=data, files=files
            )

    def get_registered_models(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get registered models.

        Args:
            limit: Maximum number of models to return

        Returns:
            List of models
        """
        params = {"limit": limit}
        return self._make_request("GET", "mlflow/registered-models", params=params)

    def get_registered_model(self, name: str) -> Dict[str, Any]:
        """
        Get registered model details.

        Args:
            name: Model name

        Returns:
            Model details
        """
        return self._make_request("GET", f"mlflow/registered-models/{name}")

    def register_model(
        self,
        run_id: str,
        model_path: str,
        name: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Register model.

        Args:
            run_id: Run ID
            model_path: Path to model within run artifacts
            name: Model name
            description: Model description
            tags: Model tags

        Returns:
            Registration details
        """
        data = {
            "run_id": run_id,
            "model_path": model_path,
            "name": name,
        }

        if description:
            data["description"] = description

        if tags:
            data["tags"] = tags

        return self._make_request("POST", "mlflow/registered-models", data=data)
