"""
ML app configuration.
"""

import os
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class MLConfig(AppConfig):
    """ML app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ml"
    verbose_name = "Machine Learning"

    def ready(self):
        """
        Initialize the app when Django starts.
        """
        data_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "data",
        )
        os.makedirs(os.path.join(data_dir, "github"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "trajectories"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "benchmarks"), exist_ok=True)

        logger.info("ML app data directories created")

        # Initialize eventstream integration
        from .integration.eventstream_integration import (
            event_stream,
            Event,
            EventType,
            EventSource,
        )

        logger.info("Initializing ML app eventstream integration")

        async def start_event_stream():
            try:
                await event_stream.start()
                logger.info("ML app eventstream started successfully")

                event_data = {
                    "action": "app_startup",
                    "app": "ml_app",
                    "components": [
                        "GitHub Scraper",
                        "Trajectory Generator",
                        "Historical Benchmark",
                        "Eventstream Integration",
                        "Kubernetes Integration",
                    ],
                }
                await event_stream.publish(
                    Event.new(EventType.STATE_UPDATE, EventSource.ML, event_data)
                )
                logger.info("ML app startup event published")
            except Exception as e:
                logger.error(f"Failed to start eventstream: {e}")

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(start_event_stream())
            else:
                loop.run_until_complete(start_event_stream())
        except Exception as e:
            logger.error(f"Error setting up eventstream: {e}")

        logger.info("ML app initialization complete")
