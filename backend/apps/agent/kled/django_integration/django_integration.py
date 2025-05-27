"""
Django integration for the Kled agent.

This module provides Django integration for the Kled software engineering agent,
connecting the agent loop with Django models and views.
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
from apps.agent.go_integration import get_go_runtime_integration

sys.path.append(str(PACKAGE_DIR.parent))
from apps.agent.kled.agent.run.run_single import RunSingle, RunSingleConfig


class KledAgentRuntime(AbstractRuntime):
    """Django implementation of the Kled agent runtime."""
    
    def __init__(self, config: RuntimeConfig):
        """Initialize the Kled agent runtime."""
        super().__init__(config)
        self.config = config  # Store config explicitly
        self.agent_run = None
        self.agent_thread = None
        self.go_runtime = get_go_runtime_integration()
    
    def initialize(self):
        """Initialize the runtime."""
        stats = AgentStats.objects.create()
        
        agent_model, _ = AgentModel.objects.get_or_create(
            name=self.config.model_name if hasattr(self.config, 'model_name') else "gemini-2.5-pro",
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
            
            if self.agent_run:
                self.agent_run.mark_complete(
                    exit_status=result.info.get('exit_status'),
                    submission=result.info.get('submission')
                )
                
                trajectory_id = self.agent_run.save_trajectory(result.trajectory)
            else:
                trajectory_id = None
            
            self.go_runtime.publish_event(
                event_type="kled_run_completed",
                data={
                    "pr_id": config_obj.environment.repo.pr_id if hasattr(config_obj.environment, 'repo') and hasattr(config_obj.environment.repo, 'pr_id') else None,
                    "repository": config_obj.environment.repo.repo_url if hasattr(config_obj.environment, 'repo') and hasattr(config_obj.environment.repo, 'repo_url') else None,
                    "branch": config_obj.environment.repo.branch if hasattr(config_obj.environment, 'repo') and hasattr(config_obj.environment.repo, 'branch') else None,
                    "status": result.info.get('exit_status'),
                    "submission": result.info.get('submission'),
                    "trajectory_id": trajectory_id
                },
                source="kled",
                metadata={
                    "agent_run_id": self.agent_run.id if self.agent_run else None,
                    "model_name": self.config.model_name if hasattr(self.config, 'model_name') else "gemini-2.5-pro"
                }
            )
            
            return {
                'status': 'success',
                'exit_status': result.info.get('exit_status'),
                'submission': result.info.get('submission'),
                'trajectory_id': trajectory_id
            }
        
        except Exception as e:
            if self.agent_run:
                self.agent_run.mark_complete(exit_status="error")
            
            import traceback
            error_data = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            
            self.go_runtime.publish_event(
                event_type="kled_run_error",
                data={
                    "error": str(e),
                    "traceback": traceback.format_exc()
                },
                source="kled",
                metadata={
                    "agent_run_id": self.agent_run.id if self.agent_run else None
                }
            )
            
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


def create_agent_runtime(config_name: Optional[str] = None) -> KledAgentRuntime:
    """
    Create a Kled agent runtime with the specified configuration.
    
    Args:
        config_name: Name of the configuration to load. If None, the default configuration is loaded.
        
    Returns:
        KledAgentRuntime: The created runtime.
    """
    config_obj = load_agent_config(config_name)
    
    from apps.agent.agent_framework.shared.runtime import LocalRuntimeConfig
    
    runtime_config = LocalRuntimeConfig()
    runtime_config.model_name = config_obj.agent.model.model_name
    runtime_config.temperature = getattr(config_obj.agent.model, 'temperature', 0.0)
    runtime_config.top_p = getattr(config_obj.agent.model, 'top_p', 1.0)
    runtime_config.cost_limit = getattr(config_obj.agent.model, 'per_instance_cost_limit', 3.0)
    
    runtime = KledAgentRuntime(runtime_config)
    runtime.initialize()
    
    return runtime
