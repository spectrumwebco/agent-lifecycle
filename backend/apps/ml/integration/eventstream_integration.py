"""
Integration with the Go eventstream system.

This module provides a Python wrapper for the Go eventstream system,
allowing the ML app to send and receive events through the shared
eventstream infrastructure.
"""

import asyncio
import json
import logging
import time
import os
from typing import Any, Dict, Optional, Callable
import redis
from pydantic import BaseModel, Field

DEFAULT_REDIS_CONFIG = {
    "host": os.environ.get("REDIS_HOST", "localhost"),
    "port": int(os.environ.get("REDIS_PORT", "6379")),
    "db": int(os.environ.get("REDIS_DB", "0")),
    "password": os.environ.get("REDIS_PASSWORD", None),
    "ssl": os.environ.get("REDIS_SSL", "False").lower() == "true",
}


class EventType:
    MESSAGE = "message"
    ACTION = "action"
    OBSERVATION = "observation"
    PLAN = "plan"
    KNOWLEDGE = "knowledge"
    DATASOURCE = "datasource"
    STATE_UPDATE = "state_update"
    CACHE_UPDATE = "cache_update"


class EventSource:
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    MODULE = "module"
    CICD = "ci_cd"
    K8S = "kubernetes"
    SANDBOX = "sandbox"
    ML = "ml"  # New source specific to ML app


class Event(BaseModel):
    """Event model mirroring the Go Event struct."""

    id: str = Field(..., description="Unique event ID")
    type: str = Field(..., description="Event type")
    source: str = Field(..., description="Event source")
    timestamp: str = Field(..., description="Event timestamp")
    data: Any = Field(..., description="Event data payload")
    metadata: Optional[Dict[str, str]] = Field(None, description="Optional metadata")

    @classmethod
    def new(
        cls,
        event_type: str,
        source: str,
        data: Any,
        metadata: Optional[Dict[str, str]] = None,
    ):
        """Create a new event."""
        return cls(
            id=f"{int(time.time() * 1000000)}",
            type=event_type,
            source=source,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
            data=data,
            metadata=metadata or {},
        )


class EventStream:
    """Python client for the Go eventstream."""

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        redis_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the event stream client."""
        self.logger = logging.getLogger("MLEventStream")
        self.subscribers = {}
        self._running = False
        self._listener_task = None

        try:
            from django.conf import settings

            if settings.configured and hasattr(settings, "REDIS_CONFIG"):
                redis_config = settings.REDIS_CONFIG
                self.logger.info("Using Redis configuration from Django settings")
            else:
                self.logger.info(
                    "Django settings not configured, using default Redis configuration"
                )
        except Exception as e:
            self.logger.info(
                f"Django settings error: {e}, using default Redis configuration"
            )

        redis_config = redis_config or DEFAULT_REDIS_CONFIG

        try:
            self.redis_client = redis_client or redis.Redis(
                host=redis_config.get("host", "localhost"),
                port=redis_config.get("port", 6379),
                db=redis_config.get("db", 0),
                password=redis_config.get("password", None),
                ssl=redis_config.get("ssl", False),
                decode_responses=True,
                socket_connect_timeout=2.0,
            )
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe("eventstream:events")
            self.redis_available = True
            self.logger.info("Redis connection established")
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            self.logger.warning(
                f"Redis connection failed: {e}. Running in local-only mode."
            )
            self.redis_available = False
            self.redis_client = None
            self.pubsub = None

    async def start(self):
        """Start listening for events."""
        if self._running:
            return

        self._running = True
        self._listener_task = asyncio.create_task(self._listen_for_events())
        self.logger.info("Event stream listener started")

    async def stop(self):
        """Stop listening for events."""
        if not self._running:
            return

        self._running = False
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Event stream listener stopped")

    async def publish(self, event: Event) -> bool:
        """Publish an event to the stream."""
        event_key = f"event:{event.id}"
        event_json = event.model_dump_json()

        # Handle local-only mode
        if not self.redis_available or self.redis_client is None:
            self.logger.info(
                f"Local mode: Event {event.id} (Type: {event.type}, Source: {event.source})"
            )
            self._process_event(event)
            return True

        try:
            self.redis_client.set(event_key, event_json, ex=86400)  # 24 hours TTL
            self.redis_client.publish("eventstream:events", event_json)

            self.logger.info(
                f"Published event: {event.id} (Type: {event.type}, Source: {event.source})"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error publishing event: {e}")
            self._process_event(event)
            return False

    def subscribe(self, event_type: str, callback: Callable[[Event], None]):
        """Subscribe to events of a specific type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        self.logger.info(f"New subscriber for event type: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable[[Event], None]):
        """Unsubscribe from events of a specific type."""
        if event_type in self.subscribers:
            self.subscribers[event_type] = [
                cb for cb in self.subscribers[event_type] if cb != callback
            ]
            self.logger.info(f"Unsubscribed callback for event type: {event_type}")

    async def _listen_for_events(self):
        """Listen for events from Redis."""
        if not self.redis_available or self.pubsub is None:
            self.logger.info(
                "Redis not available, event listener running in local-only mode"
            )
            while self._running:
                await asyncio.sleep(1)  # Just sleep in local-only mode
            return

        while self._running:
            try:
                message = self.pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "message":
                    data = message["data"]
                    try:
                        event_data = json.loads(data)
                        event = Event(**event_data)
                        self._process_event(event)
                    except json.JSONDecodeError:
                        self.logger.error(f"Error decoding JSON from message: {data}")
                    except Exception as e:
                        self.logger.error(f"Error processing event: {e}")
                await asyncio.sleep(0.01)  # Small delay to avoid CPU spinning
            except Exception as e:
                self.logger.error(f"Error in event listener: {e}")
                await asyncio.sleep(1)  # Longer delay on error

    def _process_event(self, event: Event):
        """Process a received event."""
        self.logger.info(
            f"Received event: {event.id} (Type: {event.type}, Source: {event.source})"
        )

        if event.type in self.subscribers:
            for callback in self.subscribers[event.type]:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Error in event callback: {e}")

    async def get_app_context(self, key: str) -> Optional[str]:
        """Get application context from the event stream cache."""
        if not self.redis_available or self.redis_client is None:
            self.logger.warning(
                f"Redis not available, cannot get context for key: {key}"
            )
            return None

        cache_key = f"context:{key}"
        try:
            value = self.redis_client.get(cache_key)
            return value
        except Exception as e:
            self.logger.error(f"Error getting context for key {key}: {e}")
            return None

    async def set_app_context(
        self, key: str, value: str, expiration: int = 3600
    ) -> bool:
        """Set application context in the event stream cache."""
        if not self.redis_available or self.redis_client is None:
            self.logger.warning(
                f"Redis not available, cannot set context for key: {key}"
            )
            return False

        cache_key = f"context:{key}"
        try:
            self.redis_client.set(cache_key, value, ex=expiration)
            return True
        except Exception as e:
            self.logger.error(f"Error setting context: {e}")
            return False


event_stream = EventStream()
