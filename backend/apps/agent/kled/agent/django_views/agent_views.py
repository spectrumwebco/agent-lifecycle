"""
Django views for the agent API.

This module provides Django views for the agent API, converting
the Flask routes from the original implementation to Django views.
"""

import json
import sys
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

import yaml
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async

from apps.agent.kled.agent import CONFIG_DIR, PACKAGE_DIR
from apps.agent.kled.agent.agent.problem_statement import problem_statement_from_simplified_input
from apps.agent.kled.agent.environment.repo import repo_from_simplified_input
from apps.agent.kled.agent.django_models.agent_models import AgentModel, AgentRun, AgentSession, AgentThread, AgentStats

sys.path.append(str(PACKAGE_DIR.parent))
from apps.agent.kled.agent.run.run_single import RunSingle, RunSingleConfig


AGENT_THREADS = {}


class WebSocketUpdate:
    """Class for sending updates via WebSocket."""
    
    def __init__(self, channel_layer, group_name):
        self.channel_layer = channel_layer
        self.group_name = group_name
        self.log_buffer = []
    
    async def send_update(self, update_type, data):
        """Send an update via WebSocket."""
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'send_message',
                'message': {
                    'type': update_type,
                    'data': data
                }
            }
        )
    
    async def up_log(self, message):
        """Send a log message."""
        self.log_buffer.append(message)
        await self.send_update('log', message)
    
    async def up_agent(self, message):
        """Send an agent message."""
        await self.send_update('agent', message)
    
    async def up_banner(self, message):
        """Send a banner message."""
        await self.send_update('banner', message)
    
    async def finish_run(self):
        """Mark the run as finished."""
        await self.send_update('finish', {})


class AgentWebsocketConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for agent communication."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'agent_{self.session_id}'
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        session, created = await sync_to_async(AgentSession.objects.get_or_create)(
            id=self.session_id
        )
        
        await self.accept()
        
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': 'Connected to agent WebSocket',
            'session_id': str(self.session_id)
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle received WebSocket messages."""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'stop':
            thread_id = data.get('thread_id')
            if thread_id in AGENT_THREADS:
                thread = AGENT_THREADS[thread_id]
                await sync_to_async(thread.stop)()
                await self.send(text_data=json.dumps({
                    'type': 'stop',
                    'message': 'Agent thread stopped',
                    'thread_id': thread_id
                }))
        
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'send_message',
                'message': data
            }
        )
    
    async def send_message(self, event):
        """Send message to WebSocket."""
        message = event['message']
        await self.send(text_data=json.dumps(message))


class AgentThread:
    """Thread for running the agent."""
    
    def __init__(self, thread_id, config, websocket_update):
        self.thread_id = thread_id
        self.config = config
        self.websocket_update = websocket_update
        self.is_running = False
        self.agent_run = None
    
    async def run(self):
        """Run the agent."""
        self.is_running = True
        
        try:
            stats = await sync_to_async(AgentStats.objects.create)()
            
            agent_model, _ = await sync_to_async(AgentModel.objects.get_or_create)(
                name=self.config.agent.model.model_name,
                defaults={
                    'temperature': getattr(self.config.agent.model, 'temperature', 0.0),
                    'top_p': getattr(self.config.agent.model, 'top_p', 1.0),
                    'per_instance_cost_limit': getattr(self.config.agent.model, 'per_instance_cost_limit', 3.0),
                    'total_cost_limit': getattr(self.config.agent.model, 'total_cost_limit', 0.0),
                    'per_instance_call_limit': getattr(self.config.agent.model, 'per_instance_call_limit', 0),
                }
            )
            
            self.agent_run = await sync_to_async(AgentRun.objects.create)(
                agent_model=agent_model,
                stats=stats
            )
            
            await self.websocket_update.up_agent("Starting the agent run")
            
            def run_agent():
                with redirect_stdout(self.websocket_update.log_buffer):
                    with redirect_stderr(self.websocket_update.log_buffer):
                        try:
                            main = RunSingle.from_config(self.config)
                            
                            
                            result = main.run()
                            
                            self.agent_run.mark_complete(
                                exit_status=result.info.get('exit_status'),
                                submission=result.info.get('submission')
                            )
                            
                            self.agent_run.save_trajectory(result.trajectory)
                            
                            return result
                        except Exception as e:
                            short_msg = str(e)
                            max_len = 350
                            if len(short_msg) > max_len:
                                short_msg = f"{short_msg[:max_len]}... (see log for details)"
                            
                            traceback_str = traceback.format_exc()
                            async_to_sync(self.websocket_update.up_log)(traceback_str)
                            async_to_sync(self.websocket_update.up_agent)(f"Error: {short_msg}")
                            async_to_sync(self.websocket_update.up_banner)("Critical error: " + short_msg)
                            async_to_sync(self.websocket_update.finish_run)()
                            
                            self.agent_run.mark_complete(exit_status="error")
                            
                            raise
            
            import threading
            agent_thread = threading.Thread(target=run_agent)
            agent_thread.start()
            
            while agent_thread.is_alive():
                await sync_to_async(time.sleep)(0.1)
            
            await self.websocket_update.finish_run()
            
        except Exception as e:
            short_msg = str(e)
            traceback_str = traceback.format_exc()
            await self.websocket_update.up_log(traceback_str)
            await self.websocket_update.up_agent(f"Error: {short_msg}")
            await self.websocket_update.up_banner("Critical error: " + short_msg)
            await self.websocket_update.finish_run()
        
        finally:
            self.is_running = False
            if self.thread_id in AGENT_THREADS:
                del AGENT_THREADS[self.thread_id]
    
    def stop(self):
        """Stop the agent thread."""
        self.is_running = False
        if self.agent_run:
            self.agent_run.mark_complete(exit_status="stopped")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def index_view(request):
    """Render the agent index page."""
    return render(request, 'python_agent/agent/index.html')


@csrf_exempt
@require_http_methods(["POST"])
def run_agent_view(request):
    """Run the agent."""
    try:
        data = json.loads(request.body)
        run_config = data.get('run_config')
        
        if not run_config:
            return JsonResponse({'error': 'Missing run_config'}, status=400)
        
        session_id = data.get('session_id', str(uuid4()))
        
        session, created = AgentSession.objects.get_or_create(
            id=session_id,
            defaults={
                'user_identifier': request.user.username if request.user.is_authenticated else None
            }
        )
        
        for thread_id, thread in list(AGENT_THREADS.items()):
            if hasattr(thread, 'session_id') and thread.session_id == session_id:
                thread.stop()
        
        thread_id = str(uuid4())
        
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        group_name = f'agent_{session_id}'
        websocket_update = WebSocketUpdate(channel_layer, group_name)
        
        model_name = run_config.get('agent', {}).get('model', {}).get('model_name')
        test_run = run_config.get('extra', {}).get('test_run', False)
        
        if test_run:
            model_name = "instant_empty_submit"
        
        default_config = yaml.safe_load(
            Path(CONFIG_DIR / "default_from_url.yaml").read_text()
        )
        
        config = {
            **default_config,
            "agent": {
                "model": {
                    "model_name": model_name,
                },
            },
            "environment": {
                "image_name": run_config.get('environment', {}).get('image_name'),
                "script": run_config.get('environment', {}).get('script'),
            },
        }
        
        config["problem_statement"] = problem_statement_from_simplified_input(
            input=run_config.get('problem_statement', {}).get('input'),
            type=run_config.get('problem_statement', {}).get('type'),
        )
        
        config["environment"]["repo"] = repo_from_simplified_input(
            input=run_config.get('environment', {}).get('repo_path'),
            base_commit=run_config.get('environment', {}).get('base_commit'),
            type="auto",
        )
        
        config_obj = RunSingleConfig.model_validate(**config)
        
        thread = AgentThread(thread_id, config_obj, websocket_update)
        thread.session_id = session_id
        AGENT_THREADS[thread_id] = thread
        
        AgentThread.objects.create(
            id=thread_id,
            session=session
        )
        
        import asyncio
        asyncio.create_task(thread.run())
        
        return JsonResponse({
            'status': 'success',
            'message': 'Agent started',
            'session_id': session_id,
            'thread_id': thread_id
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stop_agent_view(request):
    """Stop the agent."""
    try:
        data = json.loads(request.body)
        thread_id = data.get('thread_id')
        
        if not thread_id:
            return JsonResponse({'error': 'Missing thread_id'}, status=400)
        
        if thread_id in AGENT_THREADS:
            thread = AGENT_THREADS[thread_id]
            thread.stop()
            return JsonResponse({
                'status': 'success',
                'message': 'Agent stopped',
                'thread_id': thread_id
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Thread {thread_id} not found'
            }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def agent_status_view(request, thread_id):
    """Get the status of an agent thread."""
    try:
        if thread_id in AGENT_THREADS:
            thread = AGENT_THREADS[thread_id]
            return JsonResponse({
                'status': 'success',
                'is_running': thread.is_running,
                'thread_id': thread_id
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Thread {thread_id} not found'
            }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
