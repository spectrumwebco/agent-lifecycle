"""
Reward functions for RLLM training on issue data.

This module provides reward functions for reinforcement learning
on software engineering issue data.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from ..config.rllm_config import RLLMRewardConfig


class IssueRewardFunction(BaseModel):
    """Base class for issue reward functions."""

    name: str = Field(..., description="Name of the reward function")
    weight: float = Field(1.0, description="Weight of the reward function")
    enabled: bool = Field(
        True, description="Whether the reward function is enabled"
    )

    def calculate(
        self, response: str, reference: str, metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate reward.

        Args:
            response: Model response
            reference: Reference response
            metadata: Additional metadata

        Returns:
            Reward value
        """
        raise NotImplementedError("Subclasses must implement calculate method")


class CodeQualityReward(IssueRewardFunction):
    """Reward function for code quality."""

    name: str = "code_quality"
    code_patterns: List[str] = Field(
        default_factory=lambda: [
            r"```[a-zA-Z]*\n(.*?)```",  # Code blocks
            r"`([^`]+)`",  # Inline code
        ],
        description="Patterns to extract code from responses",
    )
    quality_indicators: Dict[str, float] = Field(
        default_factory=lambda: {
            r"\bTODO\b": -0.1,  # TODOs in code
            r"\bFIXME\b": -0.2,  # FIXMEs in code
            r"print\s*\(": -0.05,  # Debug prints
            r"console\.log\s*\(": -0.05,  # Debug logs
            r"^\s*#": 0.02,  # Comments (positive)
            r"^\s*//": 0.02,  # Comments (positive)
            r"^\s*/\*": 0.02,  # Block comments (positive)
            r"^\s*\*": 0.01,  # Block comment continuation (positive)
            r"^\s*\*/": 0.01,  # Block comment end (positive)
            r"[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[a-zA-Z_][a-zA-Z0-9_]*": 0.01,  # Variable assignments
            r"def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(": 0.03,  # Function definitions
            r"class\s+[a-zA-Z_][a-zA-Z0-9_]*\s*(\(|\:)": 0.05,  # Class definitions
            r"import\s+[a-zA-Z_][a-zA-Z0-9_]*": 0.01,  # Imports
            r"from\s+[a-zA-Z_][a-zA-Z0-9_.]*\s+import": 0.01,  # From imports
            r"try\s*:": 0.02,  # Try blocks
            r"except\s+[a-zA-Z_][a-zA-Z0-9_]*\s*:": 0.02,  # Except blocks
            r"finally\s*:": 0.02,  # Finally blocks
            r"with\s+[a-zA-Z_][a-zA-Z0-9_]*\s*(\(|\:)": 0.02,  # With blocks
            r"if\s+.*\s*:": 0.01,  # If statements
            r"elif\s+.*\s*:": 0.01,  # Elif statements
            r"else\s*:": 0.01,  # Else statements
            r"for\s+.*\s+in\s+.*\s*:": 0.01,  # For loops
            r"while\s+.*\s*:": 0.01,  # While loops
            r"return\s+.*": 0.01,  # Return statements
            r"raise\s+[a-zA-Z_][a-zA-Z0-9_]*": 0.01,  # Raise statements
            r"assert\s+.*": 0.01,  # Assert statements
            r"lambda\s+.*\s*:": 0.02,  # Lambda expressions
            r"async\s+def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(": 0.03,  # Async function definitions
            r"await\s+[a-zA-Z_][a-zA-Z0-9_]*": 0.01,  # Await expressions
        },
        description="Indicators of code quality with their weights",
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

    def calculate(
        self, response: str, reference: str, metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate code quality reward.

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

        for snippet in code_snippets:
            lines = snippet.split("\n")
            total_lines += len(lines)

            for line in lines:
                for pattern, weight in self.quality_indicators.items():
                    if re.search(pattern, line):
                        total_reward += weight

        if total_lines > 0:
            total_reward = total_reward / total_lines

        total_reward *= self.weight

        return total_reward


class ComprehensiveExplanationReward(IssueRewardFunction):
    """Reward function for comprehensive explanations."""

    name: str = "comprehensive_explanation"
    explanation_indicators: Dict[str, float] = Field(
        default_factory=lambda: {
            r"^#+\s+.*": 0.1,  # Markdown headers
            r"^\d+\.\s+.*": 0.05,  # Numbered lists
            r"^-\s+.*": 0.03,  # Bullet points
            r"^>\s+.*": 0.05,  # Blockquotes
            r"\*\*.*\*\*": 0.02,  # Bold text
            r"\*.*\*": 0.01,  # Italic text
            r"\[.*\]\(.*\)": 0.05,  # Links
            r"!\[.*\]\(.*\)": 0.05,  # Images
            r"<.*>": 0.02,  # HTML tags
            r"^---$": 0.02,  # Horizontal rules
            r"^___$": 0.02,  # Horizontal rules
            r"^(\s*\|.*\|\s*)+$": 0.05,  # Tables
            r"^(\s*\|:?-+:?\|\s*)+$": 0.05,  # Table separators
        },
        description="Indicators of comprehensive explanations with their weights",
    )
    min_length: int = Field(
        100, description="Minimum length for a comprehensive explanation"
    )
    max_length: int = Field(
        5000, description="Maximum length for a comprehensive explanation"
    )

    def calculate(
        self, response: str, reference: str, metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate comprehensive explanation reward.

        Args:
            response: Model response
            reference: Reference response
            metadata: Additional metadata

        Returns:
            Reward value
        """
        if not self.enabled:
            return 0.0

        length = len(response)
        length_reward = 0.0

        if length < self.min_length:
            length_reward = -0.5  # Penalize too short responses
        elif length > self.max_length:
            length_reward = -0.3  # Penalize too long responses
        else:
            length_reward = (
                0.5
                * (length - self.min_length)
                / (self.max_length - self.min_length)
            )

        quality_reward = 0.0
        lines = response.split("\n")

        for line in lines:
            for pattern, weight in self.explanation_indicators.items():
                if re.search(pattern, line):
                    quality_reward += weight

        if len(lines) > 0:
            quality_reward = quality_reward / len(lines)

        total_reward = 0.6 * length_reward + 0.4 * quality_reward

        total_reward *= self.weight

        return total_reward


class SolutionAccuracyReward(IssueRewardFunction):
    """Reward function for solution accuracy."""

    name: str = "solution_accuracy"
    accuracy_keywords: Dict[str, float] = Field(
        default_factory=lambda: {
            r"\bfix\b": 0.05,
            r"\bsolve\b": 0.05,
            r"\bimplement\b": 0.05,
            r"\brefactor\b": 0.05,
            r"\boptimize\b": 0.05,
            r"\benhance\b": 0.03,
            r"\bimprove\b": 0.03,
            r"\bupdate\b": 0.03,
            r"\bmodify\b": 0.03,
            r"\bchange\b": 0.02,
            r"\badd\b": 0.02,
            r"\bremove\b": 0.02,
            r"\breplace\b": 0.02,
            r"\bcreate\b": 0.02,
            r"\bdelete\b": 0.02,
        },
        description="Keywords indicating solution accuracy with their weights",
    )

    def calculate(
        self, response: str, reference: str, metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate solution accuracy reward.

        Args:
            response: Model response
            reference: Reference response
            metadata: Additional metadata

        Returns:
            Reward value
        """
        if not self.enabled:
            return 0.0

        keyword_reward = 0.0

        for pattern, weight in self.accuracy_keywords.items():
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for _ in matches:
                keyword_reward += weight

        keyword_reward = min(1.0, keyword_reward)

        similarity_reward = 0.0

        if reference:
            response_words = set(re.findall(r"\b\w+\b", response.lower()))
            reference_words = set(re.findall(r"\b\w+\b", reference.lower()))

            if reference_words:
                overlap = len(response_words.intersection(reference_words))
                similarity_reward = overlap / len(reference_words)

        total_reward = 0.7 * keyword_reward
        if reference:
            total_reward += 0.3 * similarity_reward

        total_reward *= self.weight

        return total_reward


class RewardCalculator:
    """Calculator for RLLM rewards."""

    def __init__(
        self,
        config: Optional[RLLMRewardConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize calculator.

        Args:
            config: Reward configuration
            logger: Logger
        """
        self.config = config or RLLMRewardConfig()
        self.logger = logger or logging.getLogger("RewardCalculator")

        self.reward_functions = self._initialize_reward_functions()

        self.logger.info(
            f"Initialized reward calculator with {len(self.reward_functions)} functions"
        )

    def _initialize_reward_functions(self) -> List[IssueRewardFunction]:
        """
        Initialize reward functions.

        Returns:
            List of reward functions
        """
        reward_functions = []

        if hasattr(self.config, 'reward'):
            if self.config.reward.code_quality_weight > 0:
                reward_functions.append(
                    CodeQualityReward(
                        weight=self.config.reward.code_quality_weight,
                        enabled=True,
                    )
                )

            if self.config.reward.code_readability_weight > 0:
                from .code_readability_reward import CodeReadabilityReward
                reward_functions.append(
                    CodeReadabilityReward(
                        weight=self.config.reward.code_readability_weight,
                        enabled=True,
                    )
                )

            if hasattr(self.config.reward, 'explanation_weight') and self.config.reward.explanation_weight > 0:
                reward_functions.append(
                    ComprehensiveExplanationReward(
                        weight=self.config.reward.explanation_weight,
                        enabled=True,
                    )
                )

            if hasattr(self.config.reward, 'accuracy_weight') and self.config.reward.accuracy_weight > 0:
                reward_functions.append(
                    SolutionAccuracyReward(
                        weight=self.config.reward.accuracy_weight,
                        enabled=True,
                    )
                )
        else:
            # Using direct RLLMRewardConfig
            if hasattr(self.config, 'code_quality_weight') and self.config.code_quality_weight > 0:
                reward_functions.append(
                    CodeQualityReward(
                        weight=self.config.code_quality_weight,
                        enabled=True,
                    )
                )

            if hasattr(self.config, 'code_readability_weight') and self.config.code_readability_weight > 0:
                from .code_readability_reward import CodeReadabilityReward
                reward_functions.append(
                    CodeReadabilityReward(
                        weight=self.config.code_readability_weight,
                        enabled=True,
                    )
                )

            if hasattr(self.config, 'explanation_weight') and self.config.explanation_weight > 0:
                reward_functions.append(
                    ComprehensiveExplanationReward(
                        weight=self.config.explanation_weight,
                        enabled=True,
                    )
                )

            if hasattr(self.config, 'accuracy_weight') and self.config.accuracy_weight > 0:
                reward_functions.append(
                    SolutionAccuracyReward(
                        weight=self.config.accuracy_weight,
                        enabled=True,
                    )
                )

        return reward_functions

    def calculate_reward(
        self,
        response: str,
        reference: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Calculate total reward.

        Args:
            response: Model response
            reference: Reference response
            metadata: Additional metadata

        Returns:
            Total reward
        """
        metadata = metadata or {}

        total_reward = 0.0
        rewards_breakdown = {}

        for reward_function in self.reward_functions:
            if not reward_function.enabled:
                continue

            try:
                reward = reward_function.calculate(
                    response, reference, metadata
                )
                total_reward += reward
                rewards_breakdown[reward_function.name] = reward

                self.logger.debug(
                    f"Reward function {reward_function.name}: {reward}"
                )

            except Exception as e:
                self.logger.error(
                    f"Error calculating reward for {reward_function.name}: {e}"
                )

        if hasattr(self.config, 'reward') and hasattr(self.config.reward, 'global_scale'):
            total_reward *= self.config.reward.global_scale
        elif hasattr(self.config, 'global_scale'):
            total_reward *= self.config.global_scale
        else:
            total_reward *= 1.0

        min_reward = 0.0
        max_reward = 1.0
        
        if hasattr(self.config, 'reward'):
            min_reward = getattr(self.config.reward, 'min_reward', min_reward)
            max_reward = getattr(self.config.reward, 'max_reward', max_reward)
        else:
            min_reward = getattr(self.config, 'min_reward', min_reward)
            max_reward = getattr(self.config, 'max_reward', max_reward)
            
        total_reward = max(min_reward, min(max_reward, total_reward))

        self.logger.debug(
            f"Total reward: {total_reward}, breakdown: {rewards_breakdown}"
        )

        return total_reward

    def add_custom_reward_function(
        self, reward_function: IssueRewardFunction
    ) -> None:
        """
        Add custom reward function.

        Args:
            reward_function: Custom reward function
        """
        self.reward_functions.append(reward_function)
        self.logger.info(
            f"Added custom reward function: {reward_function.name}"
        )

    def remove_reward_function(self, name: str) -> bool:
        """
        Remove reward function by name.

        Args:
            name: Name of the reward function

        Returns:
            Whether the reward function was removed
        """
        for i, reward_function in enumerate(self.reward_functions):
            if reward_function.name == name:
                del self.reward_functions[i]
                self.logger.info(f"Removed reward function: {name}")
                return True

        self.logger.warning(f"Reward function not found: {name}")
        return False
