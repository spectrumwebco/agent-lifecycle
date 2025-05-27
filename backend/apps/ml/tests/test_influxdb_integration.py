import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from backend.apps.ml.integration.influxdb_integration import (
    ContextClient,
    ContextManager,
    AppContextTracker,
    OrgContextTracker,
    SessionContextTracker,
    ContextType,
)


class TestContextClient(unittest.TestCase):
    @patch("backend.apps.ml.integration.influxdb_integration.influxdb_client")
    def test_context_client_initialization(self, mock_influxdb_client):
        mock_client = MagicMock()
        mock_write_api = MagicMock()
        mock_query_api = MagicMock()
        mock_influxdb_client.InfluxDBClient.return_value = mock_client
        mock_client.write_api.return_value = mock_write_api
        mock_client.query_api.return_value = mock_query_api

        client = ContextClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
            measurement="test-measurement",
        )

        self.assertEqual(client.url, "http://localhost:8086")
        self.assertEqual(client.token, "test-token")
        self.assertEqual(client.org, "test-org")
        self.assertEqual(client.bucket, "test-bucket")
        self.assertEqual(client.measurement, "test-measurement")
        self.assertEqual(client.client, mock_client)
        self.assertEqual(client.write_api, mock_write_api)
        self.assertEqual(client.query_api, mock_query_api)
        self.assertTrue(client.influxdb_available)

    @patch("backend.apps.ml.integration.influxdb_integration.influxdb_client")
    def test_write_event(self, mock_influxdb_client):
        mock_client = MagicMock()
        mock_write_api = MagicMock()
        mock_query_api = MagicMock()
        mock_influxdb_client.InfluxDBClient.return_value = mock_client
        mock_client.write_api.return_value = mock_write_api
        mock_client.query_api.return_value = mock_query_api
        mock_point = MagicMock()
        mock_influxdb_client.Point.return_value = mock_point
        mock_point.tag.return_value = mock_point
        mock_point.field.return_value = mock_point

        client = ContextClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
            measurement="test-measurement",
        )
        result = client.write_event(
            context_type=ContextType.APP,
            context_id="test-app",
            event_type="test-event",
            source="test-source",
            data={
                "test_key": "test_value",
                "numeric_value": 42,
                "bool_value": True,
            },
        )

        self.assertTrue(result)
        mock_influxdb_client.Point.assert_called_once_with("test-measurement")
        mock_point.tag.assert_any_call("context_type", "app")
        mock_point.tag.assert_any_call("context_id", "test-app")
        mock_point.tag.assert_any_call("event_type", "test-event")
        mock_point.tag.assert_any_call("source", "test-source")
        mock_point.field.assert_any_call("test_key", "test_value")
        mock_point.field.assert_any_call("numeric_value", 42)
        mock_point.field.assert_any_call("bool_value", True)
        mock_write_api.write.assert_called_once_with(
            bucket="test-bucket", org="test-org", record=mock_point
        )

    @patch("backend.apps.ml.integration.influxdb_integration.influxdb_client")
    def test_write_event_error(self, mock_influxdb_client):
        mock_client = MagicMock()
        mock_write_api = MagicMock()
        mock_query_api = MagicMock()
        mock_influxdb_client.InfluxDBClient.return_value = mock_client
        mock_client.write_api.return_value = mock_write_api
        mock_client.query_api.return_value = mock_query_api
        mock_point = MagicMock()
        mock_influxdb_client.Point.return_value = mock_point
        mock_point.tag.return_value = mock_point
        mock_point.field.return_value = mock_point
        mock_write_api.write.side_effect = Exception("Test error")

        client = ContextClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
            measurement="test-measurement",
        )
        result = client.write_event(
            context_type=ContextType.APP,
            context_id="test-app",
            event_type="test-event",
            source="test-source",
            data={
                "test_key": "test_value",
            },
        )

        self.assertFalse(result)

    @patch("backend.apps.ml.integration.influxdb_integration.influxdb_client")
    def test_query_events(self, mock_influxdb_client):
        mock_client = MagicMock()
        mock_write_api = MagicMock()
        mock_query_api = MagicMock()
        mock_influxdb_client.InfluxDBClient.return_value = mock_client
        mock_client.write_api.return_value = mock_write_api
        mock_client.query_api.return_value = mock_query_api
        
        mock_tables = MagicMock()
        mock_query_api.query.return_value = mock_tables
        
        mock_record1 = {
            "context_type": "app",
            "context_id": "test-app",
            "event_type": "test-event",
            "source": "test-source",
            "test_key": "test_value",
            "_time": datetime.now(),
        }
        mock_record2 = {
            "context_type": "app",
            "context_id": "test-app",
            "event_type": "test-event2",
            "source": "test-source2",
            "test_key2": "test_value2",
            "_time": datetime.now(),
        }
        mock_tables.to_values.return_value = [mock_record1, mock_record2]

        client = ContextClient(
            url="http://localhost:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket",
            measurement="test-measurement",
        )
        start = datetime.now() - timedelta(hours=1)
        stop = datetime.now()
        events = client.query_events(
            context_type=ContextType.APP,
            context_id="test-app",
            start=start,
            stop=stop,
            filter_dict={"event_type": "test-event"},
        )

        self.assertEqual(len(events), 2)
        mock_query_api.query.assert_called_once()
        self.assertIn("from(bucket: \"test-bucket\")", mock_query_api.query.call_args[0][0])
        self.assertIn("r[\"context_type\"] == \"app\"", mock_query_api.query.call_args[0][0])
        self.assertIn("r[\"context_id\"] == \"test-app\"", mock_query_api.query.call_args[0][0])
        self.assertIn("r[\"event_type\"] == \"test-event\"", mock_query_api.query.call_args[0][0])


