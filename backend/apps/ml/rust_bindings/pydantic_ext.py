"""
Python interface to Rust implementation of Pydantic extensions.
"""
from typing import Dict, List, Optional, Type, Any
import inspect
from pydantic import BaseModel

try:
    from agent_runtime_rust.ml_core import RustValidator, create_validator_from_pydantic
except ImportError:
    RustValidator = None
    create_validator_from_pydantic = None


class PydanticRustValidator:
    """
    Python wrapper for the Rust implementation of Pydantic validation.
    Falls back to Python implementation if Rust bindings are not available.
    """
    
    def __init__(self, model_class: Type[BaseModel]):
        """
        Initialize the validator with a Pydantic model class.
        
        Args:
            model_class: Pydantic model class to validate against
        """
        self.model_class = model_class
        
        if RustValidator is not None and create_validator_from_pydantic is not None:
            import pyo3
            with pyo3.Python.acquire_gil() as gil:
                self._rust_validator = create_validator_from_pydantic(gil.python(), model_class)
        else:
            self._rust_validator = None
    
    def validate_dict(self, data: Dict) -> List[str]:
        """
        Validate a dictionary against the Pydantic model.
        
        Args:
            data: Dictionary to validate
            
        Returns:
            List of validation errors
        """
        if self._rust_validator is not None:
            import pyo3
            with pyo3.Python.acquire_gil() as gil:
                return self._rust_validator.validate_dict(gil.python(), data)
        else:
            errors = []
            try:
                self.model_class(**data)
            except Exception as e:
                if hasattr(e, 'errors'):
                    for error in e.errors():
                        loc = '.'.join(str(l) for l in error.get('loc', []))
                        msg = error.get('msg', 'Unknown error')
                        errors.append(f"{loc}: {msg}")
                else:
                    errors.append(str(e))
            return errors
    
    def batch_validate(self, data_list: List[Dict]) -> List[List[str]]:
        """
        Validate a list of dictionaries against the Pydantic model.
        
        Args:
            data_list: List of dictionaries to validate
            
        Returns:
            List of lists of validation errors
        """
        if self._rust_validator is not None:
            import pyo3
            with pyo3.Python.acquire_gil() as gil:
                return self._rust_validator.batch_validate(gil.python(), data_list)
        else:
            return [self.validate_dict(data) for data in data_list]


def create_rust_validator(model_class: Type[BaseModel]) -> PydanticRustValidator:
    """
    Create a Rust validator for a Pydantic model.
    
    Args:
        model_class: Pydantic model class to validate against
        
    Returns:
        PydanticRustValidator instance
    """
    return PydanticRustValidator(model_class)
