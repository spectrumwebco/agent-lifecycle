"""
Legacy import path for Kled tools.

This module redirects imports to the new location in the kled package.
"""

import sys
import importlib
from pathlib import Path

__path__ = [str(Path(__file__).parent.parent / 'kled' / 'tools')]

def __getattr__(name):
    """Redirect attribute access to kled.tools."""
    return getattr(importlib.import_module(f'apps.python_agent.kled.tools'), name)