class TestContextManager(unittest.TestCase):
    @patch("backend.apps.ml.integration.influxdb_integration.ContextClient")
    def test_context_manager_initialization(self, mock_context_client):
        mock_client = MagicMock()
        mock_context_client.return_value = mock_client

        manager = ContextManager(mock_client)

        self.assertEqual(manager.client, mock_client)
        self.assertEqual(len(manager.app_contexts), 0)
        self.assertEqual(len(manager.org_contexts), 0)
        self.assertEqual(len(manager.session_contexts), 0)

    @patch("backend.apps.ml.integration.influxdb_integration.ContextClient")
    @patch("backend.apps.ml.integration.influxdb_integration.AppContextTracker")
    def test_create_app_context(self, mock_app_tracker, mock_context_client):
        mock_client = MagicMock()
        mock_context_client.return_value = mock_client
        mock_tracker = MagicMock()
        mock_app_tracker.return_value = mock_tracker

        manager = ContextManager(mock_client)
        tracker = manager.create_app_context("test-app")

        self.assertEqual(tracker, mock_tracker)
        self.assertEqual(len(manager.app_contexts), 1)
        self.assertIn("test-app", manager.app_contexts)
        self.assertEqual(manager.app_contexts["test-app"], mock_tracker)
        mock_app_tracker.assert_called_once_with(mock_client, "test-app")

    @patch("backend.apps.ml.integration.influxdb_integration.ContextClient")
    @patch("backend.apps.ml.integration.influxdb_integration.OrgContextTracker")
    def test_create_org_context(self, mock_org_tracker, mock_context_client):
        mock_client = MagicMock()
        mock_context_client.return_value = mock_client
        mock_tracker = MagicMock()
        mock_org_tracker.return_value = mock_tracker

        manager = ContextManager(mock_client)
        tracker = manager.create_org_context("test-org")

        self.assertEqual(tracker, mock_tracker)
        self.assertEqual(len(manager.org_contexts), 1)
        self.assertIn("test-org", manager.org_contexts)
        self.assertEqual(manager.org_contexts["test-org"], mock_tracker)
        mock_org_tracker.assert_called_once_with(mock_client, "test-org")

    @patch("backend.apps.ml.integration.influxdb_integration.ContextClient")
    @patch("backend.apps.ml.integration.influxdb_integration.SessionContextTracker")
    def test_create_session_context(self, mock_session_tracker, mock_context_client):
        mock_client = MagicMock()
        mock_context_client.return_value = mock_client
        mock_tracker = MagicMock()
        mock_session_tracker.return_value = mock_tracker

        manager = ContextManager(mock_client)
        tracker = manager.create_session_context("test-session")

        self.assertEqual(tracker, mock_tracker)
        self.assertEqual(len(manager.session_contexts), 1)
        self.assertIn("test-session", manager.session_contexts)
        self.assertEqual(manager.session_contexts["test-session"], mock_tracker)
        mock_session_tracker.assert_called_once_with(mock_client, "test-session")

    @patch("backend.apps.ml.integration.influxdb_integration.ContextClient")
    def test_get_app_context(self, mock_context_client):
        mock_client = MagicMock()
        mock_context_client.return_value = mock_client
        mock_tracker = MagicMock()

        manager = ContextManager(mock_client)
        manager.app_contexts["test-app"] = mock_tracker
        tracker = manager.get_app_context("test-app")

        self.assertEqual(tracker, mock_tracker)

    @patch("backend.apps.ml.integration.influxdb_integration.ContextClient")
    def test_get_org_context(self, mock_context_client):
        mock_client = MagicMock()
        mock_context_client.return_value = mock_client
        mock_tracker = MagicMock()

        manager = ContextManager(mock_client)
        manager.org_contexts["test-org"] = mock_tracker
        tracker = manager.get_org_context("test-org")

        self.assertEqual(tracker, mock_tracker)

    @patch("backend.apps.ml.integration.influxdb_integration.ContextClient")
    def test_get_session_context(self, mock_context_client):
        mock_client = MagicMock()
        mock_context_client.return_value = mock_client
        mock_tracker = MagicMock()

        manager = ContextManager(mock_client)
        manager.session_contexts["test-session"] = mock_tracker
        tracker = manager.get_session_context("test-session")

        self.assertEqual(tracker, mock_tracker)

    @patch("backend.apps.ml.integration.influxdb_integration.ContextClient")
    def test_track_event_to_all_contexts(self, mock_context_client):
        mock_client = MagicMock()
        mock_context_client.return_value = mock_client
        mock_app_tracker = MagicMock()
        mock_org_tracker = MagicMock()
        mock_session_tracker = MagicMock()

        manager = ContextManager(mock_client)
        manager.app_contexts["test-app"] = mock_app_tracker
        manager.org_contexts["test-org"] = mock_org_tracker
        manager.session_contexts["test-session"] = mock_session_tracker
        
        result = manager.track_event_to_all_contexts(
            event_type="test-event",
            source="test-source",
            org_name="test-org",
            session_id="test-session",
            data={
                "test_key": "test_value",
            },
        )

        self.assertTrue(result)
        mock_app_tracker.track_event.assert_called_once_with(
            event_type="test-event",
            source="test-source",
            data={
                "test_key": "test_value",
            },
        )
        mock_org_tracker.track_event.assert_called_once_with(
            event_type="test-event",
            source="test-source",
            data={
                "test_key": "test_value",
            },
        )
        mock_session_tracker.track_event.assert_called_once_with(
            event_type="test-event",
            source="test-source",
            data={
                "test_key": "test_value",
            },
        )


