import asyncio
import os
from pathlib import Path
from typing import Any, Literal, Protocol

from git import InvalidGitRepositoryError
from git import Repo as GitRepo
from pydantic import BaseModel, ConfigDict, Field
from ..swerex.deployment.abstract import AbstractDeployment
from ..swerex.runtime.abstract import Command, UploadRequest
from typing_extensions import Self

from ..utils.github import _parse_gh_repo_url
from ..utils.gitee import InvalidGiteeURL

from ..utils.log import get_logger

logger = get_logger("swea-config", emoji="🔧")


class Repo(Protocol):
    """Protocol for repository configurations."""

    base_commit: str
    repo_name: str

    def copy(self, deployment: AbstractDeployment): ...

    def get_reset_commands(self) -> list[str]: ...


def _get_git_reset_commands(base_commit: str) -> list[str]:
    return [
        "git status",
        "git restore .",
        f"git reset --hard {base_commit}",
        "git clean -fdq",
    ]


class PreExistingRepoConfig(BaseModel):
    """Use this to specify a repository that already exists on the deployment.
    This is important because we need to cd to the repo before running the agent.

    Note: The repository must be at the root of the deployment.
    """

    repo_name: str
    """The repo name (the repository must be located at the root of the deployment)."""
    base_commit: str = Field(default="HEAD")
    """The commit to reset the repository to. The default is HEAD,
    i.e., the latest commit. You can also set this to a branch name (e.g., `dev`),
    a tag (e.g., `v0.1.0`), or a commit hash (e.g., `a4464baca1f`).
    SWE-agent will then start from this commit when trying to solve the problem.
    """

    type: Literal["preexisting"] = "preexisting"
    """Discriminator for (de)serialization/CLI. Do not change."""

    model_config = ConfigDict(extra="forbid")

    def copy(self, deployment: AbstractDeployment):
        """Does nothing."""
        pass

    def get_reset_commands(self) -> list[str]:
        """Issued after the copy operation or when the environment is reset."""
        return _get_git_reset_commands(self.base_commit)


class LocalRepoConfig(BaseModel):
    path: Path
    base_commit: str = Field(default="HEAD")
    """The commit to reset the repository to. The default is HEAD,
    i.e., the latest commit. You can also set this to a branch name (e.g., `dev`),
    a tag (e.g., `v0.1.0`), or a commit hash (e.g., `a4464baca1f`).
    SWE-agent will then start from this commit when trying to solve the problem.
    """

    type: Literal["local"] = "local"
    """Discriminator for (de)serialization/CLI. Do not change."""

    model_config = ConfigDict(extra="forbid")

    @property
    def repo_name(self) -> str:
        """Set automatically based on the repository name. Cannot be set."""
        return Path(self.path).resolve().name.replace(" ", "-").replace("'", "")

    # Let's not make this a model validator, because it leads to cryptic errors.
    # Let's just check during copy instead.
    def check_valid_repo(self) -> Self:
        try:
            repo = GitRepo(self.path, search_parent_directories=True)
        except InvalidGitRepositoryError as e:
            msg = f"Could not find git repository at {self.path=}."
            raise ValueError(msg) from e
        if repo.is_dirty() and "PYTEST_CURRENT_TEST" not in os.environ:
            msg = f"Local git repository {self.path} is dirty. Please commit or stash changes."
            raise ValueError(msg)
        return self

    def copy(self, deployment: AbstractDeployment):
        self.check_valid_repo()
        asyncio.run(
            deployment.runtime.upload(
                UploadRequest(
                    source_path=str(self.path), target_path=f"/{self.repo_name}"
                )
            )
        )
        r = asyncio.run(
            deployment.runtime.execute(
                Command(command=f"chown -R root:root {self.repo_name}", shell=True)
            )
        )
        if r.exit_code != 0:
            msg = f"Failed to change permissions on copied repository (exit code: {r.exit_code}, stdout: {r.stdout}, stderr: {r.stderr})"
            raise RuntimeError(msg)

    def get_reset_commands(self) -> list[str]:
        """Issued after the copy operation or when the environment is reset."""
        return _get_git_reset_commands(self.base_commit)


class GithubRepoConfig(BaseModel):
    github_url: str

    base_commit: str = Field(default="HEAD")
    """The commit to reset the repository to. The default is HEAD,
    i.e., the latest commit. You can also set this to a branch name (e.g., `dev`),
    a tag (e.g., `v0.1.0`), or a commit hash (e.g., `a4464baca1f`).
    SWE-agent will then start from this commit when trying to solve the problem.
    """

    clone_timeout: float = 500
    """Timeout for git clone operation."""

    type: Literal["github"] = "github"
    """Discriminator for (de)serialization/CLI. Do not change."""

    model_config = ConfigDict(extra="forbid")

    def model_post_init(self, __context: Any) -> None:
        if self.github_url.count("/") == 1:
            self.github_url = f"https://github.com/{self.github_url}"

    @property
    def repo_name(self) -> str:
        org, repo = _parse_gh_repo_url(self.github_url)
        return f"{org}__{repo}"

    def _get_url_with_token(self, token: str) -> str:
        """Prepend github token to URL"""
        if not token:
            return self.github_url
        if "@" in self.github_url:
            logger.warning("Cannot prepend token to URL. '@' found in URL")
            return self.github_url
        _, _, url_no_protocol = self.github_url.partition("://")
        return f"https://{token}@{url_no_protocol}"

    def copy(self, deployment: AbstractDeployment):
        """Clones the repository to the sandbox."""
        base_commit = self.base_commit
        github_token = os.getenv("GITHUB_TOKEN", "")
        url = self._get_url_with_token(github_token)
        asyncio.run(
            deployment.runtime.execute(
                Command(
                    command=" && ".join(
                        (
                            f"mkdir {self.repo_name}",
                            f"cd {self.repo_name}",
                            "git init",
                            f"git remote add origin {url}",
                            f"git fetch --depth 1 origin {base_commit}",
                            "git checkout FETCH_HEAD",
                            "cd ..",
                        )
                    ),
                    timeout=self.clone_timeout,
                    shell=True,
                    check=True,
                )
            ),
        )

    def get_reset_commands(self) -> list[str]:
        """Issued after the copy operation or when the environment is reset."""
        return _get_git_reset_commands(self.base_commit)


