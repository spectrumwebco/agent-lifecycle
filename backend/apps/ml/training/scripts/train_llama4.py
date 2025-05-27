"""
Script for fine-tuning Llama 4 models.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, List, Optional, Union

import torch
import transformers
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    HfArgumentParser,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
    set_seed,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    Llama4MaverickConfig,
    Llama4ScoutConfig,
    DataConfig,
    get_config_for_model,
    get_data_config_for_dataset,
)


def parse_args():
    """
    Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Fine-tune Llama 4 models")
    parser.add_argument(
        "--model_type",
        type=str,
        default="llama4-maverick",
        choices=["llama4-maverick", "llama4-scout"],
        help="Model type",
    )
    parser.add_argument(
        "--dataset_type",
        type=str,
        default="github_issues",
        choices=["default", "github_issues"],
        help="Dataset type",
    )
    parser.add_argument(
        "--config_file",
        type=str,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--data_config_file",
        type=str,
        help="Path to data configuration file",
    )
    parser.add_argument(
        "--train_file",
        type=str,
        help="Path to training file",
    )
    parser.add_argument(
        "--validation_file",
        type=str,
        help="Path to validation file",
    )
    parser.add_argument(
        "--test_file",
        type=str,
        help="Path to test file",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        help="Output directory",
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        help="Learning rate",
    )
    parser.add_argument(
        "--num_train_epochs",
        type=int,
        help="Number of training epochs",
    )
    parser.add_argument(
        "--per_device_train_batch_size",
        type=int,
        help="Per device training batch size",
    )
    parser.add_argument(
        "--per_device_eval_batch_size",
        type=int,
        help="Per device evaluation batch size",
    )
    parser.add_argument(
        "--gradient_accumulation_steps",
        type=int,
        help="Gradient accumulation steps",
    )
    parser.add_argument(
        "--max_seq_length",
        type=int,
        help="Maximum sequence length",
    )
    parser.add_argument(
        "--use_lora",
        action="store_true",
        help="Use LoRA",
    )
    parser.add_argument(
        "--no_lora",
        action="store_true",
        help="Do not use LoRA",
    )
    parser.add_argument(
        "--use_8bit_quantization",
        action="store_true",
        help="Use 8-bit quantization",
    )
    parser.add_argument(
        "--use_4bit_quantization",
        action="store_true",
        help="Use 4-bit quantization",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    return parser.parse_args()


def load_config(args):
    """
    Load configuration.

    Args:
        args: Command line arguments

    Returns:
        Model configuration, data configuration
    """
    if args.config_file:
        if args.model_type == "llama4-maverick":
            model_config = Llama4MaverickConfig.from_json(args.config_file)
        else:
            model_config = Llama4ScoutConfig.from_json(args.config_file)
    else:
        model_config = get_config_for_model(args.model_type)

    if args.output_dir:
        model_config.output_dir = args.output_dir
    if args.learning_rate:
        model_config.learning_rate = args.learning_rate
    if args.num_train_epochs:
        model_config.num_train_epochs = args.num_train_epochs
    if args.per_device_train_batch_size:
        model_config.per_device_train_batch_size = args.per_device_train_batch_size
    if args.per_device_eval_batch_size:
        model_config.per_device_eval_batch_size = args.per_device_eval_batch_size
    if args.gradient_accumulation_steps:
        model_config.gradient_accumulation_steps = args.gradient_accumulation_steps
    if args.seed:
        model_config.seed = args.seed
    if args.no_lora:
        model_config.use_lora = False
    elif args.use_lora:
        model_config.use_lora = True
    if args.use_8bit_quantization:
        model_config.use_8bit_quantization = True
        model_config.use_4bit_quantization = False
    if args.use_4bit_quantization:
        model_config.use_4bit_quantization = True
        model_config.use_8bit_quantization = False

    if args.data_config_file:
        data_config = DataConfig.from_json(args.data_config_file)
    else:
        data_config = get_data_config_for_dataset(args.dataset_type)

    if args.train_file:
        data_config.train_file = args.train_file
    if args.validation_file:
        data_config.validation_file = args.validation_file
    if args.test_file:
        data_config.test_file = args.test_file
    if args.max_seq_length:
        data_config.max_seq_length = args.max_seq_length
        model_config.max_seq_length = args.max_seq_length

    return model_config, data_config


def setup_logging(debug=False):
    """
    Set up logging.

    Args:
        debug: Enable debug mode
    """
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=log_level,
    )
    transformers.utils.logging.set_verbosity_info()
    if debug:
        transformers.utils.logging.set_verbosity_debug()