class TestAppContextTracker(unittest.TestCase):
    def test_app_context_tracker_initialization(self):
        mock_client = MagicMock()

        tracker = AppContextTracker(mock_client, "test-app")

        self.assertEqual(tracker.client, mock_client)
        self.assertEqual(tracker.app_id, "test-app")

    def test_track_event(self):
        mock_client = MagicMock()
        mock_client.write_event.return_value = True

        tracker = AppContextTracker(mock_client, "test-app")
        result = tracker.track_event(
            event_type="test-event",
            source="test-source",
            data={
                "test_key": "test_value",
            },
        )

        self.assertTrue(result)
        mock_client.write_event.assert_called_once_with(
            context_type=ContextType.APP,
            context_id="test-app",
            event_type="test-event",
            source="test-source",
            data={
                "test_key": "test_value",
            },
        )

    def test_track_agent_event(self):
        mock_client = MagicMock()
        mock_client.write_event.return_value = True

        tracker = AppContextTracker(mock_client, "test-app")
        result = tracker.track_agent_event(
            agent_id="test-agent",
            event_type="test-event",
            data={
                "test_key": "test_value",
            },
        )

        self.assertTrue(result)
        mock_client.write_event.assert_called_once_with(
            context_type=ContextType.APP,
            context_id="test-app",
            event_type="test-event",
            source="agent:test-agent",
            data={
                "test_key": "test_value",
                "agent_id": "test-agent",
            },
        )

    def test_get_events(self):
        mock_client = MagicMock()
        mock_events = [{"event": "data"}]
        mock_client.query_events.return_value = mock_events
        start = datetime.now() - timedelta(hours=1)
        stop = datetime.now()

        tracker = AppContextTracker(mock_client, "test-app")
        events = tracker.get_events(
            start=start,
            stop=stop,
            filter_dict={
                "event_type": "test-event",
            },
        )

        self.assertEqual(events, mock_events)
        mock_client.query_events.assert_called_once_with(
            context_type=ContextType.APP,
            context_id="test-app",
            start=start,
            stop=stop,
            filter_dict={
                "event_type": "test-event",
            },
        )


