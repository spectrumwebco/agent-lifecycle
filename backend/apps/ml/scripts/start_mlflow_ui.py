"""
Start MLflow UI for monitoring RLLM training.

This script starts the MLflow UI for monitoring RLLM training progress.
"""

import os
import sys
import argparse
import logging
import asyncio
from typing import Optional

from ..monitoring.mlflow_monitoring import MLflowMonitoring


async def start_mlflow_ui(
    host: str = "0.0.0.0",
    port: int = 5000,
    tracking_uri: Optional[str] = None,
):
    """
    Start MLflow UI.

    Args:
        host: Host to bind to
        port: Port to bind to
        tracking_uri: MLflow tracking URI
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("start_mlflow_ui")

    logger.info(f"Starting MLflow UI at http://{host}:{port}")
    
    if tracking_uri:
        logger.info(f"Using tracking URI: {tracking_uri}")
    
    success = await MLflowMonitoring.start_mlflow_ui(
        host=host,
        port=port,
        tracking_uri=tracking_uri,
    )
    
    if success:
        logger.info(f"MLflow UI started successfully at http://{host}:{port}")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping MLflow UI")
    else:
        logger.error("Failed to start MLflow UI")
        sys.exit(1)


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(
        description="Start MLflow UI for monitoring RLLM training"
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind to"
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="Port to bind to"
    )
    parser.add_argument(
        "--tracking-uri", type=str, help="MLflow tracking URI"
    )

    args = parser.parse_args()

    asyncio.run(
        start_mlflow_ui(
            host=args.host,
            port=args.port,
            tracking_uri=args.tracking_uri,
        )
    )


if __name__ == "__main__":
    main()
