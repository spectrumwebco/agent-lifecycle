"""
WebSocket consumers for the agent API.

This module provides WebSocket consumers for the agent API, enabling
real-time communication with the agent.
"""

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from apps.agent.kled.agent.django_models.agent_models import AgentSession, AgentThread


class AgentConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for agent communication."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.group_name = f'agent_{self.thread_id}'
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': 'Connected to agent WebSocket',
            'thread_id': self.thread_id
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
            from apps.agent.agent.django_views.agent_views import AGENT_THREADS
            
            if self.thread_id in AGENT_THREADS:
                thread = AGENT_THREADS[self.thread_id]
                await database_sync_to_async(thread.stop)()
                
                await self.send(text_data=json.dumps({
                    'type': 'stop',
                    'message': 'Agent thread stopped',
                    'thread_id': self.thread_id
                }))
        
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'agent_message',
                'message': data
            }
        )
    
    async def agent_message(self, event):
        """Send agent message to WebSocket."""
        message = event['message']
        
        await self.send(text_data=json.dumps(message))
