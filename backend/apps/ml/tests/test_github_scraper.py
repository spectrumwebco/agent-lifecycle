"""
Tests for the GitHub scraper.
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
    from apps.ml.scrapers.github_scraper import GitHubScraper, TrainingExample

    class TestGitHubScraper(unittest.TestCase):
        """Tests for the GitHub scraper."""

        def setUp(self):
            """Set up test environment."""
            self.scraper = GitHubScraper(output_dir="/tmp/github_test")

        def tearDown(self):
            """Clean up test environment."""
            if os.path.exists("/tmp/github_test"):
                for file in os.listdir("/tmp/github_test"):
                    os.remove(os.path.join("/tmp/github_test", file))
                os.rmdir("/tmp/github_test")

        @patch("apps.python_ml.scrapers.github_scraper.GitHubScraper.authenticate")
        @patch("aiohttp.ClientSession.get")
        async def test_search_repositories(self, mock_get, mock_auth):
            """Test searching for repositories."""
            mock_auth.return_value = {}

            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "items": [
                    {
                        "id": 1,
                        "full_name": "owner/repo1",
                        "stargazers_count": 200,
                        "topics": ["kubernetes", "gitops"],
                    },
                    {
                        "id": 2,
                        "full_name": "owner/repo2",
                        "stargazers_count": 150,
                        "topics": ["terraform", "kubernetes"],
                    },
                ]
            }
            mock_get.return_value.__aenter__.return_value = mock_response

            repos = await self.scraper.search_repositories(
                topics=["kubernetes", "terraform"],
                languages=["python", "go"],
                min_stars=100,
                max_repos=10,
            )

            self.assertEqual(len(repos), 2)
            self.assertEqual(repos[0]["id"], 1)
            self.assertEqual(repos[1]["id"], 2)

        @patch("apps.python_ml.scrapers.github_scraper.GitHubScraper.authenticate")
        @patch("aiohttp.ClientSession.get")
        async def test_get_issues(self, mock_get, mock_auth):
            """Test getting issues from repositories."""
            mock_auth.return_value = {}

            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json.side_effect = [
                [
                    {
                        "id": 101,
                        "number": 1,
                        "title": "Issue 1",
                        "body": "Issue 1 body",
                        "html_url": "https://github.com/owner/repo1/issues/1",
                        "created_at": "2023-01-01T00:00:00Z",
                        "closed_at": "2023-01-02T00:00:00Z",
                        "labels": [{"name": "bug"}],
                    },
                ],
                [
                    {
                        "id": 102,
                        "number": 2,
                        "title": "Issue 2",
                        "body": "Issue 2 body",
                        "html_url": "https://github.com/owner/repo2/issues/2",
                        "created_at": "2023-01-03T00:00:00Z",
                        "closed_at": "2023-01-04T00:00:00Z",
                        "labels": [{"name": "feature"}],
                    },
                ],
                {"resources": {"core": {"remaining": 100, "reset": 0}}},
            ]
            mock_get.return_value.__aenter__.return_value = mock_response

            repositories = [
                {
                    "id": 1,
                    "full_name": "owner/repo1",
                    "stargazers_count": 200,
                    "topics": ["kubernetes", "gitops"],
                },
                {
                    "id": 2,
                    "full_name": "owner/repo2",
                    "stargazers_count": 150,
                    "topics": ["terraform", "kubernetes"],
                },
            ]

            issues = await self.scraper.get_issues(
                repositories=repositories,
                state="closed",
                max_issues_per_repo=10,
                include_pull_requests=False,
            )

            self.assertEqual(len(issues), 2)
            self.assertEqual(issues[0]["id"], 101)
            self.assertEqual(issues[1]["id"], 102)
            self.assertEqual(issues[0]["repository"]["id"], 1)
            self.assertEqual(issues[1]["repository"]["id"], 2)

    if __name__ == "__main__":
        unittest.main()

except ImportError as e:
    print(f"Import error: {e}")
    print("Skipping GitHub scraper tests due to missing dependencies")
