"""
Historical benchmarking system for AI Agent evaluation.

This module provides functionality to benchmark AI Agents using
historical GitHub issues and generated trajectories.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..integration.eventstream_integration import (
    event_stream,
    Event,
    EventType,
    EventSource,
)
from ..integration.k8s_integration import k8s_client
from ..trajectories.generator import TrajectoryGenerator


class BenchmarkResult(BaseModel):
    """Result of a benchmark run."""

    benchmark_id: str = Field(..., description="Benchmark ID")
    start_time: str = Field(..., description="Start time")
    end_time: str = Field(..., description="End time")
    total_issues: int = Field(..., description="Total number of issues")
    successful_issues: int = Field(..., description="Number of successful issues")
    failed_issues: int = Field(..., description="Number of failed issues")
    skipped_issues: int = Field(..., description="Number of skipped issues")
    average_steps: float = Field(
        ..., description="Average number of steps per trajectory"
    )
    metrics: Dict[str, float] = Field(
        default_factory=dict, description="Benchmark metrics"
    )
    trajectories: List[str] = Field(default_factory=list, description="Trajectory IDs")


class HistoricalBenchmark:
    """Benchmarking system using historical GitHub issues."""

    def __init__(
        self,
        output_dir: str = "./data/benchmarks",
        trajectories_dir: str = "./data/trajectories",
    ):
        """
        Initialize historical benchmark.

        Args:
            output_dir: Directory to save benchmark results
            trajectories_dir: Directory with trajectory data
        """
        self.output_dir = output_dir
        self.trajectories_dir = trajectories_dir

        os.makedirs(output_dir, exist_ok=True)

        self.logger = logging.getLogger("HistoricalBenchmark")

        self.trajectory_generator = TrajectoryGenerator(trajectories_dir)

        self.event_stream = event_stream

        self.k8s_client = k8s_client

    async def _publish_benchmark_start(
        self, benchmark_id: str, total_issues: int
    ) -> None:
        """
        Publish benchmark start event.

        Args:
            benchmark_id: Benchmark ID
            total_issues: Total number of issues
        """
        if not self.event_stream:
            return

        event_data = {
            "action": "benchmark_start",
            "benchmark_id": benchmark_id,
            "total_issues": total_issues,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            await self.event_stream.publish(
                Event.new(EventType.STATE_UPDATE, EventSource.ML, event_data)
            )
        except Exception as e:
            self.logger.error(f"Error publishing benchmark start event: {e}")

    async def _publish_benchmark_progress(
        self, benchmark_id: str, processed_issues: int, total_issues: int
    ) -> None:
        """
        Publish benchmark progress event.

        Args:
            benchmark_id: Benchmark ID
            processed_issues: Number of processed issues
            total_issues: Total number of issues
        """
        if not self.event_stream:
            return

        event_data = {
            "action": "benchmark_progress",
            "benchmark_id": benchmark_id,
            "processed_issues": processed_issues,
            "total_issues": total_issues,
            "progress_percentage": round(processed_issues / total_issues * 100, 2),
            "timestamp": datetime.now().isoformat(),
        }

        try:
            await self.event_stream.publish(
                Event.new(EventType.STATE_UPDATE, EventSource.ML, event_data)
            )
        except Exception as e:
            self.logger.error(f"Error publishing benchmark progress event: {e}")

    async def _publish_benchmark_complete(
        self, benchmark_id: str, result: BenchmarkResult
    ) -> None:
        """
        Publish benchmark complete event.

        Args:
            benchmark_id: Benchmark ID
            result: Benchmark result
        """
        if not self.event_stream:
            return

        event_data = {
            "action": "benchmark_complete",
            "benchmark_id": benchmark_id,
            "result": result.dict(),
            "timestamp": datetime.now().isoformat(),
        }

        try:
            await self.event_stream.publish(
                Event.new(EventType.STATE_UPDATE, EventSource.ML, event_data)
            )
        except Exception as e:
            self.logger.error(f"Error publishing benchmark complete event: {e}")

    async def _setup_mlflow(self, namespace: str = "ml-infrastructure") -> bool:
        """
        Set up MLflow for experiment tracking.

        Args:
            namespace: Kubernetes namespace

        Returns:
            Success status
        """
        if not self.k8s_client:
            self.logger.warning(
                "Kubernetes client not available, skipping MLflow setup"
            )
            return False

        try:
            await self.k8s_client.create_namespace(namespace)

            success = await self.k8s_client.deploy_mlflow(namespace)

            if success:
                self.logger.info(
                    f"MLflow deployed successfully in namespace {namespace}"
                )
            else:
                self.logger.error(f"Failed to deploy MLflow in namespace {namespace}")

            return success
        except Exception as e:
            self.logger.error(f"Error setting up MLflow: {e}")
            return False

    async def _log_to_mlflow(self, benchmark_id: str, result: BenchmarkResult) -> None:
        """
        Log benchmark results to MLflow.

        Args:
            benchmark_id: Benchmark ID
            result: Benchmark result
        """
        try:
            import mlflow

            tracking_uri = None
            if self.event_stream:
                tracking_uri = await self.event_stream.get_app_context(
                    "mlflow_tracking_uri"
                )

            if tracking_uri:
                mlflow.set_tracking_uri(tracking_uri)

            with mlflow.start_run(run_name=f"historical_benchmark_{benchmark_id}"):
                mlflow.log_param("benchmark_id", benchmark_id)
                mlflow.log_param("total_issues", result.total_issues)
                mlflow.log_param("start_time", result.start_time)
                mlflow.log_param("end_time", result.end_time)

                mlflow.log_metric("successful_issues", result.successful_issues)
                mlflow.log_metric("failed_issues", result.failed_issues)
                mlflow.log_metric("skipped_issues", result.skipped_issues)
                mlflow.log_metric("average_steps", result.average_steps)

                for key, value in result.metrics.items():
                    mlflow.log_metric(key, value)

                result_path = os.path.join(
                    self.output_dir, f"result_{benchmark_id}.json"
                )
                with open(result_path, "w") as f:
                    json.dump(result.dict(), f, indent=2)

                mlflow.log_artifact(result_path)

                self.logger.info(f"Logged benchmark results to MLflow: {benchmark_id}")
        except ImportError:
            self.logger.warning("MLflow not available, skipping logging")
        except Exception as e:
            self.logger.error(f"Error logging to MLflow: {e}")

    async def run_benchmark(
        self,
        issues: List[Dict[str, Any]],
        detailed_trajectories: bool = True,
        log_to_mlflow: bool = True,
    ) -> BenchmarkResult:
        """
        Run benchmark on historical issues.

        Args:
            issues: List of issues
            detailed_trajectories: Whether to generate detailed trajectories
            log_to_mlflow: Whether to log results to MLflow

        Returns:
            Benchmark result
        """
        benchmark_id = f"historical_{int(datetime.now().timestamp())}"
        start_time = datetime.now().isoformat()

        self.logger.info(f"Starting historical benchmark: {benchmark_id}")
        self.logger.info(f"Total issues: {len(issues)}")

        if log_to_mlflow:
            await self._setup_mlflow()

        await self._publish_benchmark_start(benchmark_id, len(issues))

        trajectories = await self.trajectory_generator.generate_trajectories(
            issues, detailed=detailed_trajectories
        )

        await self.trajectory_generator.save_trajectories(
            trajectories, filename=f"trajectories_{benchmark_id}.json"
        )
        self.logger.info(f"Saved trajectories for benchmark: {benchmark_id}")

        total_issues = len(issues)
        successful_issues = len(trajectories)
        failed_issues = 0
        skipped_issues = total_issues - successful_issues

        total_steps = sum(len(t.steps) for t in trajectories)
        average_steps = total_steps / successful_issues if successful_issues > 0 else 0

        result = BenchmarkResult(
            benchmark_id=benchmark_id,
            start_time=start_time,
            end_time=datetime.now().isoformat(),
            total_issues=total_issues,
            successful_issues=successful_issues,
            failed_issues=failed_issues,
            skipped_issues=skipped_issues,
            average_steps=average_steps,
            metrics={
                "success_rate": (
                    successful_issues / total_issues if total_issues > 0 else 0
                ),
                "average_steps": average_steps,
            },
            trajectories=[t.issue_id for t in trajectories],
        )

        result_path = os.path.join(self.output_dir, f"result_{benchmark_id}.json")
        with open(result_path, "w") as f:
            json.dump(result.dict(), f, indent=2)

        self.logger.info(f"Benchmark completed: {benchmark_id}")
        self.logger.info(f"Results saved to: {result_path}")

        await self._publish_benchmark_complete(benchmark_id, result)

        if log_to_mlflow:
            await self._log_to_mlflow(benchmark_id, result)

        return result

    async def load_benchmark_result(
        self, benchmark_id: str
    ) -> Optional[BenchmarkResult]:
        """
        Load benchmark result.

        Args:
            benchmark_id: Benchmark ID

        Returns:
            Benchmark result or None if not found
        """
        result_path = os.path.join(self.output_dir, f"result_{benchmark_id}.json")

        if not os.path.exists(result_path):
            self.logger.error(f"Benchmark result not found: {result_path}")
            return None

        with open(result_path, "r") as f:
            data = json.load(f)

        result = BenchmarkResult(**data)

        self.logger.info(f"Loaded benchmark result: {benchmark_id}")

        return result
