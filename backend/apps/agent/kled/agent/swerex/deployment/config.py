"""
Mock swerex deployment config module for local development.
"""

from typing import Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field

from ..deployment.abstract import AbstractDeployment


class DeploymentConfig(BaseModel):
    """Base class for deployment configurations."""
    
    type: str = "abstract"
    
    def get_deployment(self) -> AbstractDeployment:
        """Get deployment instance."""
        raise NotImplementedError("Abstract method")


class DockerDeploymentConfig(DeploymentConfig):
    """Docker deployment configuration."""
    
    type: str = "docker"
    image: str = "python:3.11"
    python_standalone_dir: str = "/root"
    
    def get_deployment(self) -> AbstractDeployment:
        """Get deployment instance."""
        from .docker import DockerDeployment
        return DockerDeployment(self)


def get_deployment(config: DeploymentConfig) -> AbstractDeployment:
    """Get deployment instance from config."""
    return config.get_deployment()
