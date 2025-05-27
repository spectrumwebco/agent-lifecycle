"""
Tests for the Gitee scraper.
"""

import os
import json
import asyncio
import unittest
from unittest.mock import patch, MagicMock
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from apps.ml.scrapers.gitee_scraper import GiteeScraper


@pytest.mark.asyncio
async def test_gitee_scraper_init():
    """Test GiteeScraper initialization."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        scraper = GiteeScraper(output_dir=temp_dir)
        assert os.path.exists(temp_dir)
        assert scraper.gitee_token is None


@pytest.mark.asyncio
async def test_authenticate_without_token():
    """Test authentication without token."""
    scraper = GiteeScraper()
    headers = await scraper.authenticate()
    assert headers == {}


@pytest.mark.asyncio
async def test_authenticate_with_token():
    """Test authentication with token."""
    with patch.dict(os.environ, {"GITEE_TOKEN": "test_token"}):
        scraper = GiteeScraper()
        headers = await scraper.authenticate()
        assert headers == {
            "Authorization": "token test_token",
            "Accept": "application/json",
        }


@pytest.mark.asyncio
async def test_search_repositories():
    """Test searching repositories."""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_json():
            return {
                "items": [
                    {
                        "id": 1,
                        "name": "test-repo",
                        "full_name": "owner/test-repo",
                        "owner": {"login": "owner"},
                        "html_url": "https://gitee.com/owner/test-repo",
                        "description": "Test repository",
                        "stargazers_count": 150,
                        "language": "Python",
                        "topics": ["terraform", "gitops"],
                    }
                ]
            }

        mock_response.json = mock_json

        mock_session_context = MagicMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.return_value = mock_response

        mock_session().__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.return_value = mock_response

        scraper = GiteeScraper()
        repos = await scraper.search_repositories(
            topics=["terraform"], languages=["Python"], max_repos=1
        )

        assert len(repos) == 1
        assert repos[0]["name"] == "test-repo"
        assert repos[0]["language"] == "Python"


@pytest.mark.asyncio
async def test_get_issues():
    """Test getting issues from repositories."""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_json():
            return [
                {
                    "id": 101,
                    "number": 42,
                    "title": "Test Issue",
                    "body": "This is a test issue",
                    "html_url": "https://gitee.com/owner/test-repo/issues/42",
                    "created_at": "2023-01-01T00:00:00Z",
                    "closed_at": "2023-01-02T00:00:00Z",
                    "labels": [{"name": "bug"}],
                }
            ]

        mock_response.json = mock_json

        mock_session_context = MagicMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.return_value = mock_response

        mock_session().__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.return_value = mock_response

        scraper = GiteeScraper()
        repositories = [
            {
                "id": 1,
                "name": "test-repo",
                "owner": {"login": "owner"},
                "html_url": "https://gitee.com/owner/test-repo",
            }
        ]

        issues = await scraper.get_issues(
            repositories=repositories,
            state="closed",
            max_issues_per_repo=10,
            include_pull_requests=False,
        )

        assert len(issues) == 1
        assert issues[0]["number"] == 42
        assert issues[0]["title"] == "Test Issue"
        assert "repository" in issues[0]


@pytest.mark.asyncio
async def test_save_issues():
    """Test saving issues to file."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        scraper = GiteeScraper(output_dir=temp_dir)

        issues = [
            {
                "id": 101,
                "number": 42,
                "title": "Test Issue",
                "body": "This is a test issue",
                "repository": {
                    "id": 1,
                    "name": "test-repo",
                    "owner": {"login": "owner"},
                },
            }
        ]

        output_path = await scraper.save_issues(issues, filename="test_issues.json")

        assert os.path.exists(output_path)

        with open(output_path, "r") as f:
            loaded_issues = json.load(f)

        assert len(loaded_issues) == 1
        assert loaded_issues[0]["number"] == 42


@pytest.mark.asyncio
async def test_generate_trajectories():
    """Test generating trajectories for issues."""
    scraper = GiteeScraper()

    issues = [
        {
            "id": 101,
            "number": 42,
            "title": "Test Bug",
            "body": "This is a bug that needs fixing",
            "repository": {
                "id": 1,
                "name": "test-repo",
                "owner": {"login": "owner"},
            },
        },
        {
            "id": 102,
            "number": 43,
            "title": "Feature Request",
            "body": "Please add this feature enhancement",
            "repository": {
                "id": 1,
                "name": "test-repo",
                "owner": {"login": "owner"},
            },
        },
    ]

    issues_with_trajectories = await scraper.generate_trajectories(issues)

    assert len(issues_with_trajectories) == 2
    assert "trajectory" in issues_with_trajectories[0]
    assert "trajectory" in issues_with_trajectories[1]

    bug_trajectory = issues_with_trajectories[0]["trajectory"]
    bug_actions = [step["action"] for step in bug_trajectory]
    assert "analyze_error" in bug_actions

    feature_trajectory = issues_with_trajectories[1]["trajectory"]
    feature_actions = [step["action"] for step in feature_trajectory]
    assert "plan_implementation" in feature_actions


@pytest.mark.asyncio
async def test_format_for_training():
    """Test formatting issues for training."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        scraper = GiteeScraper(output_dir=temp_dir)

        issues = [
            {
                "id": 101,
                "number": 42,
                "title": "Test Issue",
                "body": "This is a test issue",
                "html_url": "https://gitee.com/owner/test-repo/issues/42",
                "created_at": "2023-01-01T00:00:00Z",
                "closed_at": "2023-01-02T00:00:00Z",
                "labels": [{"name": "bug"}],
                "repository": {
                    "id": 1,
                    "name": "test-repo",
                    "owner": {"login": "owner"},
                    "topics": ["terraform"],
                },
            }
        ]

        output_path = await scraper.format_for_training(
            issues, filename="test_training.json"
        )

        assert os.path.exists(output_path)

        with open(output_path, "r") as f:
            training_data = json.load(f)

        assert len(training_data) == 1
        assert "input" in training_data[0]
        assert "output" in training_data[0]
        assert "metadata" in training_data[0]
        assert "trajectory" in training_data[0]
        assert training_data[0]["metadata"]["source"] == "gitee"


if __name__ == "__main__":
    asyncio.run(pytest.main(["-xvs", __file__]))
