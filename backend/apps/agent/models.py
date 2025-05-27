from django.db import models
from django.utils.translation import gettext_lazy as _
import yaml
import json
import os
from pathlib import Path

from apps.agent.agent_framework.shared.runtime import RuntimeConfig


class AgentConfiguration(models.Model):
    """Django model for agent configurations."""
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    config_yaml = models.TextField(help_text=_("YAML configuration for the agent"))
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Agent Configuration")
        verbose_name_plural = _("Agent Configurations")
        ordering = ["-updated_at"]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one default configuration."""
        if self.is_default:
            AgentConfiguration.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    @property
    def config_dict(self):
        """Return the configuration as a dictionary."""
        return yaml.safe_load(self.config_yaml)
    
    @classmethod
    def load_from_files(cls):
        """Load configurations from YAML files in the agent_config directory."""
        config_dir = Path(__file__).parent / "agent_config"
        for yaml_file in config_dir.glob("*.yaml"):
            if not yaml_file.is_file():
                continue
                
            with open(yaml_file, "r") as f:
                config_yaml = f.read()
            
            name = yaml_file.stem
            is_default = (name == "default")
            
            cls.objects.update_or_create(
                name=name,
                defaults={
                    "config_yaml": config_yaml,
                    "is_default": is_default,
                    "description": f"Loaded from {yaml_file.name}"
                }
            )


class RuntimeConfiguration(models.Model):
    """Django model for runtime configurations."""
    
    name = models.CharField(max_length=255, unique=True)
    config_type = models.CharField(
        max_length=20,
        choices=[
            ("local", "Local Runtime"),
            ("remote", "Remote Runtime"),
            ("dummy", "Dummy Runtime"),
        ]
    )
    config_json = models.JSONField(help_text=_("JSON configuration for the runtime"))
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Runtime Configuration")
        verbose_name_plural = _("Runtime Configurations")
        ordering = ["-updated_at"]
    
    def __str__(self):
        return f"{self.name} ({self.config_type})"
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one default configuration."""
        if self.is_default:
            RuntimeConfiguration.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    @property
    def runtime_config(self) -> RuntimeConfig:
        """Return the runtime configuration as a Pydantic model."""
        from apps.agent.agent_framework.shared.runtime import (
            LocalRuntimeConfig,
            RuntimeConfig,
        )
        
        config_dict = self.config_json
        config_dict["type"] = self.config_type
        
        if self.config_type == "local":
            return LocalRuntimeConfig(**config_dict)
        elif self.config_type == "remote" or self.config_type == "dummy":
            return RuntimeConfig(**config_dict)
        else:
            raise ValueError(f"Unknown runtime type: {self.config_type}")
    
    def get_runtime(self):
        """Get the runtime instance from the configuration."""
        return self.runtime_config.get_runtime()
