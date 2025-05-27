"""
Trajectory generator for AI Agent benchmarking.

This module provides functionality to generate realistic trajectories
for AI Agent benchmarking from historical GitHub and Gitee issues.
"""

import os
import json
import logging
import random
from typing import Dict, List, Any
from datetime import datetime

from ..models.trajectory_models import TrajectoryStep, BenchmarkTrajectory

def get_event_stream():
    from ..integration.eventstream_integration import (
        event_stream,
        Event,
        EventType,
        EventSource,
    )
    return event_stream, Event, EventType, EventSource


class TrajectoryGenerator:
    """Generator for realistic AI Agent trajectories."""

    def __init__(self, output_dir: str = "./data/trajectories"):
        """
        Initialize trajectory generator.

        Args:
            output_dir: Directory to save generated trajectories
        """
        self.output_dir = output_dir

        os.makedirs(output_dir, exist_ok=True)

        self.logger = logging.getLogger("TrajectoryGenerator")

        self.action_templates = {
            "bug": [
                "read_issue",
                "analyze_issue",
                "search_code",
                "analyze_error",
                "debug_issue",
                "review_logs",
                "implement_fix",
                "test_fix",
                "create_pr",
            ],
            "feature": [
                "read_issue",
                "analyze_issue",
                "plan_implementation",
                "design_architecture",
                "implement_feature",
                "write_tests",
                "update_documentation",
                "create_pr",
            ],
            "documentation": [
                "read_issue",
                "analyze_issue",
                "review_documentation",
                "research_topic",
                "write_documentation",
                "update_links",
                "create_pr",
            ],
            "general": [
                "read_issue",
                "analyze_issue",
                "plan_approach",
                "implement_solution",
                "test_solution",
                "create_pr",
            ],
        }

        self.response_templates = {
            "read_issue": [
                "I'll analyze this issue to find a solution.",
                "Let me understand this issue and work on a solution.",
                "I'll investigate this issue and resolve it.",
            ],
            "analyze_issue": [
                "Based on the issue description, I need to {action_detail}.",
                "After analyzing the issue, I see that I need to {action_detail}.",
                "The issue involves {action_detail}. I'll work on a solution.",
            ],
            "search_code": [
                "Let me search for the relevant code in this repository.",
                "I'll look for the code related to this issue.",
                "Searching for code that could be causing this issue.",
            ],
            "implement_solution": [
                "I've implemented a solution by {action_detail}.",
                "The solution has been implemented. I {action_detail}.",
                "Implementation complete. I {action_detail}.",
            ],
            "test_solution": [
                "Tests are passing. The solution works as expected.",
                "I've tested the solution and it resolves the issue.",
                "The solution has been tested and works correctly.",
            ],
            "create_pr": [
                "PR created successfully. The issue has been resolved.",
                "I've created a PR with the solution for this issue.",
                "The solution is ready for review in the PR I've created.",
            ],
        }

        event_stream, _, _, _ = get_event_stream()
        self.event_stream = event_stream

    def _get_issue_type(self, issue: Dict[str, Any]) -> str:
        """
        Determine issue type from issue content.

        Args:
            issue: Issue data

        Returns:
            Issue type (bug, feature, documentation, general)
        """
        title = issue.get("title", "").lower()
        body = issue.get("body", "").lower()
        labels = [label["name"].lower() for label in issue.get("labels", [])]

        if any(
            keyword in title or keyword in body or keyword in " ".join(labels)
            for keyword in ["bug", "error", "fix", "crash", "exception"]
        ):
            return "bug"
        elif any(
            keyword in title or keyword in body or keyword in " ".join(labels)
            for keyword in ["feature", "enhancement", "request", "add", "new"]
        ):
            return "feature"
        elif any(
            keyword in title or keyword in body or keyword in " ".join(labels)
            for keyword in ["doc", "documentation", "readme", "wiki"]
        ):
            return "documentation"
        else:
            return "general"

    def _get_random_response(self, action: str) -> str:
        """
        Get random response template for action.

        Args:
            action: Action name

        Returns:
            Response template
        """
        templates = self.response_templates.get(action, ["I've completed this step."])
        return random.choice(templates)

    async def generate_trajectory(
        self, issue: Dict[str, Any], detailed: bool = True
    ) -> BenchmarkTrajectory:
        """
        Generate realistic trajectory for an issue.

        Args:
            issue: Issue data
            detailed: Whether to generate a detailed trajectory

        Returns:
            Generated trajectory
        """
        if "repository" not in issue:
            raise ValueError("Issue must have a repository")

        repo = issue["repository"]

        if "full_name" in repo:
            repo_name = repo["full_name"]
            source = "github"
        else:
            repo_name = f"{repo['owner']['login']}/{repo['name']}"
            source = "gitee"

        issue_number = issue["number"]
        issue_title = issue["title"]
        issue_body = issue.get("body", "")
        issue_url = issue.get(
            "html_url", f"https://gitee.com/{repo_name}/issues/{issue_number}"
        )

        issue_type = self._get_issue_type(issue)

        action_template = self.action_templates.get(
            issue_type, self.action_templates["general"]
        )

        steps = []

        steps.append(
            TrajectoryStep(
                action="read_issue",
                observation=f"Issue #{issue_number}: {issue_title}",
                response=self._get_random_response("read_issue"),
            )
        )

        action_detail = (
            "fix the bug"
            if issue_type == "bug"
            else (
                "implement the feature"
                if issue_type == "feature"
                else (
                    "update the documentation"
                    if issue_type == "documentation"
                    else "solve this issue"
                )
            )
        )
        analyze_response = self._get_random_response("analyze_issue").format(
            action_detail=action_detail
        )

        steps.append(
            TrajectoryStep(
                action="analyze_issue",
                observation=issue_body[:500] + ("..." if len(issue_body) > 500 else ""),
                response=analyze_response,
            )
        )

        if detailed:
            for action in action_template[
                2:-1
            ]:  # Exclude last action (create_pr) for now
                observation = f"Performing {action}..."

                if action == "search_code":
                    observation = f"Searching for relevant code in {repo_name}..."
                elif (
                    action == "implement_solution"
                    or action == "implement_fix"
                    or action == "implement_feature"
                ):
                    observation = "Implementation in progress..."
                elif action == "test_solution" or action == "test_fix":
                    observation = "Running tests..."

                action_detail = (
                    "fixed the bug"
                    if issue_type == "bug"
                    else (
                        "implemented the feature"
                        if issue_type == "feature"
                        else (
                            "updated the documentation"
                            if issue_type == "documentation"
                            else "solved the issue"
                        )
                    )
                )
                response = (
                    self._get_random_response(action).format(
                        action_detail=action_detail
                    )
                    if action in self.response_templates
                    else f"Completed {action}."
                )

                steps.append(
                    TrajectoryStep(
                        action=action,
                        observation=observation,
                        response=response,
                    )
                )

        steps.append(
            TrajectoryStep(
                action="create_pr",
                observation=f"Creating a PR for {repo_name}...",
                response=self._get_random_response("create_pr"),
            )
        )

        trajectory = BenchmarkTrajectory(
            issue_id=str(issue["id"]),
            issue_url=issue_url,
            repository=repo_name,
            steps=steps,
            metadata={
                "issue_number": issue_number,
                "issue_title": issue_title,
                "issue_type": issue_type,
                "issue_labels": [label["name"] for label in issue.get("labels", [])],
                "issue_created_at": issue.get("created_at"),
                "issue_closed_at": issue.get("closed_at"),
            },
            source=source,
        )

        if self.event_stream:
            event_data = {
                "action": "generate_trajectory",
                "issue_id": str(issue["id"]),
                "repository": repo_name,
                "issue_number": issue_number,
                "steps_count": len(steps),
            }
            try:
                _, Event, EventType, EventSource = get_event_stream()
                await self.event_stream.publish(
                    Event.new(EventType.STATE_UPDATE, EventSource.ML, event_data)
                )
            except Exception as e:
                self.logger.error(f"Error publishing event: {e}")

        return trajectory

    async def generate_trajectories(
        self, issues: List[Dict[str, Any]], detailed: bool = True
    ) -> List[BenchmarkTrajectory]:
        """
        Generate trajectories for multiple issues.

        Args:
            issues: List of issues
            detailed: Whether to generate detailed trajectories

        Returns:
            List of generated trajectories
        """
        self.logger.info(f"Generating trajectories for {len(issues)} issues")

        trajectories = []

        for issue in issues:
            try:
                trajectory = await self.generate_trajectory(issue, detailed)
                trajectories.append(trajectory)
            except Exception as e:
                self.logger.error(
                    f"Error generating trajectory for issue {issue.get('id')}: {e}"
                )

        self.logger.info(f"Generated {len(trajectories)} trajectories")

        return trajectories

    async def save_trajectories(
        self,
        trajectories: List[BenchmarkTrajectory],
        filename: str = "trajectories.json",
    ) -> str:
        """
        Save trajectories to file.

        Args:
            trajectories: List of trajectories
            filename: Output filename

        Returns:
            Path to saved file
        """
        output_path = os.path.join(self.output_dir, filename)

        with open(output_path, "w") as f:
            json.dump([t.model_dump() for t in trajectories], f, indent=2)

        self.logger.info(f"Saved {len(trajectories)} trajectories to {output_path}")

        return output_path

    async def load_trajectories(self, filename: str) -> List[BenchmarkTrajectory]:
        """
        Load trajectories from file.

        Args:
            filename: Input filename

        Returns:
            List of trajectories
        """
        input_path = os.path.join(self.output_dir, filename)

        if not os.path.exists(input_path):
            self.logger.error(f"Trajectory file not found: {input_path}")
            return []

        with open(input_path, "r") as f:
            data = json.load(f)

        trajectories = [BenchmarkTrajectory(**item) for item in data]

        self.logger.info(f"Loaded {len(trajectories)} trajectories from {input_path}")

        return trajectories
