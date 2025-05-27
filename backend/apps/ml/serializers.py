"""
Serializers for the ML API app.
"""

from rest_framework import serializers
import sys
from django.conf import settings

sys.path.append(str(settings.SRC_DIR))


class PydanticModelSerializer(serializers.Serializer):
    """Base serializer for Pydantic models."""

    @classmethod
    def from_pydantic(cls, pydantic_instance):
        """Convert a Pydantic model instance to a serializer instance."""
        return cls(pydantic_instance.model_dump())


class ModelDetailSerializer(PydanticModelSerializer):
    """Serializer for ModelDetail Pydantic model."""
    id = serializers.CharField()
    name = serializers.CharField()
    version = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    parameters = serializers.DictField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class ModelListSerializer(PydanticModelSerializer):
    """Serializer for ModelList Pydantic model."""
    models = serializers.ListField(child=serializers.CharField())


class FineTuningJobDetailSerializer(PydanticModelSerializer):
    """Serializer for FineTuningJobDetail Pydantic model."""
    id = serializers.CharField()
    model_id = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    fine_tuned_model = serializers.CharField(allow_null=True)
    training_file = serializers.CharField()
    validation_file = serializers.CharField(allow_null=True)
    metrics = serializers.DictField(allow_null=True)
    error = serializers.CharField(allow_null=True)


class FineTuningJobCreateSerializer(PydanticModelSerializer):
    """Serializer for FineTuningJobCreate Pydantic model."""
    model_id = serializers.CharField()
    training_file = serializers.CharField()
    validation_file = serializers.CharField(allow_null=True)
    suffix = serializers.CharField(allow_null=True)
    compute_config = serializers.DictField(allow_null=True)


class InferenceServiceDetailSerializer(PydanticModelSerializer):
    """Serializer for InferenceServiceDetail Pydantic model."""
    id = serializers.CharField()
    name = serializers.CharField()
    model_id = serializers.CharField()
    status = serializers.CharField()
    url = serializers.URLField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    replicas = serializers.IntegerField()
    resources = serializers.DictField()
    scaling_config = serializers.DictField(allow_null=True)
    error = serializers.CharField(allow_null=True)


class InferenceServiceCreateSerializer(PydanticModelSerializer):
    """Serializer for InferenceServiceCreate Pydantic model."""
    name = serializers.CharField()
    model_id = serializers.CharField()
    replicas = serializers.IntegerField()
    resources = serializers.DictField()
    scaling_config = serializers.DictField(allow_null=True)
    timeout = serializers.IntegerField(allow_null=True)


class ValidationResultSerializer(PydanticModelSerializer):
    """Serializer for ValidationResult Pydantic model."""
    schema_name = serializers.CharField()
    total_examples = serializers.IntegerField()
    valid_examples = serializers.IntegerField()
    invalid_examples = serializers.IntegerField()
    valid_ratio = serializers.FloatField()
    validation_errors = serializers.ListField(child=serializers.DictField())


class QualityMetricsSerializer(PydanticModelSerializer):
    """Serializer for QualityMetrics Pydantic model."""
    total_examples = serializers.IntegerField()
    empty_fields = serializers.DictField()
    length_metrics = serializers.DictField()
    source_distribution = serializers.DictField()
    repository_distribution = serializers.DictField()
    topic_distribution = serializers.DictField()
    label_distribution = serializers.DictField()
