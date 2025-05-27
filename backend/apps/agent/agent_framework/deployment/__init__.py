"""
Backward compatibility module for agent_framework/deployment.

This module redirects imports from the old structure to the new structure.
"""

import sys
from pathlib import Path

# Redirect imports to agent_framework/shared/deployment
sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_framework.shared.deployment import *
