"""
Compatibility module for swerex imports.

This module provides compatibility with the original swerex module,
enabling imports to work correctly in the Django integration.
"""

__version__ = "1.2.1"
__file__ = __file__

from . import exceptions
from . import utils
from . import deployment
from . import runtime
