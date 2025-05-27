"""
Django models for agent configuration.

This module provides Django models for agent configuration, converting
the YAML-based configuration from the original implementation to Django models.
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField
import json
import yaml
from pathlib import Path

from apps.agent.kled.agent import CONFIG_DIR


class AgentConfig(models.Model):
    """Django model for agent configuration."""
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    
    model_name = models.CharField(max_length=255)
    temperature = models.FloatField(default=0.0)
    top_p = models.FloatField(default=1.0)
    
    per_instance_cost_limit = models.FloatField(default=3.0)
    total_cost_limit = models.FloatField(default=0.0)
    per_instance_call_limit = models.IntegerField(default=0)
    
    use_function_calling = models.BooleanField(default=True)
    submit_command = models.CharField(max_length=255, default="submit")
    
    config_file = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)
    
    raw_config = models.JSONField(default=dict)
    
    class Meta:
        verbose_name = "Agent Configuration"
        verbose_name_plural = "Agent Configurations"
    
    def __str__(self):
        return f"{self.name} ({self.model_name})"
    
    @classmethod
    def load_from_files(cls):
        """Load agent configurations from YAML files in the CONFIG_DIR."""
        count = 0
        
        for config_file in CONFIG_DIR.glob("*.yaml"):
            try:
                config_data = yaml.safe_load(config_file.read_text())
                
                agent_config = config_data.get("agent", {})
                model_config = agent_config.get("model", {})
                
                config, created = cls.objects.update_or_create(
                    name=config_file.stem,
                    defaults={
                        "description": agent_config.get("description", ""),
                        "model_name": model_config.get("model_name", ""),
                        "temperature": model_config.get("temperature", 0.0),
                        "top_p": model_config.get("top_p", 1.0),
                        "per_instance_cost_limit": model_config.get("per_instance_cost_limit", 3.0),
                        "total_cost_limit": model_config.get("total_cost_limit", 0.0),
                        "per_instance_call_limit": model_config.get("per_instance_call_limit", 0),
                        "use_function_calling": agent_config.get("use_function_calling", True),
                        "submit_command": agent_config.get("submit_command", "submit"),
                        "config_file": str(config_file),
                        "is_default": config_file.stem == "default",
                        "raw_config": config_data,
                    }
                )
                
                count += 1
            except Exception as e:
                print(f"Error loading configuration from {config_file}: {str(e)}")
        
        return count


class ToolConfig(models.Model):
    """Django model for tool configuration."""
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    agent_config = models.ForeignKey(AgentConfig, on_delete=models.CASCADE, related_name="tools")
    
    command_name = models.CharField(max_length=255)
    end_command = models.CharField(max_length=255, blank=True, null=True)
    function_name = models.CharField(max_length=255, blank=True, null=True)
    
    parameters = models.JSONField(default=dict)
    is_enabled = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Tool Configuration"
        verbose_name_plural = "Tool Configurations"
        unique_together = ("name", "agent_config")
    
    def __str__(self):
        return f"{self.name} ({self.agent_config.name})"


class ProblemStatement(models.Model):
    """Django model for problem statement configuration."""
    
    TYPE_CHOICES = [
        ("text", "Text"),
        ("file", "File"),
        ("url", "URL"),
    ]
    
    agent_config = models.OneToOneField(AgentConfig, on_delete=models.CASCADE, related_name="problem_statement")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="text")
    input = models.TextField()
    
    class Meta:
        verbose_name = "Problem Statement"
        verbose_name_plural = "Problem Statements"
    
    def __str__(self):
        return f"Problem for {self.agent_config.name}"


class EnvironmentConfig(models.Model):
    """Django model for environment configuration."""
    
    agent_config = models.OneToOneField(AgentConfig, on_delete=models.CASCADE, related_name="environment")
    
    image_name = models.CharField(max_length=255, blank=True)
    script = models.TextField(blank=True)
    
    repo_type = models.CharField(max_length=10, default="auto")
    repo_path = models.CharField(max_length=255, blank=True)
    base_commit = models.CharField(max_length=40, blank=True)
    
    class Meta:
        verbose_name = "Environment Configuration"
        verbose_name_plural = "Environment Configurations"
    
    def __str__(self):
        return f"Environment for {self.agent_config.name}"
