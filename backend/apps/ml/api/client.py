"""
API client for ML infrastructure.
"""

import logging
import requests
from typing import Dict, List, Any, Optional
import asyncio
import aiohttp

from .models import (
    ModelList,
    ModelDetail,
    FineTuningJobCreate,
    FineTuningJobDetail,
    FineTuningJobList,
    DatasetUpload,
    DatasetDetail,
    DatasetList,
    InferenceServiceCreate,
    InferenceServiceDetail,
    InferenceServiceList,
    PredictionRequest,
    PredictionResponse,
    ExperimentList,
    ExperimentDetail,
    ExperimentCreate,
    RunList,
    RunDetail,
    RunCreate,
    MetricsLog,
    ParamsLog,
    PipelineRunCreate,
    PipelineRunDetail,
    PipelineRunList,
    KServeModelCreate,
    KServeModelDetail,
    KServeModelList,
    FeatureRequest,
    FeatureResponse,
    ErrorResponse,
    HyperParameters,
    ResourceRequirements,
)


class MLInfrastructureAPIClient:
    """
    API client for ML infrastructure.
    """

    def __init__(
        self,
        base_url: str = "http://ml-infrastructure-api.example.com",
        api_key: Optional[str] = None,
    ):
        """
        Initialize ML infrastructure API client.

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
        self.logger = logging.getLogger("MLInfrastructureAPIClient")

    async def _make_async_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an asynchronous request to the API.

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
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(
                        url, headers=self.headers, params=params
                    ) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method == "POST":
                    if files:
                        form_data = aiohttp.FormData()
                        for key, value in data.items():
                            form_data.add_field(key, str(value))
                        for key, file_obj in files.items():
                            form_data.add_field(key, file_obj)

                        headers = {
                            k: v for k, v in self.headers.items() if k != "Content-Type"
                        }

                        async with session.post(
                            url, headers=headers, params=params, data=form_data
                        ) as response:
                            response.raise_for_status()
                            return await response.json()
                    else:
                        async with session.post(
                            url, headers=self.headers, params=params, json=data
                        ) as response:
                            response.raise_for_status()
                            return await response.json()
                elif method == "PUT":
                    async with session.put(
                        url, headers=self.headers, params=params, json=data
                    ) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method == "DELETE":
                    async with session.delete(
                        url, headers=self.headers, params=params, json=data
                    ) as response:
                        response.raise_for_status()
                        return await response.json()
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

        except aiohttp.ClientError as e:
            self.logger.error(f"Error making request: {str(e)}")
            raise

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a synchronous request to the API.

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

    async def get_models(self, model_type: Optional[str] = None) -> ModelList:
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

        response = await self._make_async_request("GET", "models", params=params)
        return ModelList(**response)

    async def get_model(self, model_id: str) -> ModelDetail:
        """
        Get model details.

        Args:
            model_id: Model ID

        Returns:
            Model details
        """
        response = await self._make_async_request("GET", f"models/{model_id}")
        return ModelDetail(**response)

    async def create_fine_tuning_job(
        self,
        model_type: str,
        training_data_path: str,
        validation_data_path: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
    ) -> FineTuningJobDetail:
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
        job_create = FineTuningJobCreate(
            model_type=model_type,
            training_data_path=training_data_path,
            validation_data_path=validation_data_path,
            hyperparameters=(
                HyperParameters(**hyperparameters) if hyperparameters else None
            ),
        )

        response = await self._make_async_request(
            "POST", "fine-tuning/jobs", data=job_create.model_dump(exclude_none=True)
        )

        return FineTuningJobDetail(**response)

    async def get_fine_tuning_job(self, job_id: str) -> FineTuningJobDetail:
        """
        Get fine-tuning job details.

        Args:
            job_id: Job ID

        Returns:
            Job details
        """
        response = await self._make_async_request("GET", f"fine-tuning/jobs/{job_id}")
        return FineTuningJobDetail(**response)

    async def list_fine_tuning_jobs(
        self,
        model_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> FineTuningJobList:
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

        response = await self._make_async_request(
            "GET", "fine-tuning/jobs", params=params
        )
        return FineTuningJobList(**response)

    async def cancel_fine_tuning_job(self, job_id: str) -> FineTuningJobDetail:
        """
        Cancel a fine-tuning job.

        Args:
            job_id: Job ID

        Returns:
            Job details
        """
        response = await self._make_async_request(
            "POST", f"fine-tuning/jobs/{job_id}/cancel"
        )
        return FineTuningJobDetail(**response)

    async def upload_training_data(
        self,
        file_path: str,
        dataset_name: Optional[str] = None,
    ) -> DatasetDetail:
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

            upload_request = DatasetUpload(dataset_name=dataset_name)
            data = upload_request.model_dump(exclude_none=True)

            response = await self._make_async_request(
                "POST", "datasets/upload", data=data, files=files
            )
            return DatasetDetail(**response)

    async def list_datasets(self, limit: int = 10) -> DatasetList:
        """
        List available datasets.

        Args:
            limit: Maximum number of datasets to return

        Returns:
            List of datasets
        """
        params = {"limit": limit}
        response = await self._make_async_request("GET", "datasets", params=params)
        return DatasetList(**response)

    async def get_dataset(self, dataset_id: str) -> DatasetDetail:
        """
        Get dataset details.

        Args:
            dataset_id: Dataset ID

        Returns:
            Dataset details
        """
        response = await self._make_async_request("GET", f"datasets/{dataset_id}")
        return DatasetDetail(**response)

    async def delete_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """
        Delete a dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            Deletion details
        """
        return await self._make_async_request("DELETE", f"datasets/{dataset_id}")

    async def create_inference_service(
        self,
        model_id: str,
        service_name: str,
        replicas: int = 1,
        resources: Optional[Dict[str, Any]] = None,
    ) -> InferenceServiceDetail:
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
        service_create = InferenceServiceCreate(
            model_id=model_id,
            service_name=service_name,
            replicas=replicas,
            resources=ResourceRequirements(**resources) if resources else None,
        )

        response = await self._make_async_request(
            "POST",
            "inference/services",
            data=service_create.model_dump(exclude_none=True),
        )

        return InferenceServiceDetail(**response)

    async def get_inference_service(self, service_id: str) -> InferenceServiceDetail:
        """
        Get inference service details.

        Args:
            service_id: Service ID

        Returns:
            Service details
        """
        response = await self._make_async_request(
            "GET", f"inference/services/{service_id}"
        )
        return InferenceServiceDetail(**response)

    async def list_inference_services(
        self,
        model_id: Optional[str] = None,
        limit: int = 10,
    ) -> InferenceServiceList:
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

        response = await self._make_async_request(
            "GET", "inference/services", params=params
        )
        return InferenceServiceList(**response)

    async def delete_inference_service(self, service_id: str) -> Dict[str, Any]:
        """
        Delete an inference service.

        Args:
            service_id: Service ID

        Returns:
            Deletion details
        """
        return await self._make_async_request(
            "DELETE", f"inference/services/{service_id}"
        )

    async def predict(
        self,
        service_id: str,
        input_text: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> PredictionResponse:
        """
        Make a prediction using an inference service.

        Args:
            service_id: Service ID
            input_text: Input text
            parameters: Prediction parameters

        Returns:
            Prediction result
        """
        prediction_request = PredictionRequest(
            input_text=input_text, parameters=parameters
        )

        response = await self._make_async_request(
            "POST",
            f"inference/services/{service_id}/predict",
            data=prediction_request.model_dump(exclude_none=True),
        )

        return PredictionResponse(**response)

    async def get_experiments(self, limit: int = 10) -> ExperimentList:
        """
        Get MLFlow experiments.

        Args:
            limit: Maximum number of experiments to return

        Returns:
            List of experiments
        """
        params = {"limit": limit}
        response = await self._make_async_request(
            "GET", "mlflow/experiments", params=params
        )
        return ExperimentList(**response)

    async def get_experiment(self, experiment_id: str) -> ExperimentDetail:
        """
        Get MLFlow experiment details.

        Args:
            experiment_id: Experiment ID

        Returns:
            Experiment details
        """
        response = await self._make_async_request(
            "GET", f"mlflow/experiments/{experiment_id}"
        )
        return ExperimentDetail(**response)

    async def create_experiment(
        self,
        name: str,
        artifact_location: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> ExperimentDetail:
        """
        Create MLFlow experiment.

        Args:
            name: Experiment name
            artifact_location: Artifact location
            tags: Experiment tags

        Returns:
            Experiment details
        """
        experiment_create = ExperimentCreate(
            name=name, artifact_location=artifact_location, tags=tags
        )

        response = await self._make_async_request(
            "POST",
            "mlflow/experiments",
            data=experiment_create.model_dump(exclude_none=True),
        )

        return ExperimentDetail(**response)

    async def get_runs(
        self,
        experiment_id: str,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> RunList:
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

        response = await self._make_async_request("GET", "mlflow/runs", params=params)
        return RunList(**response)

    async def get_run(self, run_id: str) -> RunDetail:
        """
        Get MLFlow run details.

        Args:
            run_id: Run ID

        Returns:
            Run details
        """
        response = await self._make_async_request("GET", f"mlflow/runs/{run_id}")
        return RunDetail(**response)

    async def create_run(
        self,
        experiment_id: str,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> RunDetail:
        """
        Create MLFlow run.

        Args:
            experiment_id: Experiment ID
            run_name: Run name
            tags: Run tags

        Returns:
            Run details
        """
        run_create = RunCreate(
            experiment_id=experiment_id, run_name=run_name, tags=tags
        )

        response = await self._make_async_request(
            "POST", "mlflow/runs", data=run_create.model_dump(exclude_none=True)
        )

        return RunDetail(**response)

    async def log_metrics(
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
        metrics_log = MetricsLog(metrics=metrics, step=step)

        return await self._make_async_request(
            "POST",
            f"mlflow/runs/{run_id}/metrics",
            data=metrics_log.model_dump(exclude_none=True),
        )

    async def log_params(
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
        params_log = ParamsLog(params=params)

        return await self._make_async_request(
            "POST",
            f"mlflow/runs/{run_id}/params",
            data=params_log.model_dump(exclude_none=True),
        )

    async def create_pipeline_run(
        self,
        pipeline_id: str,
        run_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> PipelineRunDetail:
        """
        Create a KubeFlow pipeline run.

        Args:
            pipeline_id: Pipeline ID
            run_name: Run name
            parameters: Pipeline parameters

        Returns:
            Run details
        """
        pipeline_run_create = PipelineRunCreate(
            pipeline_id=pipeline_id, run_name=run_name, parameters=parameters
        )

        response = await self._make_async_request(
            "POST",
            "kubeflow/pipelines/runs",
            data=pipeline_run_create.model_dump(exclude_none=True),
        )

        return PipelineRunDetail(**response)

    async def get_pipeline_run(self, run_id: str) -> PipelineRunDetail:
        """
        Get KubeFlow pipeline run details.

        Args:
            run_id: Run ID

        Returns:
            Run details
        """
        response = await self._make_async_request(
            "GET", f"kubeflow/pipelines/runs/{run_id}"
        )
        return PipelineRunDetail(**response)

    async def list_pipeline_runs(
        self,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> PipelineRunList:
        """
        List KubeFlow pipeline runs.

        Args:
            pipeline_id: Filter by pipeline ID
            status: Filter by status
            limit: Maximum number of runs to return

        Returns:
            List of runs
        """
        params = {"limit": limit}

        if pipeline_id:
            params["pipeline_id"] = pipeline_id

        if status:
            params["status"] = status

        response = await self._make_async_request(
            "GET", "kubeflow/pipelines/runs", params=params
        )
        return PipelineRunList(**response)

    async def create_kserve_model(
        self,
        name: str,
        model_uri: str,
        model_format: str = "pytorch",
        resources: Optional[Dict[str, Any]] = None,
        env: Optional[List[Dict[str, Any]]] = None,
    ) -> KServeModelDetail:
        """
        Create a KServe model.

        Args:
            name: Model name
            model_uri: Model URI
            model_format: Model format
            resources: Resource requirements
            env: Environment variables

        Returns:
            Model details
        """
        resource_requirements = None
        if resources:
            resource_requirements = ResourceRequirements(**resources)

        kserve_model = KServeModelCreate(
            name=name,
            model_uri=model_uri,
            model_format=model_format,
            resources=resource_requirements,
            env=env,
        )

        response = await self._make_async_request(
            "POST", "kserve/models", data=kserve_model.model_dump(exclude_none=True)
        )

        return KServeModelDetail(**response)

    async def get_kserve_model(self, name: str) -> KServeModelDetail:
        """
        Get KServe model details.

        Args:
            name: Model name

        Returns:
            Model details
        """
        response = await self._make_async_request("GET", f"kserve/models/{name}")
        return KServeModelDetail(**response)

    async def list_kserve_models(self, limit: int = 10) -> KServeModelList:
        """
        List KServe models.

        Args:
            limit: Maximum number of models to return

        Returns:
            List of models
        """
        params = {"limit": limit}
        response = await self._make_async_request("GET", "kserve/models", params=params)
        return KServeModelList(**response)

    async def delete_kserve_model(self, name: str) -> Dict[str, Any]:
        """
        Delete a KServe model.

        Args:
            name: Model name

        Returns:
            Deletion details
        """
        response = await self._make_async_request("DELETE", f"kserve/models/{name}")
        return response

    async def get_feature_values(
        self,
        entity_name: str,
        entity_ids: List[str],
        feature_names: List[str],
    ) -> FeatureResponse:
        """
        Get feature values from Feast.

        Args:
            entity_name: Entity name
            entity_ids: Entity IDs
            feature_names: Feature names

        Returns:
            Feature values
        """
        feature_request = FeatureRequest(
            entity_name=entity_name, entity_ids=entity_ids, feature_names=feature_names
        )

        response = await self._make_async_request(
            "POST", "feast/features", data=feature_request.model_dump()
        )

        return FeatureResponse(**response)

    def run_async(self, coroutine):
        """
        Run an asynchronous coroutine.

        Args:
            coroutine: Asynchronous coroutine

        Returns:
            Coroutine result
        """
        return asyncio.run(coroutine)

    def get_models_sync(self, model_type: Optional[str] = None) -> ModelList:
        """
        Get available models (synchronous version).

        Args:
            model_type: Filter by model type

        Returns:
            List of models
        """
        params = {}
        if model_type:
            params["model_type"] = model_type

        response = self._make_request("GET", "models", params=params)
        return ModelList(**response)

    def predict_sync(
        self,
        service_id: str,
        input_text: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> PredictionResponse:
        """
        Make a prediction using an inference service (synchronous version).

        Args:
            service_id: Service ID
            input_text: Input text
            parameters: Prediction parameters

        Returns:
            Prediction result
        """
        prediction_request = PredictionRequest(
            input_text=input_text, parameters=parameters
        )

        response = self._make_request(
            "POST",
            f"inference/services/{service_id}/predict",
            data=prediction_request.model_dump(exclude_none=True),
        )

        return PredictionResponse(**response)
