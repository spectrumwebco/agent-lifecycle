"""
Configuration for training data.
"""

import os
from typing import Dict, Any, List, Optional, Union


class DataConfig:
    """
    Configuration for training data.
    """

    def __init__(
        self,
        train_file: str = "/data/train.json",
        validation_file: str = "/data/validation.json",
        test_file: Optional[str] = "/data/test.json",
        max_seq_length: int = 4096,
        input_column: str = "input",
        output_column: str = "output",
        metadata_column: Optional[str] = "metadata",
        preprocessing_num_workers: Optional[int] = None,
        overwrite_cache: bool = False,
        preprocessing_batch_size: int = 1000,
        streaming: bool = False,
        use_auth_token: bool = False,
        ignore_pad_token_for_loss: bool = True,
        pad_to_max_length: bool = False,
        max_train_samples: Optional[int] = None,
        max_eval_samples: Optional[int] = None,
        max_predict_samples: Optional[int] = None,
    ):
        """
        Initialize data configuration.

        Args:
            train_file: Training file
            validation_file: Validation file
            test_file: Test file
            max_seq_length: Maximum sequence length
            input_column: Input column
            output_column: Output column
            metadata_column: Metadata column
            preprocessing_num_workers: Number of preprocessing workers
            overwrite_cache: Overwrite cache
            preprocessing_batch_size: Preprocessing batch size
            streaming: Use streaming
            use_auth_token: Use authentication token
            ignore_pad_token_for_loss: Ignore pad token for loss
            pad_to_max_length: Pad to maximum length
            max_train_samples: Maximum number of training samples
            max_eval_samples: Maximum number of evaluation samples
            max_predict_samples: Maximum number of prediction samples
        """
        self.train_file = train_file
        self.validation_file = validation_file
        self.test_file = test_file
        self.max_seq_length = max_seq_length
        self.input_column = input_column
        self.output_column = output_column
        self.metadata_column = metadata_column
        self.preprocessing_num_workers = preprocessing_num_workers
        self.overwrite_cache = overwrite_cache
        self.preprocessing_batch_size = preprocessing_batch_size
        self.streaming = streaming
        self.use_auth_token = use_auth_token
        self.ignore_pad_token_for_loss = ignore_pad_token_for_loss
        self.pad_to_max_length = pad_to_max_length
        self.max_train_samples = max_train_samples
        self.max_eval_samples = max_eval_samples
        self.max_predict_samples = max_predict_samples

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Configuration dictionary
        """
        return {
            "train_file": self.train_file,
            "validation_file": self.validation_file,
            "test_file": self.test_file,
            "max_seq_length": self.max_seq_length,
            "input_column": self.input_column,
            "output_column": self.output_column,
            "metadata_column": self.metadata_column,
            "preprocessing_num_workers": self.preprocessing_num_workers,
            "overwrite_cache": self.overwrite_cache,
            "preprocessing_batch_size": self.preprocessing_batch_size,
            "streaming": self.streaming,
            "use_auth_token": self.use_auth_token,
            "ignore_pad_token_for_loss": self.ignore_pad_token_for_loss,
            "pad_to_max_length": self.pad_to_max_length,
            "max_train_samples": self.max_train_samples,
            "max_eval_samples": self.max_eval_samples,
            "max_predict_samples": self.max_predict_samples,
        }

    def save_to_json(self, file_path: str) -> None:
        """
        Save configuration to JSON file.

        Args:
            file_path: File path
        """
        import json

        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, file_path: str) -> "DataConfig":
        """
        Load configuration from JSON file.

        Args:
            file_path: File path

        Returns:
            Configuration
        """
        import json

        with open(file_path, "r") as f:
            config_dict = json.load(f)

        return cls(**config_dict)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "DataConfig":
        """
        Load configuration from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Configuration
        """
        return cls(**config_dict)


class GitHubIssueDataConfig(DataConfig):
    """
    Configuration for GitHub issue training data.
    """

    def __init__(
        self,
        train_file: str = "/data/github_issues_train.json",
        validation_file: str = "/data/github_issues_validation.json",
        test_file: Optional[str] = "/data/github_issues_test.json",
        input_column: str = "issue",
        output_column: str = "solution",
        metadata_column: str = "metadata",
        **kwargs,
    ):
        """
        Initialize GitHub issue data configuration.

        Args:
            train_file: Training file
            validation_file: Validation file
            test_file: Test file
            input_column: Input column
            output_column: Output column
            metadata_column: Metadata column
            **kwargs: Additional arguments
        """
        super().__init__(
            train_file=train_file,
            validation_file=validation_file,
            test_file=test_file,
            input_column=input_column,
            output_column=output_column,
            metadata_column=metadata_column,
            **kwargs,
        )


def get_default_data_config() -> DataConfig:
    """
    Get default data configuration.

    Returns:
        Default configuration
    """
    return DataConfig()


def get_github_issue_data_config() -> GitHubIssueDataConfig:
    """
    Get GitHub issue data configuration.

    Returns:
        GitHub issue data configuration
    """
    return GitHubIssueDataConfig()


def get_data_config_for_dataset(
    dataset_type: str,
) -> Union[DataConfig, GitHubIssueDataConfig]:
    """
    Get data configuration for dataset.

    Args:
        dataset_type: Dataset type

    Returns:
        Data configuration
    """
    if dataset_type == "default":
        return get_default_data_config()
    elif dataset_type == "github_issues":
        return get_github_issue_data_config()
    else:
        raise ValueError(f"Unsupported dataset type: {dataset_type}")
