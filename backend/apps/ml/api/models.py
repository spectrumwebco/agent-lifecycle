"""
Pydantic models for ML infrastructure API client.

This module provides Pydantic models for request and response data
for the ML infrastructure API client.
"""

from typing import Dict, List, Any, Optional, Union, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, HttpUrl


class ModelBase(BaseModel):
    """Base model for all models."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Model name")
    created_at: datetime = Field(..., description="Creation timestamp")


class ModelDetail(ModelBase):
    """Detailed model information."""

    model_type: str = Field(..., description="Model type")
    version: str = Field(..., description="Model version")
    description: Optional[str] = Field(None, description="Model description")
    metrics: Optional[Dict[str, float]] = Field(None, description="Model metrics")
    tags: Optional[Dict[str, str]] = Field(None, description="Model tags")
    uri: str = Field(..., description="Model URI")
    status: str = Field(..., description="Model status")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ModelList(BaseModel):
    """List of models."""

    models: List[ModelBase] = Field(..., description="List of models")
    total: int = Field(..., description="Total number of models")


class HyperParameters(BaseModel):
    """Hyperparameters for fine-tuning."""

    learning_rate: Optional[float] = Field(None, description="Learning rate")
    batch_size: Optional[int] = Field(None, description="Batch size")
    epochs: Optional[int] = Field(None, description="Number of epochs")
    warmup_steps: Optional[int] = Field(None, description="Warmup steps")
    weight_decay: Optional[float] = Field(None, description="Weight decay")
    gradient_accumulation_steps: Optional[int] = Field(
        None, description="Gradient accumulation steps"
    )
    max_grad_norm: Optional[float] = Field(None, description="Maximum gradient norm")
    optimizer: Optional[str] = Field(None, description="Optimizer")
    scheduler: Optional[str] = Field(None, description="Scheduler")
    additional_params: Optional[Dict[str, Any]] = Field(
        None, description="Additional parameters"
    )


class FineTuningJobCreate(BaseModel):
    """Create fine-tuning job request."""

    model_type: str = Field(..., description="Model type")
    training_data_path: str = Field(..., description="Path to training data")
    validation_data_path: Optional[str] = Field(
        None, description="Path to validation data"
    )
    hyperparameters: Optional[HyperParameters] = Field(
        None, description="Hyperparameters for fine-tuning"
    )


class FineTuningJobBase(BaseModel):
    """Base fine-tuning job information."""

    id: str = Field(..., description="Job ID")
    model_type: str = Field(..., description="Model type")
    status: str = Field(..., description="Job status")
    created_at: datetime = Field(..., description="Creation timestamp")


class FineTuningJobDetail(FineTuningJobBase):
    """Detailed fine-tuning job information."""

    training_data_path: str = Field(..., description="Path to training data")
    validation_data_path: Optional[str] = Field(
        None, description="Path to validation data"
    )
    hyperparameters: Optional[HyperParameters] = Field(
        None, description="Hyperparameters for fine-tuning"
    )
    metrics: Optional[Dict[str, float]] = Field(None, description="Training metrics")
    model_id: Optional[str] = Field(None, description="ID of the fine-tuned model")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(
        None, description="Error message if job failed"
    )


class FineTuningJobList(BaseModel):
    """List of fine-tuning jobs."""

    jobs: List[FineTuningJobBase] = Field(..., description="List of fine-tuning jobs")
    total: int = Field(..., description="Total number of jobs")


class DatasetUpload(BaseModel):
    """Dataset upload request."""

    dataset_name: Optional[str] = Field(None, description="Name of the dataset")


class DatasetBase(BaseModel):
    """Base dataset information."""

    id: str = Field(..., description="Dataset ID")
    name: str = Field(..., description="Dataset name")
    created_at: datetime = Field(..., description="Creation timestamp")
    size_bytes: int = Field(..., description="Dataset size in bytes")


class DatasetDetail(DatasetBase):
    """Detailed dataset information."""

    file_path: str = Field(..., description="Path to dataset file")
    format: str = Field(..., description="Dataset format")
    num_examples: int = Field(..., description="Number of examples in dataset")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Dataset metadata")


class DatasetList(BaseModel):
    """List of datasets."""

    datasets: List[DatasetBase] = Field(..., description="List of datasets")
    total: int = Field(..., description="Total number of datasets")


class ResourceRequirements(BaseModel):
    """Resource requirements for services."""

    cpu: Optional[str] = Field(None, description="CPU requirements")
    memory: Optional[str] = Field(None, description="Memory requirements")
    gpu: Optional[str] = Field(None, description="GPU requirements")
    storage: Optional[str] = Field(None, description="Storage requirements")


class InferenceServiceCreate(BaseModel):
    """Create inference service request."""

    model_id: str = Field(..., description="Model ID")
    service_name: str = Field(..., description="Service name")
    replicas: int = Field(1, description="Number of replicas")
    resources: Optional[ResourceRequirements] = Field(
        None, description="Resource requirements"
    )


class InferenceServiceBase(BaseModel):
    """Base inference service information."""

    id: str = Field(..., description="Service ID")
    service_name: str = Field(..., description="Service name")
    model_id: str = Field(..., description="Model ID")
    status: str = Field(..., description="Service status")
    created_at: datetime = Field(..., description="Creation timestamp")


class InferenceServiceDetail(InferenceServiceBase):
    """Detailed inference service information."""

    replicas: int = Field(..., description="Number of replicas")
    resources: Optional[ResourceRequirements] = Field(
        None, description="Resource requirements"
    )
    endpoint: str = Field(..., description="Service endpoint")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metrics: Optional[Dict[str, float]] = Field(None, description="Service metrics")


class InferenceServiceList(BaseModel):
    """List of inference services."""

    services: List[InferenceServiceBase] = Field(
        ..., description="List of inference services"
    )
    total: int = Field(..., description="Total number of services")


class PredictionRequest(BaseModel):
    """Prediction request."""

    input_text: str = Field(..., description="Input text")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Prediction parameters"
    )


class PredictionResponse(BaseModel):
    """Prediction response."""

    output: str = Field(..., description="Prediction output")
    confidence: Optional[float] = Field(None, description="Prediction confidence")
    latency_ms: float = Field(..., description="Prediction latency in milliseconds")
    model_id: str = Field(..., description="Model ID")
    service_id: str = Field(..., description="Service ID")
    timestamp: datetime = Field(..., description="Prediction timestamp")


class ExperimentBase(BaseModel):
    """Base experiment information."""

    id: str = Field(..., description="Experiment ID")
    name: str = Field(..., description="Experiment name")
    created_at: datetime = Field(..., description="Creation timestamp")


class ExperimentDetail(ExperimentBase):
    """Detailed experiment information."""

    artifact_location: str = Field(..., description="Artifact location")
    tags: Optional[Dict[str, str]] = Field(None, description="Experiment tags")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ExperimentList(BaseModel):
    """List of experiments."""

    experiments: List[ExperimentBase] = Field(..., description="List of experiments")
    total: int = Field(..., description="Total number of experiments")


class ExperimentCreate(BaseModel):
    """Create experiment request."""

    name: str = Field(..., description="Experiment name")
    artifact_location: Optional[str] = Field(None, description="Artifact location")
    tags: Optional[Dict[str, str]] = Field(None, description="Experiment tags")


class RunBase(BaseModel):
    """Base run information."""

    id: str = Field(..., description="Run ID")
    experiment_id: str = Field(..., description="Experiment ID")
    status: str = Field(..., description="Run status")
    created_at: datetime = Field(..., description="Creation timestamp")


class RunDetail(RunBase):
    """Detailed run information."""

    run_name: Optional[str] = Field(None, description="Run name")
    tags: Optional[Dict[str, str]] = Field(None, description="Run tags")
    metrics: Optional[Dict[str, float]] = Field(None, description="Run metrics")
    params: Optional[Dict[str, str]] = Field(None, description="Run parameters")
    artifact_uri: str = Field(..., description="Artifact URI")
    updated_at: datetime = Field(..., description="Last update timestamp")
    ended_at: Optional[datetime] = Field(None, description="End timestamp")


class RunList(BaseModel):
    """List of runs."""

    runs: List[RunBase] = Field(..., description="List of runs")
    total: int = Field(..., description="Total number of runs")


class RunCreate(BaseModel):
    """Create run request."""

    experiment_id: str = Field(..., description="Experiment ID")
    run_name: Optional[str] = Field(None, description="Run name")
    tags: Optional[Dict[str, str]] = Field(None, description="Run tags")


class MetricsLog(BaseModel):
    """Metrics log request."""

    metrics: Dict[str, float] = Field(..., description="Metrics to log")
    step: Optional[int] = Field(None, description="Step number")


class ParamsLog(BaseModel):
    """Parameters log request."""

    params: Dict[str, str] = Field(..., description="Parameters to log")


class PipelineRunCreate(BaseModel):
    """Create pipeline run request."""

    pipeline_id: str = Field(..., description="Pipeline ID")
    run_name: str = Field(..., description="Run name")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Pipeline parameters"
    )


class PipelineRunBase(BaseModel):
    """Base pipeline run information."""

    id: str = Field(..., description="Run ID")
    pipeline_id: str = Field(..., description="Pipeline ID")
    run_name: str = Field(..., description="Run name")
    status: str = Field(..., description="Run status")
    created_at: datetime = Field(..., description="Creation timestamp")


class PipelineRunDetail(PipelineRunBase):
    """Detailed pipeline run information."""

    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Pipeline parameters"
    )
    metrics: Optional[Dict[str, float]] = Field(None, description="Run metrics")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(
        None, description="Error message if run failed"
    )


class PipelineRunList(BaseModel):
    """List of pipeline runs."""

    runs: List[PipelineRunBase] = Field(..., description="List of pipeline runs")
    total: int = Field(..., description="Total number of runs")


class KServeModelCreate(BaseModel):
    """Create KServe model request."""

    name: str = Field(..., description="Model name")
    model_uri: str = Field(..., description="Model URI")
    model_format: str = Field("pytorch", description="Model format")
    resources: Optional[ResourceRequirements] = Field(
        None, description="Resource requirements"
    )
    env: Optional[List[Dict[str, Any]]] = Field(
        None, description="Environment variables"
    )


class KServeModelBase(BaseModel):
    """Base KServe model information."""

    id: str = Field(..., description="Model ID")
    name: str = Field(..., description="Model name")
    status: str = Field(..., description="Model status")
    created_at: datetime = Field(..., description="Creation timestamp")


class KServeModelDetail(KServeModelBase):
    """Detailed KServe model information."""

    model_uri: str = Field(..., description="Model URI")
    model_format: str = Field(..., description="Model format")
    resources: Optional[ResourceRequirements] = Field(
        None, description="Resource requirements"
    )
    env: Optional[List[Dict[str, Any]]] = Field(
        None, description="Environment variables"
    )
    endpoint: str = Field(..., description="Model endpoint")
    updated_at: datetime = Field(..., description="Last update timestamp")


class KServeModelList(BaseModel):
    """List of KServe models."""

    models: List[KServeModelBase] = Field(..., description="List of KServe models")
    total: int = Field(..., description="Total number of models")


class FeatureRequest(BaseModel):
    """Feature request."""

    entity_id: str = Field(..., description="Entity ID")
    feature_names: List[str] = Field(..., description="Feature names")


class FeatureResponse(BaseModel):
    """Feature response."""

    entity_id: str = Field(..., description="Entity ID")
    features: Dict[str, Any] = Field(..., description="Feature values")
    timestamp: datetime = Field(..., description="Feature timestamp")


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(..., description="Error timestamp")
