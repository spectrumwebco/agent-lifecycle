"""
Django-integrated server for the agent.

This module provides a Django-integrated server for the agent, replacing
the Flask server from the original implementation.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.agent.kled.agent import CONFIG_DIR, PACKAGE_DIR
from apps.agent.kled.agent.django_integration import (
    load_agent_config, create_agent_runtime, DjangoAgentRuntime
)
from apps.agent.kled.agent.django_models.agent_models import (
    AgentModel, AgentRun, AgentStats, AgentSession, AgentThread
)
from apps.agent.kled.agent.django_models.config_models import (
    AgentConfig, ToolConfig, ProblemStatement, EnvironmentConfig
)

from apps.agent.agent_framework.shared.runtime import RuntimeConfig, AbstractRuntime

sys.path.append(str(PACKAGE_DIR.parent))
from apps.agent.kled.agent.run.run_single import RunSingle, RunSingleConfig


def run_agent(config_name: Optional[str] = None, 
              problem_statement: Optional[Dict[str, Any]] = None,
              repo_path: Optional[str] = None,
              model_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the agent with the specified configuration.
    
    Args:
        config_name: Name of the configuration to load. If None, the default configuration is loaded.
        problem_statement: Problem statement to use. If None, the problem statement from the configuration is used.
        repo_path: Repository path to use. If None, the repository path from the configuration is used.
        model_name: Model name to use. If None, the model name from the configuration is used.
        
    Returns:
        Dict[str, Any]: The result of running the agent.
    """
    try:
        config_obj = load_agent_config(config_name)
        
        if problem_statement:
            from apps.agent.kled.agent.agent.problem_statement import problem_statement_from_simplified_input
            config_obj.problem_statement = problem_statement_from_simplified_input(
                input=problem_statement.get("input"),
                type=problem_statement.get("type", "text"),
            )
        
        if repo_path:
            from apps.agent.kled.agent.environment.repo import repo_from_simplified_input
            if "environment" not in config_obj.model_fields_set:
                config_obj.environment = {}
            
            config_obj.environment.repo = repo_from_simplified_input(
                input=repo_path,
                type="auto",
            )
        
        if model_name:
            if "agent" not in config_obj.model_fields_set:
                config_obj.agent = {}
            
            if "model" not in config_obj.agent.model_fields_set:
                config_obj.agent.model = {}
            
            config_obj.agent.model.model_name = model_name
        
        runtime = create_agent_runtime(config_name)
        
        result = runtime.run_agent(config_obj)
        
        runtime.cleanup()
        
        return result
    
    except Exception as e:
        import traceback
        return {
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }


def stop_agent(thread_id: str) -> Dict[str, Any]:
    """
    Stop a running agent thread.
    
    Args:
        thread_id: ID of the thread to stop.
        
    Returns:
        Dict[str, Any]: The result of stopping the agent.
    """
    try:
        from apps.agent.kled.agent.django_views.agent_views import AGENT_THREADS
        
        if thread_id in AGENT_THREADS:
            thread = AGENT_THREADS[thread_id]
            thread.stop()
            
            return {
                'status': 'success',
                'message': f'Thread {thread_id} stopped'
            }
        else:
            return {
                'status': 'error',
                'message': f'Thread {thread_id} not found'
            }
    
    except Exception as e:
        import traceback
        return {
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }


def get_agent_status(thread_id: str) -> Dict[str, Any]:
    """
    Get the status of a running agent thread.
    
    Args:
        thread_id: ID of the thread to get the status of.
        
    Returns:
        Dict[str, Any]: The status of the agent.
    """
    try:
        from apps.agent.kled.agent.django_views.agent_views import AGENT_THREADS
        
        if thread_id in AGENT_THREADS:
            thread = AGENT_THREADS[thread_id]
            
            return {
                'status': 'success',
                'is_running': thread.is_running,
                'thread_id': thread_id
            }
        else:
            try:
                thread = AgentThread.objects.get(id=thread_id)
                
                agent_run = thread.agent_run
                
                return {
                    'status': 'success',
                    'is_running': False,
                    'is_active': thread.is_active,
                    'thread_id': thread_id,
                    'run': {
                        'id': str(agent_run.id),
                        'started_at': agent_run.started_at.isoformat(),
                        'completed_at': agent_run.completed_at.isoformat() if agent_run.completed_at else None,
                        'exit_status': agent_run.exit_status,
                        'submission': agent_run.submission,
                    }
                }
            
            except AgentThread.DoesNotExist:
                return {
                    'status': 'error',
                    'message': f'Thread {thread_id} not found'
                }
    
    except Exception as e:
        import traceback
        return {
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }


def list_agent_configs() -> Dict[str, Any]:
    """
    List all available agent configurations.
    
    Returns:
        Dict[str, Any]: The list of agent configurations.
    """
    try:
        configs = AgentConfig.objects.all()
        
        return {
            'status': 'success',
            'configs': [
                {
                    'name': config.name,
                    'description': config.description,
                    'model_name': config.model_name,
                    'is_default': config.is_default,
                }
                for config in configs
            ]
        }
    
    except Exception as e:
        import traceback
        return {
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }


def get_agent_config(config_name: str) -> Dict[str, Any]:
    """
    Get an agent configuration.
    
    Args:
        config_name: Name of the configuration to get.
        
    Returns:
        Dict[str, Any]: The agent configuration.
    """
    try:
        try:
            config = AgentConfig.objects.get(name=config_name)
        except AgentConfig.DoesNotExist:
            return {
                'status': 'error',
                'message': f'Configuration {config_name} not found'
            }
        
        return {
            'status': 'success',
            'config': {
                'name': config.name,
                'description': config.description,
                'model_name': config.model_name,
                'temperature': config.temperature,
                'top_p': config.top_p,
                'per_instance_cost_limit': config.per_instance_cost_limit,
                'total_cost_limit': config.total_cost_limit,
                'per_instance_call_limit': config.per_instance_call_limit,
                'use_function_calling': config.use_function_calling,
                'submit_command': config.submit_command,
                'is_default': config.is_default,
                'raw_config': config.raw_config,
            }
        }
    
    except Exception as e:
        import traceback
        return {
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }
