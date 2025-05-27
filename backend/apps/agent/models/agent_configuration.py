from django.db import models
from django.utils.translation import gettext_lazy as _
import yaml
import os
from pathlib import Path


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
        config_dir = Path(__file__).parent.parent / "agent_config"
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
