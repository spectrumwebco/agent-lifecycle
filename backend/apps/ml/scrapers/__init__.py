"""
GitHub and Gitee Issue Scraper Modules for Historical Data Collection.
"""

from .github_scraper import GitHubScraper, TrainingExample
from .gitee_scraper import GiteeScraper, GiteeTrainingExample

__all__ = ["GitHubScraper", "TrainingExample", "GiteeScraper", "GiteeTrainingExample"]
