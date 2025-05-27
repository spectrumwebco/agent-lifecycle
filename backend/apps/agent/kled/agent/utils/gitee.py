"""Gitee API client for repository management."""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
import requests
from urllib.parse import urlparse

from ..utils.log import get_logger

logger = get_logger("gitee-api", emoji="🐙")


class InvalidGiteeURL(Exception):
    """Raised when a Gitee URL is invalid."""

    pass


class GiteeAPIError(Exception):
    """Raised when the Gitee API returns an error."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class GiteeClient:
    """Client for interacting with the Gitee API."""

    BASE_URL = "https://gitee.com/api/v5"

    def __init__(self, access_token: Optional[str] = None):
        """Initialize the Gitee client.

        Args:
            access_token: Gitee personal access token. If not provided, will try to get from environment.
        """
        self.access_token = access_token or os.environ.get("GITEE_ACCESS_TOKEN")
        if not self.access_token:
            logger.warning("No Gitee access token provided. Some API calls may fail.")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the Gitee API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Form data
            json_data: JSON data

        Returns:
            Response data as dictionary

        Raises:
            GiteeAPIError: If the API returns an error
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        if self.access_token:
            if params is None:
                params = {}
            params["access_token"] = self.access_token

        try:
            response = requests.request(
                method=method, url=url, params=params, data=data, json=json_data
            )

            response.raise_for_status()

            if response.status_code == 204:  # No content
                return {}

            return response.json()
        except requests.exceptions.RequestException as e:
            status_code = (
                getattr(e.response, "status_code", None)
                if hasattr(e, "response")
                else None
            )
            response_data = {}

            if hasattr(e, "response") and e.response is not None:
                try:
                    response_data = e.response.json()
                except ValueError:
                    response_data = {"message": e.response.text}

            error_message = response_data.get("message", str(e))
            raise GiteeAPIError(
                error_message, status_code=status_code, response=response_data
            ) from e

    def get_user(self) -> Dict[str, Any]:
        """Get the authenticated user's information."""
        return self._make_request("GET", "/user")

    def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get a repository by owner and name."""
        return self._make_request("GET", f"/repos/{owner}/{repo}")

    def create_repository(
        self, name: str, description: str = "", private: bool = False
    ) -> Dict[str, Any]:
        """Create a new repository."""
        data = {
            "name": name,
            "description": description,
            "private": private,
            "has_issues": True,
            "has_wiki": True,
        }
        return self._make_request("POST", "/user/repos", json_data=data)

    def list_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """List branches in a repository."""
        return self._make_request("GET", f"/repos/{owner}/{repo}/branches")

    def get_branch(self, owner: str, repo: str, branch: str) -> Dict[str, Any]:
        """Get a specific branch in a repository."""
        return self._make_request("GET", f"/repos/{owner}/{repo}/branches/{branch}")

    def create_branch(
        self, owner: str, repo: str, branch: str, ref: str
    ) -> Dict[str, Any]:
        """Create a new branch in a repository."""
        data = {"refs": f"refs/heads/{branch}", "sha": ref}
        return self._make_request(
            "POST", f"/repos/{owner}/{repo}/branches", json_data=data
        )

    def list_pull_requests(
        self, owner: str, repo: str, state: str = "open"
    ) -> List[Dict[str, Any]]:
        """List pull requests in a repository."""
        params = {"state": state}
        return self._make_request("GET", f"/repos/{owner}/{repo}/pulls", params=params)

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: str = "",
        draft: bool = False,
    ) -> Dict[str, Any]:
        """Create a new pull request."""
        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": body,
            "draft": draft,
        }
        return self._make_request(
            "POST", f"/repos/{owner}/{repo}/pulls", json_data=data
        )

    def get_pull_request(self, owner: str, repo: str, number: int) -> Dict[str, Any]:
        """Get a specific pull request."""
        return self._make_request("GET", f"/repos/{owner}/{repo}/pulls/{number}")

    def list_issues(
        self, owner: str, repo: str, state: str = "open"
    ) -> List[Dict[str, Any]]:
        """List issues in a repository."""
        params = {"state": state}
        return self._make_request("GET", f"/repos/{owner}/{repo}/issues", params=params)

    def get_issue(self, owner: str, repo: str, number: int) -> Dict[str, Any]:
        """Get a specific issue."""
        return self._make_request("GET", f"/repos/{owner}/{repo}/issues/{number}")

    def create_issue(
        self, owner: str, repo: str, title: str, body: str = ""
    ) -> Dict[str, Any]:
        """Create a new issue."""
        data = {"title": title, "body": body}
        return self._make_request(
            "POST", f"/repos/{owner}/{repo}/issues", json_data=data
        )

    def create_issue_comment(
        self, owner: str, repo: str, issue_number: int, body: str
    ) -> Dict[str, Any]:
        """Create a comment on an issue."""
        data = {"body": body}
        return self._make_request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            json_data=data,
        )

    @staticmethod
    def parse_gitee_url(url: str) -> Dict[str, str]:
        """Parse a Gitee URL into its components.

        Args:
            url: Gitee URL (e.g., https://gitee.com/owner/repo)

        Returns:
            Dictionary with owner and repo

        Raises:
            InvalidGiteeURL: If the URL is not a valid Gitee URL
        """
        parsed = urlparse(url)

        if parsed.netloc != "gitee.com" or not parsed.path:
            raise InvalidGiteeURL(f"Not a valid Gitee URL: {url}")

        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) < 2:
            raise InvalidGiteeURL(f"Not a valid Gitee repository URL: {url}")

        owner, repo = path_parts[0], path_parts[1]

        if repo.endswith(".git"):
            repo = repo[:-4]

        return {"owner": owner, "repo": repo}

    @classmethod
    def from_environment(cls) -> "GiteeClient":
        """Create a GiteeClient from environment variables."""
        access_token = os.environ.get("GITEE_ACCESS_TOKEN")
        return cls(access_token=access_token)
