"""
Backward compatibility module for agent.
This module redirects imports from the old structure to the new structure.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from kled.agent import *