def load_datasets(data_config):
    """
    Load datasets.

    Args:
        data_config: Data configuration

    Returns:
        Datasets
    """
    data_files = {
        "train": data_config.train_file,
        "validation": data_config.validation_file,
    }

    if data_config.test_file:
        data_files["test"] = data_config.test_file

    extension = data_config.train_file.split(".")[-1]
    raw_datasets = load_dataset(
        extension,
        data_files=data_files,
        use_auth_token=data_config.use_auth_token,
    )

    if data_config.max_train_samples is not None:
        max_train_samples = min(
            len(raw_datasets["train"]), data_config.max_train_samples
        )
        raw_datasets["train"] = raw_datasets["train"].select(range(max_train_samples))

    if data_config.max_eval_samples is not None:
        max_eval_samples = min(
            len(raw_datasets["validation"]), data_config.max_eval_samples
        )
        raw_datasets["validation"] = raw_datasets["validation"].select(
            range(max_eval_samples)
        )

    if "test" in raw_datasets and data_config.max_predict_samples is not None:
        max_predict_samples = min(
            len(raw_datasets["test"]), data_config.max_predict_samples
        )
        raw_datasets["test"] = raw_datasets["test"].select(range(max_predict_samples))

    return raw_datasets


def preprocess_function(examples, tokenizer, data_config):
    """
    Preprocess examples.

    Args:
        examples: Examples
        tokenizer: Tokenizer
        data_config: Data configuration

    Returns:
        Preprocessed examples
    """
    inputs = examples[data_config.input_column]
    targets = examples[data_config.output_column]

    model_inputs = tokenizer(
        inputs,
        max_length=data_config.max_seq_length,
        padding="max_length" if data_config.pad_to_max_length else False,
        truncation=True,
    )

    with tokenizer.as_target_tokenizer():
        labels = tokenizer(
            targets,
            max_length=data_config.max_seq_length,
            padding="max_length" if data_config.pad_to_max_length else False,
            truncation=True,
        )

    model_inputs["labels"] = labels["input_ids"]

    return model_inputs


def main():
    """
    Main function.
    """
    args = parse_args()

    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting fine-tuning for {args.model_type}")

    model_config, data_config = load_config(args)
    logger.info(f"Model configuration: {model_config.to_dict()}")
    logger.info(f"Data configuration: {data_config.to_dict()}")

    set_seed(model_config.seed)

    logger.info(f"Loading tokenizer for {model_config.model_id}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_config.model_id,
        use_auth_token=data_config.use_auth_token,
    )

    logger.info("Loading datasets")
    raw_datasets = load_datasets(data_config)
    logger.info(f"Loaded {len(raw_datasets['train'])} training examples")
    logger.info(f"Loaded {len(raw_datasets['validation'])} validation examples")
    if "test" in raw_datasets:
        logger.info(f"Loaded {len(raw_datasets['test'])} test examples")

    logger.info("Preprocessing datasets")
    tokenized_datasets = raw_datasets.map(
        lambda examples: preprocess_function(examples, tokenizer, data_config),
        batched=True,
        num_proc=data_config.preprocessing_num_workers,
        remove_columns=raw_datasets["train"].column_names,
        load_from_cache_file=not data_config.overwrite_cache,
        desc="Running tokenizer on datasets",
    )

    logger.info(f"Loading model {model_config.model_id}")

    quantization_config = model_config.get_quantization_config()

    model = AutoModelForCausalLM.from_pretrained(
        model_config.model_id,
        use_auth_token=data_config.use_auth_token,
        **quantization_config,
    )

    if model_config.use_lora:
        logger.info("Applying LoRA")

        if model_config.use_8bit_quantization or model_config.use_4bit_quantization:
            model = prepare_model_for_kbit_training(model)

        lora_config = LoraConfig(**model_config.get_lora_config())

        model = get_peft_model(model, lora_config)

        logger.info(f"LoRA configuration: {lora_config}")

    logger.info("Creating training arguments")
    training_args = TrainingArguments(
        **model_config.get_training_args(),
    )

    logger.info("Creating data collator")
    data_collator = DataCollatorForSeq2Seq(
        tokenizer,
        model=model,
        label_pad_token_id=(
            -100 if data_config.ignore_pad_token_for_loss else tokenizer.pad_token_id
        ),
        pad_to_multiple_of=8 if training_args.fp16 else None,
    )

    logger.info("Creating trainer")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    logger.info("Training model")
    train_result = trainer.train()

    logger.info(f"Saving model to {model_config.output_dir}")
    trainer.save_model()

    tokenizer.save_pretrained(model_config.output_dir)

    trainer.save_args()

    trainer.state.save_to_json(
        os.path.join(model_config.output_dir, "trainer_state.json")
    )

    metrics = train_result.metrics
    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)

    logger.info("Evaluating model")
    eval_metrics = trainer.evaluate()
    trainer.log_metrics("eval", eval_metrics)
    trainer.save_metrics("eval", eval_metrics)

    model_config.save_to_json(
        os.path.join(model_config.output_dir, "model_config.json")
    )

    data_config.save_to_json(os.path.join(model_config.output_dir, "data_config.json"))

    logger.info("Fine-tuning completed successfully")


if __name__ == "__main__":
    main()
