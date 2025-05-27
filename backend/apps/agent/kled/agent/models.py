"""
Mock models module for local development.
"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field


class AbstractModel(BaseModel):
    """Base class for all models."""
    
    name: str = Field(default="abstract_model")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional arguments
            
        Returns:
            str: Generated text
        """
        return f"Mock response for: {prompt}"
    
    def get_embedding(self, text: str, **kwargs) -> List[float]:
        """
        Get embedding for text.
        
        Args:
            text: Input text
            **kwargs: Additional arguments
            
        Returns:
            List[float]: Embedding vector
        """
        return [0.1, 0.2, 0.3, 0.4, 0.5]


class ModelConfig(BaseModel):
    """Configuration for a model."""
    
    name: str
    provider: str = "mock"
    api_key: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
