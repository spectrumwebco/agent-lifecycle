"""
Connector for integrating GitHub and Gitee scrapers with ML infrastructure.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
import pandas as pd
from datetime import datetime

from integrations.github import GitHubScraper, GitHubIntegration
from integrations.gitee import GiteeScraper, GiteeIntegration
from integrations.issue_collector import IssueCollector


class ScraperMLConnector:
    """
    Connector for integrating GitHub and Gitee scrapers with ML infrastructure.
    """

    def __init__(
        self,
        output_dir: str = "./data/ml_pipeline",
        mlflow_tracking_uri: Optional[str] = None,
        feast_feature_server_url: Optional[str] = None,
    ):
        """
        Initialize the scraper-ML connector.

        Args:
            output_dir: Directory for output files
            mlflow_tracking_uri: MLFlow tracking URI
            feast_feature_server_url: Feast feature server URL
        """
        self.output_dir = output_dir
        self.mlflow_tracking_uri = mlflow_tracking_uri
        self.feast_feature_server_url = feast_feature_server_url

        os.makedirs(output_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("ScraperMLConnector")

    async def collect_training_data(
        self,
        github_api_key: Optional[str] = None,
        gitee_api_key: Optional[str] = None,
        topics: List[str] = ["gitops", "terraform", "kubernetes", "k8s"],
        languages: Optional[List[str]] = None,
        min_stars: int = 100,
        max_repos_per_platform: int = 25,
        max_issues_per_repo: int = 50,
    ) -> Dict[str, Any]:
        """
        Collect training data from GitHub and Gitee.

        Args:
            github_api_key: GitHub API key
            gitee_api_key: Gitee API key
            topics: List of topics to search for
            languages: List of languages to filter by
            min_stars: Minimum number of stars
            max_repos_per_platform: Maximum number of repositories to scrape per platform
            max_issues_per_repo: Maximum number of issues to scrape per repository

        Returns:
            Collection results
        """
        self.logger.info("Collecting training data from GitHub and Gitee")

        collector = IssueCollector(
            github_api_key=github_api_key,
            gitee_api_key=gitee_api_key,
            output_dir=os.path.join(self.output_dir, "raw_data"),
        )

        results = await collector.collect_and_save(
            topics=topics,
            languages=languages,
            min_stars=min_stars,
            max_repos_per_platform=max_repos_per_platform,
            max_issues_per_repo=max_issues_per_repo,
        )

        self.logger.info(
            f"Collected {len(results['combined_training_data'])} training examples"
        )

        return results

    def preprocess_training_data(
        self,
        training_data_path: str,
        output_path: Optional[str] = None,
        train_ratio: float = 0.8,
        validation_ratio: float = 0.1,
        test_ratio: float = 0.1,
        seed: int = 42,
    ) -> Dict[str, str]:
        """
        Preprocess training data for ML pipeline.

        Args:
            training_data_path: Path to training data
            output_path: Path for output files
            train_ratio: Ratio of training data
            validation_ratio: Ratio of validation data
            test_ratio: Ratio of test data
            seed: Random seed

        Returns:
            Paths to preprocessed data files
        """
        self.logger.info(f"Preprocessing training data from {training_data_path}")

        if output_path is None:
            output_path = os.path.join(self.output_dir, "preprocessed_data")

        os.makedirs(output_path, exist_ok=True)

        with open(training_data_path, "r") as f:
            training_data = json.load(f)

        self.logger.info(f"Loaded {len(training_data)} training examples")

        df = pd.DataFrame(training_data)

        df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

        train_end = int(len(df) * train_ratio)
        val_end = train_end + int(len(df) * validation_ratio)

        train_df = df[:train_end]
        val_df = df[train_end:val_end]
        test_df = df[val_end:]

        self.logger.info(
            f"Split data into {len(train_df)} training, {len(val_df)} validation, and {len(test_df)} test examples"
        )

        train_path = os.path.join(output_path, "train.json")
        val_path = os.path.join(output_path, "validation.json")
        test_path = os.path.join(output_path, "test.json")

        train_df.to_json(train_path, orient="records", indent=2)
        val_df.to_json(val_path, orient="records", indent=2)
        test_df.to_json(test_path, orient="records", indent=2)

        metadata = {
            "dataset_name": "llama4-fine-tuning",
            "dataset_description": "Training data for fine-tuning Llama 4 models on software engineering tasks",
            "dataset_version": datetime.now().strftime("%Y%m%d"),
            "dataset_size": len(df),
            "train_size": len(train_df),
            "validation_size": len(val_df),
            "test_size": len(test_df),
            "topics": list(
                set(
                    [
                        topic
                        for example in training_data
                        for topic in example.get("metadata", {}).get("topics", [])
                    ]
                )
            ),
            "languages": list(
                set(
                    [
                        example.get("metadata", {}).get("language")
                        for example in training_data
                        if example.get("metadata", {}).get("language")
                    ]
                )
            ),
            "repositories": list(
                set(
                    [
                        example.get("metadata", {}).get("repository")
                        for example in training_data
                    ]
                )
            ),
            "created_at": datetime.now().isoformat(),
        }

        metadata_path = os.path.join(output_path, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        self.logger.info(f"Saved preprocessed data to {output_path}")

        return {
            "train_path": train_path,
            "validation_path": val_path,
            "test_path": test_path,
            "metadata_path": metadata_path,
        }

    def create_feature_store_data(
        self,
        training_data_path: str,
        output_path: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Create feature store data from training data.

        Args:
            training_data_path: Path to training data
            output_path: Path for output files

        Returns:
            Paths to feature store data files
        """
        self.logger.info(f"Creating feature store data from {training_data_path}")

        if output_path is None:
            output_path = os.path.join(self.output_dir, "feature_store_data")

        os.makedirs(output_path, exist_ok=True)

        with open(training_data_path, "r") as f:
            training_data = json.load(f)

        self.logger.info(f"Loaded {len(training_data)} training examples")

        issue_features = []
        for example in training_data:
            metadata = example.get("metadata", {})

            title_embedding = [0.0] * 384
            description_embedding = [0.0] * 384
            topic_vector = [0.0] * 50

            issue_features.append(
                {
                    "issue_id": metadata.get("issue_id", 0),
                    "repository": metadata.get("repository", ""),
                    "title_embedding": title_embedding,
                    "description_embedding": description_embedding,
                    "topic_vector": topic_vector,
                    "language": metadata.get("language", ""),
                    "stars": metadata.get("stars", 0),
                    "issue_age_days": 0,  # Placeholder
                    "solution_length": len(example.get("output", "")),
                    "has_code": 1 if "```" in example.get("output", "") else 0,
                    "timestamp": datetime.now().isoformat(),
                    "created_timestamp": datetime.now().isoformat(),
                }
            )

        repository_features = []
        repositories = {}

        for example in training_data:
            metadata = example.get("metadata", {})
            repo = metadata.get("repository", "")

            if repo and repo not in repositories:
                repositories[repo] = True

                repository_embedding = [0.0] * 384

                repository_features.append(
                    {
                        "issue_id": metadata.get("issue_id", 0),
                        "repository": repo,
                        "repository_embedding": repository_embedding,
                        "repository_stars": metadata.get("stars", 0),
                        "repository_forks": 0,  # Placeholder
                        "repository_age_days": 0,  # Placeholder
                        "repository_topics": metadata.get("topics", [""] * 10)[:10]
                        + [""] * (10 - len(metadata.get("topics", []))),
                        "timestamp": datetime.now().isoformat(),
                        "created_timestamp": datetime.now().isoformat(),
                    }
                )

        issue_df = pd.DataFrame(issue_features)
        repository_df = pd.DataFrame(repository_features)

        issue_path = os.path.join(output_path, "issue_features.parquet")
        repository_path = os.path.join(output_path, "repository_features.parquet")

        issue_df.to_parquet(issue_path, index=False)
        repository_df.to_parquet(repository_path, index=False)

        self.logger.info(f"Saved feature store data to {output_path}")

        return {
            "issue_features_path": issue_path,
            "repository_features_path": repository_path,
        }

    def create_mlflow_experiment(
        self,
        experiment_name: str,
        metadata: Dict[str, Any],
    ) -> str:
        """
        Create MLFlow experiment for tracking.

        Args:
            experiment_name: Name of the experiment
            metadata: Experiment metadata

        Returns:
            Experiment ID
        """
        self.logger.info(f"Creating MLFlow experiment: {experiment_name}")

        if self.mlflow_tracking_uri is None:
            self.logger.warning(
                "MLFlow tracking URI not set, skipping experiment creation"
            )
            return ""

        try:
            import mlflow

            mlflow.set_tracking_uri(self.mlflow_tracking_uri)

            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(
                    name=experiment_name,
                    tags=metadata,
                )
                self.logger.info(
                    f"Created MLFlow experiment: {experiment_name} (ID: {experiment_id})"
                )
            else:
                experiment_id = experiment.experiment_id
                self.logger.info(
                    f"Using existing MLFlow experiment: {experiment_name} (ID: {experiment_id})"
                )

            return experiment_id

        except ImportError:
            self.logger.warning("MLFlow not installed, skipping experiment creation")
            return ""

        except Exception as e:
            self.logger.error(f"Error creating MLFlow experiment: {str(e)}")
            return ""

    def prepare_training_config(
        self,
        model_type: str,
        train_path: str,
        validation_path: str,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Prepare training configuration for fine-tuning.

        Args:
            model_type: Model type (llama4-maverick or llama4-scout)
            train_path: Path to training data
            validation_path: Path to validation data
            output_path: Path for output files

        Returns:
            Training configuration
        """
        self.logger.info(f"Preparing training configuration for {model_type}")

        if output_path is None:
            output_path = os.path.join(self.output_dir, "training_config")

        os.makedirs(output_path, exist_ok=True)

        config = {
            "model_type": model_type,
            "model_id": f"meta-llama/{model_type}",
            "train_file": train_path,
            "validation_file": validation_path,
            "output_dir": f"/models/{model_type}",
            "training_args": {
                "per_device_train_batch_size": 8,
                "per_device_eval_batch_size": 8,
                "gradient_accumulation_steps": 4,
                "learning_rate": 5e-5,
                "num_train_epochs": 3,
                "fp16": True,
                "logging_steps": 100,
                "evaluation_strategy": "steps",
                "eval_steps": 500,
                "save_steps": 1000,
                "save_total_limit": 3,
                "load_best_model_at_end": True,
                "metric_for_best_model": "eval_loss",
                "greater_is_better": False,
                "seed": 42,
            },
            "tokenizer_config": {
                "padding_side": "right",
                "truncation_side": "right",
                "model_max_length": 4096,
            },
        }

        config_path = os.path.join(output_path, f"{model_type}_config.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        self.logger.info(f"Saved training configuration to {config_path}")

        return {
            "config": config,
            "config_path": config_path,
        }

    async def run_full_pipeline(
        self,
        github_api_key: Optional[str] = None,
        gitee_api_key: Optional[str] = None,
        topics: List[str] = ["gitops", "terraform", "kubernetes", "k8s"],
        languages: Optional[List[str]] = None,
        min_stars: int = 100,
        max_repos_per_platform: int = 25,
        max_issues_per_repo: int = 50,
        model_types: List[str] = ["llama4-maverick", "llama4-scout"],
    ) -> Dict[str, Any]:
        """
        Run the full data pipeline from scraping to ML infrastructure.

        Args:
            github_api_key: GitHub API key
            gitee_api_key: Gitee API key
            topics: List of topics to search for
            languages: List of languages to filter by
            min_stars: Minimum number of stars
            max_repos_per_platform: Maximum number of repositories to scrape per platform
            max_issues_per_repo: Maximum number of issues to scrape per repository
            model_types: List of model types to prepare for

        Returns:
            Pipeline results
        """
        self.logger.info("Running full data pipeline")

        collection_results = await self.collect_training_data(
            github_api_key=github_api_key,
            gitee_api_key=gitee_api_key,
            topics=topics,
            languages=languages,
            min_stars=min_stars,
            max_repos_per_platform=max_repos_per_platform,
            max_issues_per_repo=max_issues_per_repo,
        )

        preprocessing_results = self.preprocess_training_data(
            training_data_path=collection_results["combined_training_data_path"],
        )

        feature_store_results = self.create_feature_store_data(
            training_data_path=collection_results["combined_training_data_path"],
        )

        experiment_id = self.create_mlflow_experiment(
            experiment_name="llama4-fine-tuning",
            metadata={
                "dataset_size": len(collection_results["combined_training_data"]),
                "topics": ",".join(topics),
                "languages": ",".join(languages) if languages else "",
                "model_types": ",".join(model_types),
            },
        )

        training_configs = {}
        for model_type in model_types:
            training_configs[model_type] = self.prepare_training_config(
                model_type=model_type,
                train_path=preprocessing_results["train_path"],
                validation_path=preprocessing_results["validation_path"],
            )

        pipeline_results = {
            "collection_results": collection_results,
            "preprocessing_results": preprocessing_results,
            "feature_store_results": feature_store_results,
            "experiment_id": experiment_id,
            "training_configs": training_configs,
        }

        pipeline_results_path = os.path.join(self.output_dir, "pipeline_results.json")
        with open(pipeline_results_path, "w") as f:
            serializable_results = {
                "collection_results": {
                    "github_issues_count": len(
                        collection_results.get("github", {}).get("issues", [])
                    ),
                    "gitee_issues_count": len(
                        collection_results.get("gitee", {}).get("issues", [])
                    ),
                    "combined_training_data_count": len(
                        collection_results["combined_training_data"]
                    ),
                    "combined_training_data_path": collection_results[
                        "combined_training_data_path"
                    ],
                },
                "preprocessing_results": preprocessing_results,
                "feature_store_results": feature_store_results,
                "experiment_id": experiment_id,
                "training_configs": {
                    model_type: {
                        "config_path": config["config_path"],
                    }
                    for model_type, config in training_configs.items()
                },
            }
            json.dump(serializable_results, f, indent=2)

        self.logger.info(f"Saved pipeline results to {pipeline_results_path}")

        return pipeline_results
