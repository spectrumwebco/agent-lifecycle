"""
Code readability reward function for RLLM training.

This module provides a reward function that evaluates code readability
based on various metrics like variable naming, function length, and comments.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple

from pydantic import Field

from .issue_rewards import IssueRewardFunction


class CodeReadabilityReward(IssueRewardFunction):
    """Reward function for code readability."""

    name: str = "code_readability"
    code_patterns: List[str] = Field(
        default_factory=lambda: [
            r"```[a-zA-Z]*\n(.*?)```",  # Code blocks
            r"`([^`]+)`",  # Inline code
        ],
        description="Patterns to extract code from responses",
    )
    readability_indicators: Dict[str, float] = Field(
        default_factory=lambda: {
            r"\b[a-z][a-z0-9_]+\b": 0.02,  # snake_case variables (good)
            r"\b[a-z][a-zA-Z0-9]+\b": 0.02,  # camelCase variables (good)
            r"\b[A-Z][A-Z0-9_]+\b": 0.01,  # CONSTANT_CASE (good for constants)
            
            r"\b[a-z][0-9]\b": -0.05,  # Single letter with number (e.g., x1, y2)
            r"\b[a-z]\b": -0.02,  # Single letter variables (except in loops)
            
            r"def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]{100,}\)": -0.05,  # Long parameter lists
            
            r"^\s*#\s+[A-Z]": 0.03,  # Proper comments starting with capital letter
            r"^\s*#[^A-Z\s]": -0.01,  # Comments not starting with capital letter
            
            r'"""[\s\S]*?"""': 0.05,  # Triple-quoted docstrings
            r"'''\s*\n\s*[A-Z][\s\S]*?\n\s*'''": 0.05,  # Triple-quoted docstrings with proper capitalization
            
            r"\n\s*\n\s*\n": -0.02,  # Too many blank lines
            r"^\s{4,}": 0.01,  # Proper indentation (4+ spaces)
            r"^\t+": -0.01,  # Tab indentation (discouraged in Python)
            
            r"^.{100,}$": -0.03,  # Lines longer than 100 characters
            
            r"def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)\s*->\s*[a-zA-Z_][a-zA-Z0-9_]*": 0.03,  # Return type hints
            r"[a-zA-Z_][a-zA-Z0-9_]*\s*:\s*[a-zA-Z_][a-zA-Z0-9_]*": 0.02,  # Parameter type hints
        },
        description="Indicators of code readability with their weights",
    )
    
    max_function_lines: int = Field(
        50, description="Maximum recommended lines for a function"
    )
    max_line_length: int = Field(
        88, description="Maximum recommended line length"
    )

    def extract_code(self, text: str) -> List[str]:
        """
        Extract code from text.

        Args:
            text: Text to extract code from

        Returns:
            List of code snippets
        """
        code_snippets = []

        for pattern in self.code_patterns:
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                if len(match.groups()) > 0:
                    code_snippets.append(match.group(1))
                else:
                    code_snippets.append(match.group(0))

        return code_snippets

    def analyze_function_length(self, code: str) -> Tuple[float, int]:
        """
        Analyze function length in code.

        Args:
            code: Code to analyze

        Returns:
            Tuple of (reward, number of functions)
        """
        functions = re.finditer(
            r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(.*?\).*?:",
            code,
            re.DOTALL,
        )
        
        total_reward = 0.0
        function_count = 0
        
        for func_match in functions:
            function_count += 1
            func_name = func_match.group(1)
            func_start = func_match.start()
            
            lines = code[func_start:].split("\n")
            func_lines = 1  # Start with the definition line
            
            if len(lines) <= 1:
                continue
                
            base_indent = len(lines[1]) - len(lines[1].lstrip())
            
            for i in range(2, len(lines)):
                if lines[i].strip() and len(lines[i]) - len(lines[i].lstrip()) <= base_indent:
                    break
                func_lines += 1
            
            if func_lines <= 10:
                length_reward = 0.05
            elif func_lines <= self.max_function_lines:
                length_reward = 0.02
            else:
                length_reward = -0.05 * (func_lines / self.max_function_lines)
            
            total_reward += length_reward
        
        return total_reward, function_count

    def calculate(
        self, response: str, reference: str, metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate code readability reward.

        Args:
            response: Model response
            reference: Reference response
            metadata: Additional metadata

        Returns:
            Reward value
        """
        if not self.enabled:
            return 0.0

        code_snippets = self.extract_code(response)

        if not code_snippets:
            return 0.0

        total_reward = 0.0
        total_lines = 0
        total_functions = 0

        for snippet in code_snippets:
            lines = snippet.split("\n")
            total_lines += len(lines)
            
            for line in lines:
                for pattern, weight in self.readability_indicators.items():
                    if re.search(pattern, line):
                        total_reward += weight
            
            function_reward, function_count = self.analyze_function_length(snippet)
            total_reward += function_reward
            total_functions += function_count
            
            comment_lines = sum(1 for line in lines if re.match(r"^\s*#", line))
            comment_ratio = comment_lines / len(lines) if len(lines) > 0 else 0
            
            if 0.1 <= comment_ratio <= 0.2:
                total_reward += 0.1  # Ideal comment ratio
            elif comment_ratio > 0.3:
                total_reward -= 0.05  # Too many comments
            elif comment_ratio < 0.05 and len(lines) > 10:
                total_reward -= 0.1  # Too few comments in substantial code

        if total_lines > 0:
            total_reward = total_reward / total_lines
            
        if total_functions > 0:
            total_reward += 0.05
            
        total_reward *= self.weight

        return total_reward
