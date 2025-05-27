"""
Tests for the trajectory generator.
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
    from apps.ml.trajectories.generator import (
        TrajectoryGenerator,
        TrajectoryStep,
        BenchmarkTrajectory,
    )

    class TestTrajectoryGenerator(unittest.TestCase):
        """Tests for the trajectory generator."""

        def setUp(self):
            """Set up test environment."""
            self.generator = TrajectoryGenerator(output_dir="/tmp/trajectories_test")

        def tearDown(self):
            """Clean up test environment."""
            if os.path.exists("/tmp/trajectories_test"):
                for file in os.listdir("/tmp/trajectories_test"):
                    os.remove(os.path.join("/tmp/trajectories_test", file))
                os.rmdir("/tmp/trajectories_test")

        def test_get_issue_type(self):
            """Test issue type detection."""
            bug_issue = {
                "title": "Fix crash when loading data",
                "body": "The application crashes when loading data",
                "labels": [{"name": "bug"}],
            }
            self.assertEqual(self.generator._get_issue_type(bug_issue), "bug")

            feature_issue = {
                "title": "Add new feature",
                "body": "Please add a new feature",
                "labels": [{"name": "enhancement"}],
            }
            self.assertEqual(self.generator._get_issue_type(feature_issue), "feature")

            doc_issue = {
                "title": "Update README",
                "body": "Please update the documentation",
                "labels": [{"name": "documentation"}],
            }
            self.assertEqual(self.generator._get_issue_type(doc_issue), "documentation")

            general_issue = {
                "title": "General issue",
                "body": "This is a general issue",
                "labels": [{"name": "question"}],
            }
            self.assertEqual(self.generator._get_issue_type(general_issue), "general")

        async def test_generate_trajectory(self):
            """Test trajectory generation."""
            issue = {
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
            }

            trajectory = await self.generator.generate_trajectory(issue)

            self.assertEqual(trajectory.issue_id, "101")
            self.assertEqual(trajectory.repository, "owner/repo")
            self.assertGreater(len(trajectory.steps), 0)

            self.assertEqual(trajectory.steps[0].action, "read_issue")
            self.assertEqual(
                trajectory.steps[0].observation, "Issue #1: Fix crash when loading data"
            )

            self.assertEqual(trajectory.steps[-1].action, "create_pr")

        async def test_generate_trajectories(self):
            """Test generating multiple trajectories."""
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

            trajectories = await self.generator.generate_trajectories(issues)

            self.assertEqual(len(trajectories), 2)
            self.assertEqual(trajectories[0].issue_id, "101")
            self.assertEqual(trajectories[1].issue_id, "102")

        async def test_save_and_load_trajectories(self):
            """Test saving and loading trajectories."""
            trajectories = [
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

            filename = "test_trajectories.json"
            saved_path = await self.generator.save_trajectories(trajectories, filename)

            self.assertTrue(os.path.exists(saved_path))

            loaded_trajectories = await self.generator.load_trajectories(filename)

            self.assertEqual(len(loaded_trajectories), 2)
            self.assertEqual(loaded_trajectories[0].issue_id, "101")
            self.assertEqual(loaded_trajectories[1].issue_id, "102")
            self.assertEqual(len(loaded_trajectories[0].steps), 2)
            self.assertEqual(len(loaded_trajectories[1].steps), 2)

    if __name__ == "__main__":
        unittest.main()

except ImportError as e:
    print(f"Import error: {e}")
    print("Skipping trajectory generator tests due to missing dependencies")
