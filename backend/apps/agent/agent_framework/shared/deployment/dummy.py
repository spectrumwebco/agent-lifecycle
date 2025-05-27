import logging
from typing import Any

from typing_extensions import Self

from apps.agent.agent_framework.deployment.abstract import AbstractDeployment
from apps.agent.agent_framework.deployment.config import DummyDeploymentConfig
from apps.agent.agent_framework.deployment.hooks.abstract import (
    CombinedDeploymentHook,
    DeploymentHook,
)
from apps.agent.agent_framework.runtime.abstract import IsAliveResponse
from apps.agent.agent_framework.runtime.dummy import DummyRuntime
from apps.agent.agent_framework.utils.log import get_logger


class DummyDeployment(AbstractDeployment):
    def __init__(self, *, logger: logging.Logger | None = None, **kwargs: Any):
        """This deployment returns blank or predefined outputs.
        Useful for testing.

        Args:
            **kwargs: Keyword arguments (see `DummyDeploymentConfig` for details).
        """
        self._config = DummyDeploymentConfig(**kwargs)
        self.logger = logger or get_logger("rex-deploy")
        self._runtime = DummyRuntime(logger=self.logger)  # type: ignore
        self._hooks = CombinedDeploymentHook()

    def add_hook(self, hook: DeploymentHook):
        self._hooks.add_hook(hook)

    @classmethod
    def from_config(cls, config: DummyDeploymentConfig) -> Self:
        return cls(**config.model_dump())

    async def is_alive(self, *, timeout: float | None = None) -> IsAliveResponse:
        return IsAliveResponse(is_alive=True)

    async def start(self):
        pass

    async def stop(self):
        pass

    @property
    def runtime(self) -> DummyRuntime:
        return self._runtime

    @runtime.setter
    def runtime(self, runtime: DummyRuntime):
        self._runtime = runtime
