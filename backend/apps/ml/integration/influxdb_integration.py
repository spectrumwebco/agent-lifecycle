"""
Integration with the InfluxDB agent context system.

This module provides a Python wrapper for the InfluxDB agent context system,
allowing the ML app to send and receive context data.
"""

import os
import time
import logging
import socket
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum

try:
    import influxdb_client
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    logging.warning("InfluxDB client not available. Install with 'pip install influxdb-client'")

DEFAULT_INFLUXDB_CONFIG = {
    "url": os.environ.get("INFLUXDB_URL", "http://localhost:8086"),
    "token": os.environ.get("INFLUXDB_TOKEN", ""),
    "org": os.environ.get("INFLUXDB_ORG", "spectrumwebco"),
    "bucket": os.environ.get("INFLUXDB_BUCKET", "agent_context"),
}


class ContextType(str, Enum):
    """Enum for context types."""
    APP = "app"
    ORG = "org"
    SESSION = "session"


class ContextClient:
    """Client for the InfluxDB agent context system."""

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        org: Optional[str] = None,
        bucket: Optional[str] = None,
        measurement: str = "agent_context",
    ):
        """Initialize the context client."""
        self.logger = logging.getLogger("MLContextClient")
        
        try:
            from django.conf import settings

            if settings.configured and hasattr(settings, "INFLUXDB_CONFIG"):
                config = settings.INFLUXDB_CONFIG
                self.logger.info("Using InfluxDB configuration from Django settings")
            else:
                config = DEFAULT_INFLUXDB_CONFIG
                self.logger.info(
                    "Django settings not configured, using default InfluxDB configuration"
                )
        except ImportError:
            self.logger.info("Django not available, using default InfluxDB configuration")
            config = DEFAULT_INFLUXDB_CONFIG
        except Exception as e:
            self.logger.info(
                f"Django settings error: {e}, using default InfluxDB configuration"
            )
            config = DEFAULT_INFLUXDB_CONFIG

        self.url = url or config.get("url")
        self.token = token or config.get("token")
        self.org = org or config.get("org")
        self.bucket = bucket or config.get("bucket")
        self.measurement = measurement
        self.hostname = socket.gethostname()

        if not INFLUXDB_AVAILABLE:
            self.logger.warning("InfluxDB client not available. Running in local-only mode.")
            self.influxdb_available = False
            self.client = None
            self.write_api = None
            self.query_api = None
            return

        try:
            self.client = influxdb_client.InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org,
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            self.influxdb_available = True
            self.logger.info("InfluxDB connection established")
        except Exception as e:
            self.logger.warning(
                f"InfluxDB connection failed: {e}. Running in local-only mode."
            )
            self.influxdb_available = False
            self.client = None
            self.write_api = None
            self.query_api = None

    def close(self):
        """Close the InfluxDB client."""
        if self.client:
            self.client.close()

    def write_event(
        self,
        context_type: Union[ContextType, str],
        tags: Dict[str, str],
        fields: Dict[str, Any],
    ) -> bool:
        """Write an event to InfluxDB."""
        if isinstance(context_type, ContextType):
            context_type = context_type.value

        if not self.influxdb_available or not self.write_api:
            self.logger.info(
                f"Local mode: Event for context type {context_type}"
            )
            return True

        try:
            point = influxdb_client.Point(self.measurement)
            point.tag("context_type", context_type)
            point.tag("host", self.hostname)
            
            for k, v in tags.items():
                if v is not None:
                    point.tag(k, str(v))
            
            for k, v in fields.items():
                if isinstance(v, (int, float)):
                    point.field(k, v)
                elif isinstance(v, bool):
                    point.field(k, v)
                elif isinstance(v, (str, bytes)):
                    point.field(k, str(v))
                elif v is None:
                    continue
                else:
                    point.field(k, str(v))

            self.write_api.write(bucket=self.bucket, record=point)
            self.logger.info(f"Wrote event to InfluxDB for context type {context_type}")
            return True
        except Exception as e:
            self.logger.error(f"Error writing event to InfluxDB: {e}")
            return False

    def query_events(
        self,
        context_type: Union[ContextType, str],
        start: datetime,
        stop: datetime,
        filter_dict: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Query events from InfluxDB."""
        if isinstance(context_type, ContextType):
            context_type = context_type.value

        if not self.influxdb_available or not self.query_api:
            self.logger.warning(
                f"InfluxDB not available, cannot query events for context type {context_type}"
            )
            return []

        try:
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {start.isoformat()}, stop: {stop.isoformat()})
                |> filter(fn: (r) => r._measurement == "{self.measurement}")
                |> filter(fn: (r) => r.context_type == "{context_type}")
            '''

            for k, v in filter_dict.items():
                query += f'|> filter(fn: (r) => r.{k} == "{v}")'

            tables = self.query_api.query(query, org=self.org)
            
            events = []
            for table in tables:
                for record in table.records:
                    event = {
                        "time": record.get_time(),
                        "value": record.get_value(),
                    }
                    for k, v in record.values.items():
                        event[k] = v
                    events.append(event)
            
            return events
        except Exception as e:
            self.logger.error(f"Error querying events from InfluxDB: {e}")
            return []


class AppContextTracker:
    """Tracker for application-level context."""

    def __init__(self, client: ContextClient, app_id: str):
        """Initialize the app context tracker."""
        self.client = client
        self.app_id = app_id
        self.logger = logging.getLogger("AppContextTracker")

    def track_event(
        self, 
        event_type: str, 
        source: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Track an event in the app context."""
        tags = {
            "app_id": self.app_id,
            "event_type": event_type,
            "source": source,
        }

        return self.client.write_event(ContextType.APP, tags, data)

    def track_ci_event(
        self, 
        pipeline: str, 
        status: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Track a CI/CD event in the app context."""
        tags = {
            "app_id": self.app_id,
            "pipeline": pipeline,
            "status": status,
        }

        return self.client.write_event(ContextType.APP, tags, data)

    def track_deployment_event(
        self, 
        environment: str, 
        status: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Track a deployment event in the app context."""
        tags = {
            "app_id": self.app_id,
            "environment": environment,
            "status": status,
        }

        return self.client.write_event(ContextType.APP, tags, data)

    def get_events(
        self, 
        start: datetime, 
        stop: datetime, 
        filter_dict: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        """Get events from the app context."""
        if filter_dict is None:
            filter_dict = {}

        base_filter = {
            "app_id": self.app_id,
        }

        for k, v in filter_dict.items():
            base_filter[k] = v

        return self.client.query_events(ContextType.APP, start, stop, base_filter)


class OrgContextTracker:
    """Tracker for GitHub organization-level context."""

    def __init__(self, client: ContextClient, org_id: str):
        """Initialize the org context tracker."""
        self.client = client
        self.org_id = org_id
        self.logger = logging.getLogger("OrgContextTracker")

    def track_event(
        self, 
        event_type: str, 
        source: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Track an event in the org context."""
        tags = {
            "org_id": self.org_id,
            "event_type": event_type,
            "source": source,
        }

        return self.client.write_event(ContextType.ORG, tags, data)

    def track_repository_event(
        self, 
        repo: str, 
        action: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Track a repository event in the org context."""
        tags = {
            "org_id": self.org_id,
            "repo": repo,
            "action": action,
        }

        return self.client.write_event(ContextType.ORG, tags, data)

    def track_issue_event(
        self, 
        repo: str, 
        issue_id: str, 
        action: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Track an issue event in the org context."""
        tags = {
            "org_id": self.org_id,
            "repo": repo,
            "issue_id": issue_id,
            "action": action,
        }

        return self.client.write_event(ContextType.ORG, tags, data)

    def track_pr_event(
        self, 
        repo: str, 
        pr_id: str, 
        action: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Track a pull request event in the org context."""
        tags = {
            "org_id": self.org_id,
            "repo": repo,
            "pr_id": pr_id,
            "action": action,
        }

        return self.client.write_event(ContextType.ORG, tags, data)

    def get_events(
        self, 
        start: datetime, 
        stop: datetime, 
        filter_dict: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        """Get events from the org context."""
        if filter_dict is None:
            filter_dict = {}

        base_filter = {
            "org_id": self.org_id,
        }

        for k, v in filter_dict.items():
            base_filter[k] = v

        return self.client.query_events(ContextType.ORG, start, stop, base_filter)


class SessionContextTracker:
    """Tracker for session-level context."""

    def __init__(self, client: ContextClient, session_id: str):
        """Initialize the session context tracker."""
        self.client = client
        self.session_id = session_id
        self.logger = logging.getLogger("SessionContextTracker")

    def track_event(
        self, 
        event_type: str, 
        source: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Track an event in the session context."""
        tags = {
            "session_id": self.session_id,
            "event_type": event_type,
            "source": source,
        }

        return self.client.write_event(ContextType.SESSION, tags, data)

    def track_agent_event(
        self, 
        agent_id: str, 
        action: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Track an agent event in the session context."""
        tags = {
            "session_id": self.session_id,
            "agent_id": agent_id,
            "action": action,
        }

        return self.client.write_event(ContextType.SESSION, tags, data)

    def track_tool_event(
        self, 
        tool_name: str, 
        action: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Track a tool event in the session context."""
        tags = {
            "session_id": self.session_id,
            "tool_name": tool_name,
            "action": action,
        }

        return self.client.write_event(ContextType.SESSION, tags, data)

    def track_state_event(
        self, 
        state_type: str, 
        action: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Track a state event in the session context."""
        tags = {
            "session_id": self.session_id,
            "state_type": state_type,
            "action": action,
        }

        return self.client.write_event(ContextType.SESSION, tags, data)

    def get_events(
        self, 
        start: datetime, 
        stop: datetime, 
        filter_dict: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        """Get events from the session context."""
        if filter_dict is None:
            filter_dict = {}

        base_filter = {
            "session_id": self.session_id,
        }

        for k, v in filter_dict.items():
            base_filter[k] = v

        return self.client.query_events(ContextType.SESSION, start, stop, base_filter)


class ContextManager:
    """Manager for all agent contexts."""

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        org: Optional[str] = None,
        bucket: Optional[str] = None,
    ):
        """Initialize the context manager."""
        self.client = ContextClient(url, token, org, bucket)
        self.app_tracker = None
        self.org_trackers = {}
        self.session_trackers = {}
        self.logger = logging.getLogger("ContextManager")

    def close(self):
        """Close the context manager and release resources."""
        if self.client:
            self.client.close()

    def set_app_context(self, app_id: str):
        """Set the application context."""
        self.app_tracker = AppContextTracker(self.client, app_id)

    def get_app_context(self) -> Optional[AppContextTracker]:
        """Get the application context."""
        return self.app_tracker

    def get_org_context(self, org_id: str) -> OrgContextTracker:
        """Get or create an organization context."""
        if org_id not in self.org_trackers:
            self.org_trackers[org_id] = OrgContextTracker(self.client, org_id)
        return self.org_trackers[org_id]

    def get_session_context(self, session_id: str) -> SessionContextTracker:
        """Get or create a session context."""
        if session_id not in self.session_trackers:
            self.session_trackers[session_id] = SessionContextTracker(self.client, session_id)
        return self.session_trackers[session_id]

    def track_event_to_all_contexts(
        self,
        event_type: str,
        source: str,
        org_id: Optional[str],
        session_id: Optional[str],
        data: Dict[str, Any],
    ) -> bool:
        """Track an event to all relevant contexts."""
        success = True

        if self.app_tracker:
            if not self.app_tracker.track_event(event_type, source, data):
                self.logger.error("Failed to track event to app context")
                success = False

        if org_id:
            org_tracker = self.get_org_context(org_id)
            if not org_tracker.track_event(event_type, source, data):
                self.logger.error("Failed to track event to org context")
                success = False

        if session_id:
            session_tracker = self.get_session_context(session_id)
            if not session_tracker.track_event(event_type, source, data):
                self.logger.error("Failed to track event to session context")
                success = False

        return success

    def get_events_from_all_contexts(
        self,
        start: datetime,
        stop: datetime,
        filter_dict: Dict[str, str],
        app_id: Optional[str],
        org_id: Optional[str],
        session_id: Optional[str],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get events from all contexts."""
        result = {}

        if self.app_tracker and app_id:
            app_filter = {"app_id": app_id}
            for k, v in filter_dict.items():
                app_filter[k] = v

            events = self.app_tracker.get_events(start, stop, app_filter)
            result[ContextType.APP.value] = events

        if org_id:
            org_filter = {"org_id": org_id}
            for k, v in filter_dict.items():
                org_filter[k] = v

            org_tracker = self.get_org_context(org_id)
            events = org_tracker.get_events(start, stop, org_filter)
            result[ContextType.ORG.value] = events

        if session_id:
            session_filter = {"session_id": session_id}
            for k, v in filter_dict.items():
                session_filter[k] = v

            session_tracker = self.get_session_context(session_id)
            events = session_tracker.get_events(start, stop, session_filter)
            result[ContextType.SESSION.value] = events

        return result


try:
    from django.apps import AppConfig

    class InfluxDBContextConfig(AppConfig):
        """Django app configuration for InfluxDB context."""
        name = 'backend.apps.ml.integration'
        label = 'influxdb_context'
        verbose_name = 'InfluxDB Context Integration'

        def ready(self):
            """Initialize the app when Django starts."""
            from . import signals
except ImportError:
    pass
