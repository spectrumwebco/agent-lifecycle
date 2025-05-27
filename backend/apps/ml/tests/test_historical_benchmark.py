"""
Tests for the historical benchmarking system.
"""

import os
import json
import asyncio
import unittest
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from apps.ml.benchmarking.historical_benchmark import (
        HistoricalBenchmark,
        BenchmarkResult,
    )

    class TestHistoricalBenchmark(unittest.TestCase):
        """Tests for the historical benchmarking system."""

        def setUp(self):
            """Set up test environment."""
            self.benchmark = HistoricalBenchmark(
                output_dir="/tmp/benchmarks_test",
                trajectories_dir="/tmp/trajectories_test",
            )

        def tearDown(self):
            """Clean up test environment."""
            if os.path.exists("/tmp/benchmarks_test"):
                for file in os.listdir("/tmp/benchmarks_test"):
                    os.remove(os.path.join("/tmp/benchmarks_test", file))
                os.rmdir("/tmp/benchmarks_test")

        @patch(
            "apps.python_ml.benchmarking.historical_benchmark.HistoricalBenchmark._publish_benchmark_start"
        )
        @patch(
            "apps.python_ml.benchmarking.historical_benchmark.HistoricalBenchmark._publish_benchmark_complete"
        )
        @patch(
            "apps.python_ml.benchmarking.historical_benchmark.HistoricalBenchmark._setup_mlflow"
        )
        @patch(
            "apps.python_ml.benchmarking.historical_benchmark.HistoricalBenchmark._log_to_mlflow"
        )
        @patch(
            "apps.python_ml.trajectories.generator.TrajectoryGenerator.generate_trajectories"
        )
        @patch(
            "apps.python_ml.trajectories.generator.TrajectoryGenerator.save_trajectories"
        )
        async def test_run_benchmark(
            self,
            mock_save_trajectories,
            mock_generate_trajectories,
            mock_log_to_mlflow,
            mock_setup_mlflow,
            mock_publish_complete,
            mock_publish_start,
        ):
            """Test running a benchmark."""
            from apps.ml.trajectories.generator import (
                BenchmarkTrajectory,
                TrajectoryStep,
            )

            mock_trajectories = [
                BenchmarkTrajectory(
                    issue_id="101",
                    issue_url="https://github.com/owner/repo/issues/1",
                    repository="owner/repo",
                    steps=[
                        TrajectoryStep(
                            action="read_issue",
                            observation="Issue #1: Fix crash when loading data",
                            response="I'll analyze this issue to find a solution.",
                        ),
                        TrajectoryStep(
                            action="create_pr",
                            observation="Creating a PR for owner/repo...",
                            response="PR created successfully. The issue has been resolved.",
                        ),
                    ],
                    metadata={"issue_type": "bug"},
                ),
                BenchmarkTrajectory(
                    issue_id="102",
                    issue_url="https://github.com/owner/repo/issues/2",
                    repository="owner/repo",
                    steps=[
                        TrajectoryStep(
                            action="read_issue",
                            observation="Issue #2: Add new feature",
                            response="I'll analyze this issue to find a solution.",
                        ),
                        TrajectoryStep(
                            action="create_pr",
                            observation="Creating a PR for owner/repo...",
                            response="PR created successfully. The issue has been resolved.",
                        ),
                    ],
                    metadata={"issue_type": "feature"},
                ),
            ]

            mock_generate_trajectories.return_value = mock_trajectories
            mock_save_trajectories.return_value = (
                "/tmp/trajectories_test/trajectories_test.json"
            )

            issues = [
                {
                    "id": 101,
                    "number": 1,
                    "title": "Fix crash when loading data",
                    "body": "The application crashes when loading data",
                    "html_url": "https://github.com/owner/repo/issues/1",
                    "created_at": "2023-01-01T00:00:00Z",
                    "closed_at": "2023-01-02T00:00:00Z",
                    "labels": [{"name": "bug"}],
                    "repository": {
                        "id": 1,
                        "full_name": "owner/repo",
                        "stargazers_count": 200,
                        "topics": ["kubernetes", "gitops"],
                    },
                },
                {
                    "id": 102,
                    "number": 2,
                    "title": "Add new feature",
                    "body": "Please add a new feature",
                    "html_url": "https://github.com/owner/repo/issues/2",
                    "created_at": "2023-01-03T00:00:00Z",
                    "closed_at": "2023-01-04T00:00:00Z",
                    "labels": [{"name": "enhancement"}],
                    "repository": {
                        "id": 1,
                        "full_name": "owner/repo",
                        "stargazers_count": 200,
                        "topics": ["kubernetes", "gitops"],
                    },
                },
            ]

            result = await self.benchmark.run_benchmark(
                issues=issues,
                detailed_trajectories=True,
                log_to_mlflow=True,
            )

            self.assertIsInstance(result, BenchmarkResult)
            self.assertEqual(result.total_issues, 2)
            self.assertEqual(result.successful_issues, 2)
            self.assertEqual(result.failed_issues, 0)
            self.assertEqual(result.skipped_issues, 0)
            self.assertEqual(result.average_steps, 2.0)

            self.assertIn("success_rate", result.metrics)
            self.assertEqual(result.metrics["success_rate"], 1.0)
            self.assertIn("average_steps", result.metrics)
            self.assertEqual(result.metrics["average_steps"], 2.0)

            self.assertEqual(len(result.trajectories), 2)
            self.assertIn("101", result.trajectories)
            self.assertIn("102", result.trajectories)

            mock_publish_start.assert_called_once()
            mock_publish_complete.assert_called_once()
            mock_setup_mlflow.assert_called_once()
            mock_log_to_mlflow.assert_called_once()
            mock_generate_trajectories.assert_called_once_with(issues, detailed=True)
            mock_save_trajectories.assert_called_once()

        async def test_load_benchmark_result(self):
            """Test loading a benchmark result."""
            benchmark_id = "test_benchmark"
            result = BenchmarkResult(
                benchmark_id=benchmark_id,
                start_time="2023-01-01T00:00:00Z",
                end_time="2023-01-01T01:00:00Z",
                total_issues=2,
                successful_issues=2,
                failed_issues=0,
                skipped_issues=0,
                average_steps=2.0,
                metrics={
                    "success_rate": 1.0,
                    "average_steps": 2.0,
                },
                trajectories=["101", "102"],
            )

            os.makedirs("/tmp/benchmarks_test", exist_ok=True)
            result_path = os.path.join(
                "/tmp/benchmarks_test", f"result_{benchmark_id}.json"
            )
            with open(result_path, "w") as f:
                json.dump(result.dict(), f, indent=2)

            loaded_result = await self.benchmark.load_benchmark_result(benchmark_id)

            self.assertIsInstance(loaded_result, BenchmarkResult)
            self.assertEqual(loaded_result.benchmark_id, benchmark_id)
            self.assertEqual(loaded_result.total_issues, 2)
            self.assertEqual(loaded_result.successful_issues, 2)
            self.assertEqual(loaded_result.failed_issues, 0)
            self.assertEqual(loaded_result.skipped_issues, 0)
            self.assertEqual(loaded_result.average_steps, 2.0)

            self.assertIn("success_rate", loaded_result.metrics)
            self.assertEqual(loaded_result.metrics["success_rate"], 1.0)
            self.assertIn("average_steps", loaded_result.metrics)
            self.assertEqual(loaded_result.metrics["average_steps"], 2.0)

            self.assertEqual(len(loaded_result.trajectories), 2)
            self.assertIn("101", loaded_result.trajectories)
            self.assertIn("102", loaded_result.trajectories)

    if __name__ == "__main__":
        unittest.main()

except ImportError as e:
    print(f"Import error: {e}")
    print("Skipping historical benchmark tests due to missing dependencies")
