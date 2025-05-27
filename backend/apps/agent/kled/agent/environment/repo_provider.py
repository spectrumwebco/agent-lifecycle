"""Repository provider interface and implementations for different Git hosting services."""

import os
import abc
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from agent.utils.github import InvalidGithubURL
from agent.utils.gitee import GiteeClient, InvalidGiteeURL
from agent.utils.log import get_logger

logger = get_logger("repo-provider", emoji="🏢")


class RepoProviderType(str, Enum):
    """Supported repository provider types."""

    GITHUB = "github"
    GITEE = "gitee"
    LOCAL = "local"
    UNKNOWN = "unknown"


class RepoProvider(abc.ABC):
    """Abstract base class for repository providers."""

    @abc.abstractmethod
    def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information."""
        pass

    @abc.abstractmethod
    def list_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """List branches in a repository."""
        pass

    @abc.abstractmethod
    def get_branch(self, owner: str, repo: str, branch: str) -> Dict[str, Any]:
        """Get a specific branch in a repository."""
        pass

    @abc.abstractmethod
    def create_branch(
        self, owner: str, repo: str, branch: str, ref: str
    ) -> Dict[str, Any]:
        """Create a new branch in a repository."""
        pass

    @abc.abstractmethod
    def list_pull_requests(
        self, owner: str, repo: str, state: str = "open"
    ) -> List[Dict[str, Any]]:
        """List pull requests in a repository."""
        pass

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    def get_pull_request(self, owner: str, repo: str, number: int) -> Dict[str, Any]:
        """Get a specific pull request."""
        pass

    @abc.abstractmethod
    def list_issues(
        self, owner: str, repo: str, state: str = "open"
    ) -> List[Dict[str, Any]]:
        """List issues in a repository."""
        pass

    @abc.abstractmethod
    def get_issue(self, owner: str, repo: str, number: int) -> Dict[str, Any]:
        """Get a specific issue."""
        pass

    @abc.abstractmethod
    def create_issue(
        self, owner: str, repo: str, title: str, body: str = ""
    ) -> Dict[str, Any]:
        """Create a new issue."""
        pass

    @abc.abstractmethod
    def create_issue_comment(
        self, owner: str, repo: str, issue_number: int, body: str
    ) -> Dict[str, Any]:
        """Create a comment on an issue."""
        pass

    @staticmethod
    @abc.abstractmethod
    def parse_repo_url(url: str) -> Dict[str, str]:
        """Parse a repository URL into its components."""
        pass


class GitHubProvider(RepoProvider):
    """GitHub repository provider implementation."""

    def __init__(self, token: Optional[str] = None):
        """Initialize the GitHub provider.

        Args:
            token: GitHub personal access token. If not provided, will try to get from environment.
        """
        from agent.utils.github import GitHubClient

        self.client = GitHubClient(token)

    def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        return self.client.get_repository(owner, repo)

    def list_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        return self.client.list_branches(owner, repo)

    def get_branch(self, owner: str, repo: str, branch: str) -> Dict[str, Any]:
        return self.client.get_branch(owner, repo, branch)

    def create_branch(
        self, owner: str, repo: str, branch: str, ref: str
    ) -> Dict[str, Any]:
        return self.client.create_branch(owner, repo, branch, ref)

    def list_pull_requests(
        self, owner: str, repo: str, state: str = "open"
    ) -> List[Dict[str, Any]]:
        return self.client.list_pull_requests(owner, repo, state)

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
        return self.client.create_pull_request(
            owner, repo, title, head, base, body, draft
        )

    def get_pull_request(self, owner: str, repo: str, number: int) -> Dict[str, Any]:
        return self.client.get_pull_request(owner, repo, number)

    def list_issues(
        self, owner: str, repo: str, state: str = "open"
    ) -> List[Dict[str, Any]]:
        return self.client.list_issues(owner, repo, state)

    def get_issue(self, owner: str, repo: str, number: int) -> Dict[str, Any]:
        return self.client.get_issue(owner, repo, number)

    def create_issue(
        self, owner: str, repo: str, title: str, body: str = ""
    ) -> Dict[str, Any]:
        return self.client.create_issue(owner, repo, title, body)

    def create_issue_comment(
        self, owner: str, repo: str, issue_number: int, body: str
    ) -> Dict[str, Any]:
        return self.client.create_issue_comment(owner, repo, issue_number, body)

    @staticmethod
    def parse_repo_url(url: str) -> Dict[str, str]:
        from agent.utils.github import _parse_gh_repo_url

        return _parse_gh_repo_url(url)


class GiteeProvider(RepoProvider):
    """Gitee repository provider implementation."""

    def __init__(self, token: Optional[str] = None):
        """Initialize the Gitee provider.

        Args:
            token: Gitee personal access token. If not provided, will try to get from environment.
        """
        self.client = GiteeClient(token)

    def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        return self.client.get_repository(owner, repo)

    def list_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        return self.client.list_branches(owner, repo)

    def get_branch(self, owner: str, repo: str, branch: str) -> Dict[str, Any]:
        return self.client.get_branch(owner, repo, branch)

    def create_branch(
        self, owner: str, repo: str, branch: str, ref: str
    ) -> Dict[str, Any]:
        return self.client.create_branch(owner, repo, branch, ref)

    def list_pull_requests(
        self, owner: str, repo: str, state: str = "open"
    ) -> List[Dict[str, Any]]:
        return self.client.list_pull_requests(owner, repo, state)

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
        return self.client.create_pull_request(
            owner, repo, title, head, base, body, draft
        )

    def get_pull_request(self, owner: str, repo: str, number: int) -> Dict[str, Any]:
        return self.client.get_pull_request(owner, repo, number)

    def list_issues(
        self, owner: str, repo: str, state: str = "open"
    ) -> List[Dict[str, Any]]:
        return self.client.list_issues(owner, repo, state)

    def get_issue(self, owner: str, repo: str, number: int) -> Dict[str, Any]:
        return self.client.get_issue(owner, repo, number)

    def create_issue(
        self, owner: str, repo: str, title: str, body: str = ""
    ) -> Dict[str, Any]:
        return self.client.create_issue(owner, repo, title, body)

    def create_issue_comment(
        self, owner: str, repo: str, issue_number: int, body: str
    ) -> Dict[str, Any]:
        return self.client.create_issue_comment(owner, repo, issue_number, body)

    @staticmethod
    def parse_repo_url(url: str) -> Dict[str, str]:
        return GiteeClient.parse_gitee_url(url)


def get_repo_provider(
    provider_type: RepoProviderType, token: Optional[str] = None
) -> RepoProvider:
    """Get a repository provider instance based on the provider type.

    Args:
        provider_type: Type of repository provider
        token: Optional access token for the provider

    Returns:
        Repository provider instance

    Raises:
        ValueError: If the provider type is not supported
    """
    if provider_type == RepoProviderType.GITHUB:
        return GitHubProvider(token)
    elif provider_type == RepoProviderType.GITEE:
        return GiteeProvider(token)
    else:
        raise ValueError(f"Unsupported repository provider type: {provider_type}")


def detect_provider_from_url(url: str) -> RepoProviderType:
    """Detect the repository provider type from a URL or repository shorthand.

    Args:
        url: Repository URL or shorthand (e.g., "owner/repo")

    Returns:
        Repository provider type
    """
    if "/" in url and not url.startswith(("http", "https", "git@", "/", ".")):
        logger.debug(f"Detected GitHub shorthand format: {url}")
        return RepoProviderType.GITHUB

    try:
        GitHubProvider.parse_repo_url(url)
        return RepoProviderType.GITHUB
    except InvalidGithubURL:
        try:
            GiteeProvider.parse_repo_url(url)
            return RepoProviderType.GITEE
        except InvalidGiteeURL:
            if Path(url).exists():
                return RepoProviderType.LOCAL

            return RepoProviderType.UNKNOWN
