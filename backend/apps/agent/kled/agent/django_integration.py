"""
Django integration for the agent.

This module provides Django integration for the agent, connecting
the agent loop with Django models and views.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from django.conf import settings
from django.utils import timezone

from apps.agent.kled.agent import CONFIG_DIR, PACKAGE_DIR
from apps.agent.kled.agent.django_models.agent_models import (
    AgentModel, AgentRun, AgentStats, AgentSession, AgentThread
)
from apps.agent.kled.agent.django_models.config_models import (
    AgentConfig, ToolConfig, ProblemStatement, EnvironmentConfig
)

from apps.agent.agent_framework.shared.runtime import RuntimeConfig
from apps.agent.agent_framework.shared.runtime import AbstractRuntime

sys.path.append(str(PACKAGE_DIR.parent))
from apps.agent.kled.agent.run.run_single import RunSingle, RunSingleConfig


class DjangoAgentRuntime(AbstractRuntime):
    """Django implementation of the agent runtime."""
    
    def __init__(self, config: RuntimeConfig):
        """Initialize the Django agent runtime."""
        super().__init__(config)
        self.agent_run = None
        self.agent_thread = None
    
    def initialize(self):
        """Initialize the runtime."""
        stats = AgentStats.objects.create()
        
        agent_model, _ = AgentModel.objects.get_or_create(
            name=self.config.model_name,
            defaults={
                'temperature': getattr(self.config, 'temperature', 0.0),
                'top_p': getattr(self.config, 'top_p', 1.0),
                'per_instance_cost_limit': getattr(self.config, 'cost_limit', 3.0),
                'total_cost_limit': 0.0,
                'per_instance_call_limit': 0,
            }
        )
        
        self.agent_run = AgentRun.objects.create(
            agent_model=agent_model,
            stats=stats
        )
        
        self.agent_thread = AgentThread.objects.create(
            session=AgentSession.objects.create()
        )
        
        return True
    
    def run_agent(self, config_obj: RunSingleConfig):
        """Run the agent with the specified configuration."""
        try:
            main = RunSingle.from_config(config_obj)
            result = main.run()
            
            self.agent_run.mark_complete(
                exit_status=result.info.get('exit_status'),
                submission=result.info.get('submission')
            )
            
            trajectory_id = self.agent_run.save_trajectory(result.trajectory)
            
            return {
                'status': 'success',
                'exit_status': result.info.get('exit_status'),
                'submission': result.info.get('submission'),
                'trajectory_id': trajectory_id
            }
        
        except Exception as e:
            self.agent_run.mark_complete(exit_status="error")
            
            import traceback
            return {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def cleanup(self):
        """Clean up the runtime."""
        return True


def load_agent_config(config_name: Optional[str] = None) -> RunSingleConfig:
    """
    Load agent configuration from the database or YAML files.
    
    Args:
        config_name: Name of the configuration to load. If None, the default configuration is loaded.
        
    Returns:
        RunSingleConfig: The loaded configuration.
    """
    if config_name:
        try:
            config = AgentConfig.objects.get(name=config_name)
            return RunSingleConfig.model_validate(**config.raw_config)
        except AgentConfig.DoesNotExist:
            pass
    
    try:
        config = AgentConfig.objects.get(is_default=True)
        return RunSingleConfig.model_validate(**config.raw_config)
    except AgentConfig.DoesNotExist:
        pass
    
    import yaml
    config = yaml.safe_load(
        Path(CONFIG_DIR / "default_from_url.yaml").read_text()
    )
    return RunSingleConfig.model_validate(**config)


def create_agent_runtime(config_name: Optional[str] = None) -> DjangoAgentRuntime:
    """
    Create a Django agent runtime with the specified configuration.
    
    Args:
        config_name: Name of the configuration to load. If None, the default configuration is loaded.
        
    Returns:
        DjangoAgentRuntime: The created runtime.
    """
    config_obj = load_agent_config(config_name)
    
    runtime_config = RuntimeConfig(
        model_name=config_obj.agent.model.model_name,
        temperature=getattr(config_obj.agent.model, 'temperature', 0.0),
        top_p=getattr(config_obj.agent.model, 'top_p', 1.0),
        cost_limit=getattr(config_obj.agent.model, 'per_instance_cost_limit', 3.0),
    )
    
    runtime = DjangoAgentRuntime(runtime_config)
    runtime.initialize()
    
    return runtime