class GiteeRepoConfig(BaseModel):
    gitee_url: str

    base_commit: str = Field(default="HEAD")
    """The commit to reset the repository to. The default is HEAD,
    i.e., the latest commit. You can also set this to a branch name (e.g., `dev`),
    a tag (e.g., `v0.1.0`), or a commit hash (e.g., `a4464baca1f`).
    SWE-agent will then start from this commit when trying to solve the problem.
    """

    clone_timeout: float = 500
    """Timeout for git clone operation."""

    type: Literal["gitee"] = "gitee"
    """Discriminator for (de)serialization/CLI. Do not change."""

    model_config = ConfigDict(extra="forbid")

    @property
    def repo_name(self) -> str:
        from agent.utils.gitee import GiteeClient

        try:
            parsed = GiteeClient.parse_gitee_url(self.gitee_url)
            return f"{parsed['owner']}__{parsed['repo']}"
        except InvalidGiteeURL as e:
            logger.error(f"Failed to parse Gitee URL {self.gitee_url}: {e}")
            return "gitee_repo"

    def _get_url_with_token(self, token: str) -> str:
        """Prepend Gitee token to URL"""
        if not token:
            return self.gitee_url
        if "@" in self.gitee_url:
            logger.warning("Cannot prepend token to URL. '@' found in URL")
            return self.gitee_url
        _, _, url_no_protocol = self.gitee_url.partition("://")
        return f"https://{token}@{url_no_protocol}"

    def copy(self, deployment: AbstractDeployment):
        """Clones the repository to the sandbox."""
        base_commit = self.base_commit
        gitee_token = os.getenv("GITEE_ACCESS_TOKEN", "")  # Use GITEE_ACCESS_TOKEN
        url = self._get_url_with_token(gitee_token)
        asyncio.run(
            deployment.runtime.execute(
                Command(
                    command=" && ".join(
                        (
                            f"mkdir {self.repo_name}",
                            f"cd {self.repo_name}",
                            "git init",
                            f"git remote add origin {url}",
                            f"git fetch --depth 1 origin {base_commit}",
                            "git checkout FETCH_HEAD",
                            "cd ..",
                        )
                    ),
                    timeout=self.clone_timeout,
                    shell=True,
                    check=True,
                )
            ),
        )

    def get_reset_commands(self) -> list[str]:
        """Issued after the copy operation or when the environment is reset."""
        return _get_git_reset_commands(self.base_commit)


RepoConfig = (
    LocalRepoConfig | GithubRepoConfig | GiteeRepoConfig | PreExistingRepoConfig
)


def repo_from_simplified_input(
    *,
    input: str,
    base_commit: str = "HEAD",
    type: Literal["local", "github", "gitee", "preexisting", "auto"] = "auto",
) -> RepoConfig:
    """Get repo config from a simplified input.

    Args:
        input: Local path, GitHub URL, or Gitee URL
        type: The type of repo. Set to "auto" to automatically detect the type
            (does not work for preexisting repos).
    """
    if type == "local":
        return LocalRepoConfig(path=Path(input), base_commit=base_commit)
    if type == "github":
        return GithubRepoConfig(github_url=input, base_commit=base_commit)
    if type == "gitee":
        return GiteeRepoConfig(gitee_url=input, base_commit=base_commit)
    if type == "preexisting":
        return PreExistingRepoConfig(repo_name=input, base_commit=base_commit)
    if type == "auto":
        from ..repo_provider import (
            detect_provider_from_url,
            RepoProviderType,
        )

        detected_type = detect_provider_from_url(input)
        if detected_type == RepoProviderType.GITHUB:
            return GithubRepoConfig(github_url=input, base_commit=base_commit)
        elif detected_type == RepoProviderType.GITEE:
            return GiteeRepoConfig(gitee_url=input, base_commit=base_commit)
        elif detected_type == RepoProviderType.LOCAL:
            if Path(input).exists():
                return LocalRepoConfig(path=Path(input), base_commit=base_commit)
            else:
                if "/" in input and not input.startswith(("http", ".", "/")):
                    logger.info(f"Assuming '{input}' is a GitHub repository shorthand.")
                    return GithubRepoConfig(
                        github_url=f"https://github.com/{input}",
                        base_commit=base_commit,
                    )
                else:
                    msg = f"Could not automatically determine repository type for input: {input}"
                    raise ValueError(msg)
        else:  # UNKNOWN
            msg = (
                f"Could not automatically determine repository type for input: {input}"
            )
            raise ValueError(msg)

    msg = f"Unknown repo type: {type}"
    raise ValueError(msg)
