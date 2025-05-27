"""
Gitee scraper for historical issues.

This module provides functionality to scrape Gitee repositories
for historical issues and format them for benchmarking and trajectory generation.
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field

from ..integration.eventstream_integration import (
    event_stream,
    Event,
    EventType,
    EventSource,
)


class GiteeTrainingExample(BaseModel):
    """Training example for ML models."""

    input: str = Field(..., description="Input text")
    output: str = Field(..., description="Output text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    trajectory: List[Dict[str, str]] = Field(
        default_factory=list, description="Trajectory steps"
    )


class GiteeScraper:
    """Gitee scraper for collecting historical issues."""

    def __init__(
        self,
        output_dir: str = "./data/gitee",
        gitee_token: Optional[str] = None,
    ):
        """
        Initialize the Gitee scraper.

        Args:
            output_dir: Directory to save scraped data
            gitee_token: Gitee API token
        """
        self.gitee_token = gitee_token or os.environ.get("GITEE_TOKEN")
        self.output_dir = output_dir

        os.makedirs(output_dir, exist_ok=True)

        self.logger = logging.getLogger("GiteeScraper")

    async def authenticate(self):
        """
        Authenticate with Gitee API.

        Returns:
            Authentication headers
        """
        if not self.gitee_token:
            self.logger.warning("No Gitee token provided, using unauthenticated access")
            return {}

        return {
            "Authorization": f"token {self.gitee_token}",
            "Accept": "application/json",
        }

    async def search_repositories(
        self,
        topics: List[str],
        languages: Optional[List[str]] = None,
        min_stars: int = 100,
        max_repos: int = 25,
    ) -> List[Dict[str, Any]]:
        """
        Search for repositories based on topics and languages.

        Args:
            topics: List of topics to search for
            languages: Optional list of languages to filter by
            min_stars: Minimum number of stars
            max_repos: Maximum number of repositories to return

        Returns:
            List of repositories
        """
        import aiohttp

        self.logger.info(f"Searching for repositories with topics: {topics}")

        headers = await self.authenticate()
        repositories = []

        async with aiohttp.ClientSession() as session:
            for topic in topics:
                query_params = {
                    "q": topic,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": min(max_repos, 100),
                    "page": 1,
                }

                if languages:
                    for language in languages:
                        self.logger.info(f"Searching with topic: {topic}")

                        url = "https://gitee.com/api/v5/search/repositories"
                        async with session.get(
                            url, headers=headers, params=query_params
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                language_repos = [
                                    repo
                                    for repo in data.get("items", [])
                                    if repo.get("language") == language
                                ]
                                repositories.extend(language_repos)
                                self.logger.info(
                                    f"Found {len(language_repos)} repos for {topic} in {language}"
                                )
                            else:
                                self.logger.error(
                                    f"Error searching repositories: {response.status}"
                                )
                else:
                    self.logger.info(f"Searching with topic: {topic}")

                    url = "https://gitee.com/api/v5/search/repositories"
                    async with session.get(
                        url, headers=headers, params=query_params
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            repositories.extend(data.get("items", []))
                            self.logger.info(
                                f"Found {len(data.get('items', []))} repositories for {topic}"
                            )
                        else:
                            self.logger.error(
                                f"Error searching repositories: {response.status}"
                            )

        unique_repos = {}
        for repo in repositories:
            repo_id = repo["id"]
            if repo_id not in unique_repos:
                unique_repos[repo_id] = repo

        repositories = list(unique_repos.values())
        repositories.sort(key=lambda x: x.get("stargazers_count", 0), reverse=True)
        repositories = repositories[:max_repos]

        self.logger.info(f"Found {len(repositories)} unique repositories")

        if hasattr(self, "event_stream") and event_stream:
            event_data = {
                "action": "scrape_gitee_repositories",
                "count": len(repositories),
                "topics": topics,
                "languages": languages,
            }
            try:
                await event_stream.publish(
                    Event.new(EventType.DATASOURCE, EventSource.ML, event_data)
                )
            except Exception as e:
                self.logger.error(f"Error publishing event: {e}")

        return repositories

    async def get_issues(
        self,
        repositories: List[Dict[str, Any]],
        state: str = "closed",
        max_issues_per_repo: int = 50,
        include_pull_requests: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get issues from repositories.

        Args:
            repositories: List of repositories
            state: Issue state (open, closed, all)
            max_issues_per_repo: Maximum number of issues per repository
            include_pull_requests: Whether to include pull requests

        Returns:
            List of issues
        """
        import aiohttp

        self.logger.info(f"Getting issues from {len(repositories)} repositories")

        headers = await self.authenticate()
        all_issues = []

        async with aiohttp.ClientSession() as session:
            for repo in repositories:
                owner = repo["owner"]["login"]
                name = repo["name"]

                self.logger.info(f"Getting issues from {owner}/{name}")

                url = f"https://gitee.com/api/v5/repos/{owner}/{name}/issues"
                params = {
                    "state": state,
                    "sort": "created",
                    "direction": "desc",
                    "per_page": min(max_issues_per_repo, 100),
                    "page": 1,
                }

                try:
                    async with session.get(
                        url, headers=headers, params=params
                    ) as response:
                        if response.status == 200:
                            issues = await response.json()

                            if not include_pull_requests:
                                issues = [
                                    issue
                                    for issue in issues
                                    if not issue.get("pull_request")
                                ]

                            for issue in issues:
                                issue["repository"] = repo

                            all_issues.extend(issues)

                            self.logger.info(
                                f"Got {len(issues)} issues from {owner}/{name}"
                            )
                        else:
                            self.logger.error(
                                f"Error getting issues: {response.status}"
                            )

                    await asyncio.sleep(0.5)  # Gitee has stricter rate limits

                except Exception as e:
                    self.logger.error(f"Error getting issues from {owner}/{name}: {e}")

        self.logger.info(f"Got {len(all_issues)} issues in total")

        if hasattr(self, "event_stream") and event_stream:
            event_data = {
                "action": "scrape_gitee_issues",
                "count": len(all_issues),
                "state": state,
            }
            try:
                await event_stream.publish(
                    Event.new(EventType.DATASOURCE, EventSource.ML, event_data)
                )
            except Exception as e:
                self.logger.error(f"Error publishing event: {e}")

        return all_issues

    async def save_issues(
        self, issues: List[Dict[str, Any]], filename: str = "gitee_issues.json"
    ) -> str:
        """
        Save issues to file.

        Args:
            issues: List of issues
            filename: Output filename

        Returns:
            Path to saved file
        """
        output_path = os.path.join(self.output_dir, filename)

        with open(output_path, "w") as f:
            json.dump(issues, f, indent=2)

        self.logger.info(f"Saved {len(issues)} issues to {output_path}")

        return output_path

    async def generate_trajectories(
        self, issues: List[Dict[str, Any]], detailed: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate realistic trajectories for issues.

        Args:
            issues: List of issues
            detailed: Whether to generate detailed trajectories

        Returns:
            List of issues with trajectories
        """
        self.logger.info(f"Generating trajectories for {len(issues)} issues")

        for issue in issues:
            if "repository" not in issue or not issue.get("body"):
                continue

            repo = issue["repository"]
            repo_name = f"{repo['owner']['login']}/{repo['name']}"
            issue_number = issue["number"]
            issue_title = issue["title"]
            issue_body = issue["body"]

            trajectory = [
                {
                    "action": "read_issue",
                    "observation": f"Issue #{issue_number}: {issue_title}",
                    "response": "I'll analyze this issue to find a solution.",
                },
                {
                    "action": "analyze_issue",
                    "observation": issue_body,
                    "response": "Based on the issue description, I need to understand the problem and find a solution.",
                },
            ]

            if detailed:
                if "error" in issue_body.lower() or "bug" in issue_body.lower():
                    trajectory.extend(
                        [
                            {
                                "action": "search_code",
                                "observation": f"Searching for relevant code in {repo_name}...",
                                "response": "I found the code responsible for this issue. Let me analyze it.",
                            },
                            {
                                "action": "analyze_error",
                                "observation": "Error details and stack trace...",
                                "response": "I've identified the root cause of the error. It's related to [specific component].",
                            },
                        ]
                    )
                elif (
                    "feature" in issue_body.lower()
                    or "enhancement" in issue_body.lower()
                ):
                    trajectory.extend(
                        [
                            {
                                "action": "plan_implementation",
                                "observation": "Planning the implementation for this feature...",
                                "response": "I'll need to modify the following components: [component list]",
                            },
                            {
                                "action": "design_architecture",
                                "observation": "Designing the architecture for this feature...",
                                "response": "Here's my proposed architecture design: [design details]",
                            },
                        ]
                    )

                trajectory.extend(
                    [
                        {
                            "action": "implement_solution",
                            "observation": "Implementing the solution...",
                            "response": "I've implemented a solution by [description of changes].",
                        },
                        {
                            "action": "test_solution",
                            "observation": "Testing the solution...",
                            "response": "Tests are passing. The solution works as expected.",
                        },
                        {
                            "action": "create_pr",
                            "observation": f"Creating a PR for {repo_name}...",
                            "response": "PR created successfully. The issue has been resolved.",
                        },
                    ]
                )
            else:
                trajectory.extend(
                    [
                        {
                            "action": "implement_solution",
                            "observation": "Testing the solution...",
                            "response": "The solution has been implemented and tested.",
                        },
                        {
                            "action": "verify_solution",
                            "observation": "The solution has been implemented and tested.",
                            "response": "The issue has been resolved successfully.",
                        },
                    ]
                )

            issue["trajectory"] = trajectory

        self.logger.info(f"Generated trajectories for {len(issues)} issues")

        return issues

    async def format_for_training(
        self, issues: List[Dict[str, Any]], filename: str = "gitee_training_data.json"
    ) -> str:
        """
        Format issues for training.

        Args:
            issues: List of issues
            filename: Output filename

        Returns:
            Path to saved file
        """
        training_data = []

        issues_with_trajectories = await self.generate_trajectories(issues)

        for issue in issues_with_trajectories:
            if "repository" not in issue or not issue.get("body"):
                continue

            repo = issue["repository"]
            repo_name = f"{repo['owner']['login']}/{repo['name']}"
            repo_topics = repo.get("topics", [])

            issue_title = issue["title"]
            issue_body = issue["body"]
            issue_number = issue["number"]
            issue_url = issue["html_url"]
            issue_created_at = issue["created_at"]
            issue_closed_at = issue.get("closed_at")
            issue_labels = [label["name"] for label in issue.get("labels", [])]

            input_text = f"Repository: {repo_name}\n"

            if repo_topics:
                input_text += f"Topics: {', '.join(repo_topics)}\n"

            input_text += f"Issue Title: {issue_title}\n"
            input_text += f"Issue Description:\n{issue_body}\n"

            output_text = "Issue resolved successfully."

            metadata = {
                "issue_id": issue["id"],
                "issue_number": issue_number,
                "repository": repo_name,
                "url": issue_url,
                "created_at": issue_created_at,
                "closed_at": issue_closed_at,
                "labels": issue_labels,
                "source": "gitee",
            }

            trajectory = issue.get("trajectory", [])

            training_example = GiteeTrainingExample(
                input=input_text,
                output=output_text,
                metadata=metadata,
                trajectory=trajectory,
            )

            training_data.append(training_example.model_dump())

        output_path = os.path.join(self.output_dir, filename)

        with open(output_path, "w") as f:
            json.dump(training_data, f, indent=2)

        self.logger.info(
            f"Saved {len(training_data)} training examples to {output_path}"
        )

        return output_path

    async def scrape_and_save(
        self,
        topics: List[str] = ["gitops", "terraform", "kubernetes", "k8s"],
        languages: Optional[List[str]] = None,
        min_stars: int = 100,
        max_repos: int = 25,
        max_issues_per_repo: int = 50,
        include_pull_requests: bool = False,
    ) -> Tuple[str, str]:
        """
        Scrape repositories and issues, and save them to files.

        Args:
            topics: List of topics to search for
            languages: Optional list of languages to filter by
            min_stars: Minimum number of stars
            max_repos: Maximum number of repositories to return
            max_issues_per_repo: Maximum number of issues per repository
            include_pull_requests: Whether to include pull requests

        Returns:
            Tuple of (issues_path, training_data_path)
        """
        repositories = await self.search_repositories(
            topics=topics,
            languages=languages,
            min_stars=min_stars,
            max_repos=max_repos,
        )

        issues = await self.get_issues(
            repositories=repositories,
            state="closed",
            max_issues_per_repo=max_issues_per_repo,
            include_pull_requests=include_pull_requests,
        )

        issues_path = await self.save_issues(issues)

        training_data_path = await self.format_for_training(issues)

        return issues_path, training_data_path
