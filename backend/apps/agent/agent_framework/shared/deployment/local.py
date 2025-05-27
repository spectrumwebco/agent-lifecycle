import logging
from typing import Any

from typing_extensions import Self

from apps.agent.agent_framework.deployment.abstract import AbstractDeployment
from apps.agent.agent_framework.deployment.config import LocalDeploymentConfig
from apps.agent.agent_framework.deployment.hooks.abstract import (
    CombinedDeploymentHook,
    DeploymentHook,
)
from apps.agent.agent_framework.exceptions import DeploymentNotStartedError
from apps.agent.agent_framework.runtime.abstract import IsAliveResponse
from apps.agent.agent_framework.runtime.local import LocalRuntime
from apps.agent.agent_framework.utils.log import get_logger

__all__ = ["LocalDeployment", "LocalDeploymentConfig"]


class LocalDeployment(AbstractDeployment):
    def __init__(
        self,
        *,
        logger: logging.Logger | None = None,
        **kwargs: Any,
    ):
        """The most boring of the deployment classes.
        This class does nothing but wrap around `Runtime` so you can switch out
        your deployment method.

        Args:
            **kwargs: Keyword arguments (see `LocalDeploymentConfig` for details).
        """
        self._runtime = None
        self.logger = logger or get_logger("rex-deploy")
        self._config = LocalDeploymentConfig(**kwargs)
        self._hooks = CombinedDeploymentHook()

    def add_hook(self, hook: DeploymentHook):
        self._hooks.add_hook(hook)

    @classmethod
    def from_config(cls, config: LocalDeploymentConfig) -> Self:
        return cls(**config.model_dump())

    async def is_alive(self, *, timeout: float | None = None) -> IsAliveResponse:
        """Checks if the runtime is alive. The return value can be
        tested with bool().

        Raises:
            DeploymentNotStartedError: If the deployment was not started.
        """
        if self._runtime is None:
            return IsAliveResponse(is_alive=False, message="Runtime is None.")
        return await self._runtime.is_alive(timeout=timeout)

    async def start(self):
        """Starts the runtime."""
        self._runtime = LocalRuntime(logger=self.logger)

    async def stop(self):
        """Stops the runtime."""
        if self._runtime is not None:
            await self._runtime.close()
            self._runtime = None

    @property
    def runtime(self) -> LocalRuntime:
        """Returns the runtime if running.

        Raises:
            DeploymentNotStartedError: If the deployment was not started.
        """
        if self._runtime is None:
            raise DeploymentNotStartedError()
        return self._runtime