class TestOrgContextTracker(unittest.TestCase):
    def test_org_context_tracker_initialization(self):
        mock_client = MagicMock()

        tracker = OrgContextTracker(mock_client, "test-org")

        self.assertEqual(tracker.client, mock_client)
        self.assertEqual(tracker.org_name, "test-org")

    def test_track_event(self):
        mock_client = MagicMock()
        mock_client.write_event.return_value = True

        tracker = OrgContextTracker(mock_client, "test-org")
        result = tracker.track_event(
            event_type="test-event",
            source="test-source",
            data={
                "test_key": "test_value",
            },
        )

        self.assertTrue(result)
        mock_client.write_event.assert_called_once_with(
            context_type=ContextType.ORG,
            context_id="test-org",
            event_type="test-event",
            source="test-source",
            data={
                "test_key": "test_value",
            },
        )

    def test_track_repository_event(self):
        mock_client = MagicMock()
        mock_client.write_event.return_value = True

        tracker = OrgContextTracker(mock_client, "test-org")
        result = tracker.track_repository_event(
            repository="test-repo",
            event_type="test-event",
            data={
                "test_key": "test_value",
            },
        )

        self.assertTrue(result)
        mock_client.write_event.assert_called_once_with(
            context_type=ContextType.ORG,
            context_id="test-org",
            event_type="test-event",
            source="repo:test-repo",
            data={
                "test_key": "test_value",
                "repository": "test-repo",
            },
        )

    def test_track_agent_event(self):
        mock_client = MagicMock()
        mock_client.write_event.return_value = True

        tracker = OrgContextTracker(mock_client, "test-org")
        result = tracker.track_agent_event(
            agent_id="test-agent",
            event_type="test-event",
            data={
                "test_key": "test_value",
            },
        )

        self.assertTrue(result)
        mock_client.write_event.assert_called_once_with(
            context_type=ContextType.ORG,
            context_id="test-org",
            event_type="test-event",
            source="agent:test-agent",
            data={
                "test_key": "test_value",
                "agent_id": "test-agent",
            },
        )

    def test_get_events(self):
        mock_client = MagicMock()
        mock_events = [{"event": "data"}]
        mock_client.query_events.return_value = mock_events
        start = datetime.now() - timedelta(hours=1)
        stop = datetime.now()

        tracker = OrgContextTracker(mock_client, "test-org")
        events = tracker.get_events(
            start=start,
            stop=stop,
            filter_dict={
                "event_type": "test-event",
            },
        )

        self.assertEqual(events, mock_events)
        mock_client.query_events.assert_called_once_with(
            context_type=ContextType.ORG,
            context_id="test-org",
            start=start,
            stop=stop,
            filter_dict={
                "event_type": "test-event",
            },
        )

    def test_get_repository_events(self):
        mock_client = MagicMock()
        mock_events = [{"event": "data"}]
        mock_client.query_events.return_value = mock_events
        start = datetime.now() - timedelta(hours=1)
        stop = datetime.now()

        tracker = OrgContextTracker(mock_client, "test-org")
        events = tracker.get_repository_events(
            repository="test-repo",
            start=start,
            stop=stop,
            filter_dict={
                "event_type": "test-event",
            },
        )

        self.assertEqual(events, mock_events)
        mock_client.query_events.assert_called_once_with(
            context_type=ContextType.ORG,
            context_id="test-org",
            start=start,
            stop=stop,
            filter_dict={
                "event_type": "test-event",
                "source": "repo:test-repo",
            },
        )


class TestSessionContextTracker(unittest.TestCase):
    def test_session_context_tracker_initialization(self):
        mock_client = MagicMock()

        tracker = SessionContextTracker(mock_client, "test-session")

        self.assertEqual(tracker.client, mock_client)
        self.assertEqual(tracker.session_id, "test-session")

    def test_track_event(self):
        mock_client = MagicMock()
        mock_client.write_event.return_value = True

        tracker = SessionContextTracker(mock_client, "test-session")
        result = tracker.track_event(
            event_type="test-event",
            source="test-source",
            data={
                "test_key": "test_value",
            },
        )

        self.assertTrue(result)
        mock_client.write_event.assert_called_once_with(
            context_type=ContextType.SESSION,
            context_id="test-session",
            event_type="test-event",
            source="test-source",
            data={
                "test_key": "test_value",
            },
        )

    def test_track_agent_event(self):
        mock_client = MagicMock()
        mock_client.write_event.return_value = True

        tracker = SessionContextTracker(mock_client, "test-session")
        result = tracker.track_agent_event(
            agent_id="test-agent",
            event_type="test-event",
            data={
                "test_key": "test_value",
            },
        )

        self.assertTrue(result)
        mock_client.write_event.assert_called_once_with(
            context_type=ContextType.SESSION,
            context_id="test-session",
            event_type="test-event",
            source="agent:test-agent",
            data={
                "test_key": "test_value",
                "agent_id": "test-agent",
            },
        )

    def test_get_events(self):
        mock_client = MagicMock()
        mock_events = [{"event": "data"}]
        mock_client.query_events.return_value = mock_events
        start = datetime.now() - timedelta(hours=1)
        stop = datetime.now()

        tracker = SessionContextTracker(mock_client, "test-session")
        events = tracker.get_events(
            start=start,
            stop=stop,
            filter_dict={
                "event_type": "test-event",
            },
        )

        self.assertEqual(events, mock_events)
        mock_client.query_events.assert_called_once_with(
            context_type=ContextType.SESSION,
            context_id="test-session",
            start=start,
            stop=stop,
            filter_dict={
                "event_type": "test-event",
            },
        )


if __name__ == "__main__":
    unittest.main()
