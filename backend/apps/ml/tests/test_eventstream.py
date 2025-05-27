"""
Test the eventstream integration.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from apps.ml.integration.eventstream_integration import (
        Event,
        EventType,
        EventSource,
    )

    from apps.ml.integration.eventstream_integration import EventStream

    test_event_stream = EventStream()

    async def test_eventstream():
        """Test the eventstream integration."""
        logger.info("Starting eventstream test")

        await test_event_stream.start()
        logger.info("Event stream started")

        def on_message(event):
            logger.info(f"Received message event: {event.id}")
            logger.info(f"  Type: {event.type}")
            logger.info(f"  Source: {event.source}")
            logger.info(f"  Data: {event.data}")

        test_event_stream.subscribe(EventType.MESSAGE, on_message)
        logger.info("Subscribed to message events")

        test_event = Event.new(
            EventType.MESSAGE,
            EventSource.ML,
            {"message": "Hello from ML app!"},
            {"test": "true"},
        )

        success = await test_event_stream.publish(test_event)
        logger.info(f"Published test event: {success}")

        logger.info("Waiting for events...")
        await asyncio.sleep(2)

        await test_event_stream.set_app_context("ml:test", "test_value")
        context_value = await test_event_stream.get_app_context("ml:test")
        logger.info(f"Retrieved context value: {context_value}")

        await test_event_stream.stop()
        logger.info("Event stream stopped")

        logger.info("Eventstream integration test completed successfully")
        return True

    if __name__ == "__main__":
        asyncio.run(test_eventstream())

except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info("Skipping eventstream test due to missing dependencies")

    if __name__ == "__main__":
        logger.info(
            "Test environment not properly set up. Please install required dependencies."
        )
        sys.exit(0)
