"""
ML-related models for the python_agent app.

This module provides Django models for ML-related data,
which are stored in the ML database.
"""

from django.db import models
import uuid
import json


class MLModel(models.Model):
    """
    Model for a machine learning model.
    
    This model represents a machine learning model.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    model_type = models.CharField(max_length=255)
    version = models.CharField(max_length=255)
    parameters = models.TextField(null=True, blank=True)
    metrics = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ml_model = True
        db_table = 'ml_models'
        verbose_name = 'ML Model'
        verbose_name_plural = 'ML Models'
    
    def __str__(self):
        return f"{self.name} v{self.version}"
    
    @property
    def parameters_json(self):
        """
        Get the model parameters as JSON.
        
        Returns:
            dict: The model parameters as JSON
        """
        if not self.parameters:
            return {}
        
        try:
            return json.loads(self.parameters)
        except json.JSONDecodeError:
            return {}
    
    @property
    def metrics_json(self):
        """
        Get the model metrics as JSON.
        
        Returns:
            dict: The model metrics as JSON
        """
        if not self.metrics:
            return {}
        
        try:
            return json.loads(self.metrics)
        except json.JSONDecodeError:
            return {}


class MLExperiment(models.Model):
    """
    Model for a machine learning experiment.
    
    This model represents a machine learning experiment.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    ml_model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='experiments')
    parameters = models.TextField(null=True, blank=True)
    metrics = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=255, default='created')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ml_model = True
        db_table = 'ml_experiments'
        verbose_name = 'ML Experiment'
        verbose_name_plural = 'ML Experiments'
    
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    @property
    def parameters_json(self):
        """
        Get the experiment parameters as JSON.
        
        Returns:
            dict: The experiment parameters as JSON
        """
        if not self.parameters:
            return {}
        
        try:
            return json.loads(self.parameters)
        except json.JSONDecodeError:
            return {}
    
    @property
    def metrics_json(self):
        """
        Get the experiment metrics as JSON.
        
        Returns:
            dict: The experiment metrics as JSON
        """
        if not self.metrics:
            return {}
        
        try:
            return json.loads(self.metrics)
        except json.JSONDecodeError:
            return {}


class MLTrainingRun(models.Model):
    """
    Model for a machine learning training run.
    
    This model represents a training run for a machine learning experiment.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    experiment = models.ForeignKey(MLExperiment, on_delete=models.CASCADE, related_name='training_runs')
    parameters = models.TextField(null=True, blank=True)
    metrics = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=255, default='created')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ml_model = True
        db_table = 'ml_training_runs'
        verbose_name = 'ML Training Run'
        verbose_name_plural = 'ML Training Runs'
    
    def __str__(self):
        return f"Run {self.id} for {self.experiment}"
    
    @property
    def parameters_json(self):
        """
        Get the training run parameters as JSON.
        
        Returns:
            dict: The training run parameters as JSON
        """
        if not self.parameters:
            return {}
        
        try:
            return json.loads(self.parameters)
        except json.JSONDecodeError:
            return {}
    
    @property
    def metrics_json(self):
        """
        Get the training run metrics as JSON.
        
        Returns:
            dict: The training run metrics as JSON
        """
        if not self.metrics:
            return {}
        
        try:
            return json.loads(self.metrics)
        except json.JSONDecodeError:
            return {}


class MLPrediction(models.Model):
    """
    Model for a machine learning prediction.
    
    This model represents a prediction made by a machine learning model.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ml_model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='predictions')
    input_data = models.TextField()
    output_data = models.TextField()
    confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ml_model = True
        db_table = 'ml_predictions'
        verbose_name = 'ML Prediction'
        verbose_name_plural = 'ML Predictions'
    
    def __str__(self):
        return f"Prediction {self.id} for {self.ml_model}"
    
    @property
    def input_json(self):
        """
        Get the prediction input data as JSON.
        
        Returns:
            dict: The prediction input data as JSON
        """
        try:
            return json.loads(self.input_data)
        except json.JSONDecodeError:
            return {}
    
    @property
    def output_json(self):
        """
        Get the prediction output data as JSON.
        
        Returns:
            dict: The prediction output data as JSON
        """
        try:
            return json.loads(self.output_data)
        except json.JSONDecodeError:
            return {}
