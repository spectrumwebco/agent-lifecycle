"""
Test runner for Neovim integration tests.

This script runs the Neovim integration tests and reports the results.
"""

import os
import sys
import unittest
import asyncio
import time
import json
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_neovim_integration import TestNeovimAPI, TestParallelWorkflow, TestNeovimRoutes


def run_tests():
    """Run all Neovim integration tests."""
    print("=" * 80)
    print("Running Neovim Integration Tests")
    print("=" * 80)
    
    suite = unittest.TestSuite()
    
    suite.addTest(unittest.makeSuite(TestNeovimAPI))
    suite.addTest(unittest.makeSuite(TestParallelWorkflow))
    suite.addTest(unittest.makeSuite(TestNeovimRoutes))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    print(f"Tests Run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print("=" * 80)
    
    return len(result.errors) == 0 and len(result.failures) == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
