"""
Django integration for the Veigar cybersecurity agent.

This module provides Django integration for the Veigar agent, connecting
the security review system with Django models and views for PR vulnerability scanning.
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

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from apps.agent.veigar.agent.security_reviewer import SecurityReviewer, SecurityReviewConfig


class VeigarSecurityRuntime(AbstractRuntime):
    """Django implementation of the Veigar security runtime."""
    
    def __init__(self, config: RuntimeConfig):
        """Initialize the Veigar security runtime."""
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
            stats=stats,
            agent_type="veigar"  # Specify this is a Veigar security agent run
        )
        
        self.agent_thread = AgentThread.objects.create(
            session=AgentSession.objects.create()
        )
        
        if not self.go_runtime.connected:
            self.go_runtime.connect()
        
        return True
    
    def run_security_review(self, config_obj: SecurityReviewConfig, pr_data: Dict[str, Any]):
        """
        Run the security review with the specified configuration.
        
        Args:
            config_obj: The security review configuration
            pr_data: Pull request data including repository, branch, and files
            
        Returns:
            Dict: The security review results
        """
        try:
            from apps.agent.veigar.agent.veigar_agent import VeigarAgent, CodeReviewConfig
            
            veigar_agent = VeigarAgent(config_obj, CodeReviewConfig())
            result = veigar_agent.review_pr(pr_data)
            
            if self.agent_run:
                self.agent_run.mark_complete(
                    exit_status=result.severity_level if result.severity_level in ["none", "low"] else "rejected",
                    submission=f"{result.security_report}\n\n{result.code_review_report}"
                )
                
                security_trajectory = result.info.get("security", {}).get("trajectory")
                if security_trajectory:
                    trajectory_id = self.agent_run.save_trajectory(security_trajectory)
                else:
                    trajectory_id = None
            else:
                trajectory_id = None
            
            self.go_runtime.publish_event(
                event_type="veigar_review_completed",
                data={
                    "pr_id": pr_data.get("pr_id"),
                    "repository": pr_data.get("repository"),
                    "branch": pr_data.get("branch"),
                    "status": result.severity_level,
                    "security_report": result.security_report,
                    "code_review_report": result.code_review_report,
                    "trajectory_id": trajectory_id
                },
                source="veigar",
                metadata={
                    "agent_run_id": self.agent_run.id if self.agent_run else None,
                    "severity_level": result.severity_level
                }
            )
            
            return {
                'status': 'success',
                'exit_status': result.severity_level if result.severity_level in ["none", "low"] else "rejected",
                'security_report': result.security_report,
                'code_review_report': result.code_review_report,
                'severity_level': result.severity_level,
                'trajectory_id': trajectory_id
            }
        
        except Exception as e:
            if self.agent_run:
                self.agent_run.mark_complete(exit_status="error")
            
            import traceback
            error_data = {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            
            self.go_runtime.publish_event(
                event_type="security_review_error",
                data={
                    "pr_id": pr_data.get("pr_id"),
                    "repository": pr_data.get("repository"),
                    "error": str(e)
                },
                source="veigar",
                metadata={
                    "agent_run_id": self.agent_run.id if self.agent_run else None
                }
            )
            
            return error_data
    
    def cleanup(self):
        """Clean up the runtime."""
        return True


def load_security_config(config_name: Optional[str] = None) -> SecurityReviewConfig:
    """
    Load security review configuration from the database or YAML files.
    
    Args:
        config_name: Name of the configuration to load. If None, the default configuration is loaded.
        
    Returns:
        SecurityReviewConfig: The loaded configuration.
    """
    if config_name:
        try:
            config = AgentConfig.objects.get(name=config_name)
            return SecurityReviewConfig.model_validate(**config.raw_config)
        except AgentConfig.DoesNotExist:
            pass
    
    try:
        config = AgentConfig.objects.get(name="veigar_security", is_default=False)
        return SecurityReviewConfig.model_validate(**config.raw_config)
    except AgentConfig.DoesNotExist:
        pass
    
    import yaml
    config = yaml.safe_load(
        Path(CONFIG_DIR / "veigar_security_config.yaml").read_text()
    )
    return SecurityReviewConfig.model_validate(**config)


def create_security_runtime(config_name: Optional[str] = None) -> VeigarSecurityRuntime:
    """
    Create a Veigar security runtime with the specified configuration.
    
    Args:
        config_name: Name of the configuration to load. If None, the default configuration is loaded.
        
    Returns:
        VeigarSecurityRuntime: The created runtime.
    """
    config_obj = load_security_config(config_name)
    
    from apps.agent.agent_framework.shared.runtime import LocalRuntimeConfig
    
    runtime_config = LocalRuntimeConfig()
    
    runtime = VeigarSecurityRuntime(runtime_config)
    runtime.initialize()
    
    return runtime
