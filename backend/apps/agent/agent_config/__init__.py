"""
Backward compatibility module for agent_config.

This module redirects imports from the old structure to the new structure.
"""

import sys
from pathlib import Path

# Redirect imports to kled/config
sys.path.insert(0, str(Path(__file__).parent.parent))
from kled.config import *
