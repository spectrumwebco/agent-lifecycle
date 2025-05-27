"""
Django management command for running the agent.

This module provides a Django management command for running the agent,
converting the CLI functionality from the original implementation.
"""

import json
import os
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.agent.kled.agent import CONFIG_DIR, PACKAGE_DIR
from apps.agent.kled.agent.agent.problem_statement import problem_statement_from_simplified_input
from apps.agent.kled.agent.environment.repo import repo_from_simplified_input
from apps.agent.kled.agent.django_models.agent_models import AgentModel, AgentRun, AgentStats

sys.path.append(str(PACKAGE_DIR.parent))
from apps.agent.kled.agent.run.run_single import RunSingle, RunSingleConfig


class Command(BaseCommand):
    help = 'Run the agent with the specified configuration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--config',
            type=str,
            help='Path to the configuration file',
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Model name to use',
        )
        parser.add_argument(
            '--problem',
            type=str,
            help='Problem statement input',
        )
        parser.add_argument(
            '--problem-type',
            type=str,
            default='text',
            choices=['text', 'file', 'url'],
            help='Type of problem statement input',
        )
        parser.add_argument(
            '--repo',
            type=str,
            help='Repository path or URL',
        )
        parser.add_argument(
            '--base-commit',
            type=str,
            help='Base commit for the repository',
        )
        parser.add_argument(
            '--repo-type',
            type=str,
            default='auto',
            choices=['auto', 'local', 'git'],
            help='Type of repository',
        )
        parser.add_argument(
            '--image',
            type=str,
            help='Docker image name',
        )
        parser.add_argument(
            '--script',
            type=str,
            help='Script to run in the environment',
        )
        parser.add_argument(
            '--test-run',
            action='store_true',
            help='Run in test mode (uses instant_empty_submit model)',
        )
    
    def handle(self, *args, **options):
        try:
            config_path = options.get('config')
            if config_path:
                config_path = Path(config_path)
                if not config_path.exists():
                    raise CommandError(f"Configuration file {config_path} does not exist")
                
                with open(config_path, 'r') as f:
                    if config_path.suffix == '.json':
                        config = json.load(f)
                    elif config_path.suffix in ['.yaml', '.yml']:
                        import yaml
                        config = yaml.safe_load(f)
                    else:
                        raise CommandError(f"Unsupported configuration file format: {config_path.suffix}")
            else:
                import yaml
                config = yaml.safe_load(
                    Path(CONFIG_DIR / "default_from_url.yaml").read_text()
                )
            
            model_name = options.get('model')
            test_run = options.get('test_run', False)
            
            if test_run:
                model_name = "instant_empty_submit"
            
            if model_name:
                if "agent" not in config:
                    config["agent"] = {}
                if "model" not in config["agent"]:
                    config["agent"]["model"] = {}
                config["agent"]["model"]["model_name"] = model_name
            
            image_name = options.get('image')
            script = options.get('script')
            
            if image_name or script:
                if "environment" not in config:
                    config["environment"] = {}
                
                if image_name:
                    config["environment"]["image_name"] = image_name
                
                if script:
                    config["environment"]["script"] = script
            
            problem_input = options.get('problem')
            problem_type = options.get('problem_type')
            
            if problem_input:
                config["problem_statement"] = problem_statement_from_simplified_input(
                    input=problem_input,
                    type=problem_type,
                )
            
            repo_input = options.get('repo')
            base_commit = options.get('base_commit')
            repo_type = options.get('repo_type')
            
            if repo_input:
                if "environment" not in config:
                    config["environment"] = {}
                
                config["environment"]["repo"] = repo_from_simplified_input(
                    input=repo_input,
                    base_commit=base_commit,
                    type=repo_type,
                )
            
            config_obj = RunSingleConfig.model_validate(**config)
            
            stats = AgentStats.objects.create()
            
            agent_model, _ = AgentModel.objects.get_or_create(
                name=config_obj.agent.model.model_name,
                defaults={
                    'temperature': getattr(config_obj.agent.model, 'temperature', 0.0),
                    'top_p': getattr(config_obj.agent.model, 'top_p', 1.0),
                    'per_instance_cost_limit': getattr(config_obj.agent.model, 'per_instance_cost_limit', 3.0),
                    'total_cost_limit': getattr(config_obj.agent.model, 'total_cost_limit', 0.0),
                    'per_instance_call_limit': getattr(config_obj.agent.model, 'per_instance_call_limit', 0),
                }
            )
            
            agent_run = AgentRun.objects.create(
                agent_model=agent_model,
                stats=stats
            )
            
            self.stdout.write(self.style.SUCCESS("Starting the agent run"))
            
            try:
                main = RunSingle.from_config(config_obj)
                result = main.run()
                
                agent_run.mark_complete(
                    exit_status=result.info.get('exit_status'),
                    submission=result.info.get('submission')
                )
                
                trajectory_id = agent_run.save_trajectory(result.trajectory)
                
                self.stdout.write(self.style.SUCCESS(f"Agent run completed successfully"))
                self.stdout.write(f"Trajectory saved as: {trajectory_id}")
                
                if result.info.get('submission'):
                    self.stdout.write(f"Submission: {result.info.get('submission')}")
                
                return result
            
            except Exception as e:
                agent_run.mark_complete(exit_status="error")
                
                self.stdout.write(self.style.ERROR(f"Error running agent: {str(e)}"))
                import traceback
                self.stdout.write(traceback.format_exc())
                
                raise CommandError(str(e))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())
            
            raise CommandError(str(e))
