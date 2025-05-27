# RLLM Integration for Python ML

This package provides integration of the RLLM (Reinforcement Learning for Language Models) framework with the existing ML infrastructure. The integration enables training language models on historical issues using reinforcement learning techniques.

## Overview

The RLLM framework has demonstrated impressive results comparable to o3-mini models in training Deep Coder. This integration brings those capabilities to our ML app, allowing us to train our agent on historic issues more effectively.

Key components:

- **Configuration**: Flexible configuration system for models, training, rewards, and distributed training
- **Models**: Wrapper for RLLM models with support for LoRA fine-tuning
- **Rewards**: Customizable reward functions for software engineering tasks
- **Data**: Trajectory dataset conversion from historical benchmarks
- **Training**: Standard and distributed training infrastructure
- **Integration**: Seamless integration with existing ML infrastructure

## Installation

The RLLM integration requires Python 3.10+ and the following dependencies:

```bash
# Create a conda environment
conda create -n rllm python=3.10 -y
conda activate rllm

# Install dependencies
pip install torch transformers peft ray optuna mlflow kubernetes
```

## Usage

### Training on Historical Issues

The `train_rllm.py` script demonstrates how to train RLLM models on historical issue trajectories:

```bash
python -m backend.apps.python_ml.scripts.train_rllm \
    --benchmark-id <benchmark_id> \
    --output-dir ./data/rllm \
    --epochs 3 \
    --batch-size 4 \
    --learning-rate 5e-5
```

You can also provide your own training data:

```bash
python -m backend.apps.python_ml.scripts.train_rllm \
    --train-path ./data/train.jsonl \
    --val-path ./data/val.jsonl \
    --output-dir ./data/rllm
```

### Programmatic Usage

```python
import asyncio
from backend.apps.python_ml import (
    RLLMConfig, get_deepcoder_config, RLLMTrainer,
    BenchmarkIntegration, MLIntegration
)

async def train_model():
    # Load configuration
    config = get_deepcoder_config()
    
    # Initialize integrations
    benchmark_integration = BenchmarkIntegration(config=config)
    ml_integration = MLIntegration(config=config)
    
    # Set up MLflow
    await ml_integration.setup_mlflow(experiment_name="rllm_training")
    
    # Convert existing benchmark to RLLM format
    result_path, train_path, val_path = await benchmark_integration.convert_existing_benchmark(
        benchmark_id="benchmark_123",
    )
    
    # Initialize trainer
    trainer = RLLMTrainer(config=config)
    
    # Train model
    model_path = await trainer.train(
        train_data_path=train_path,
        val_data_path=val_path,
    )
    
    print(f"Model saved to {model_path}")

# Run the training
asyncio.run(train_model())
```

## Integration with Existing ML Infrastructure

The RLLM integration works seamlessly with the existing ML infrastructure:

- **Benchmark Integration**: Convert historical benchmarks to RLLM training format
- **Trajectory Integration**: Generate and convert trajectories for training
- **ML Integration**: Track experiments with MLflow and deploy models with KServe

## Directory Structure

```
python_ml/
├── config/             # Configuration classes for RLLM
├── data/               # Trajectory dataset conversion
├── integration/        # Integration with existing ML infrastructure
├── models/             # RLLM model wrapper
├── rewards/            # Reward functions for issue-based training
├── scripts/            # Training and evaluation scripts
└── training/           # Training infrastructure
```

## Key Features

- **Reinforcement Learning**: Train language models using PPO (Proximal Policy Optimization)
- **Historical Data**: Leverage historical issues for training
- **Distributed Training**: Scale training with Ray for distributed computing
- **MLflow Integration**: Track experiments and metrics
- **Kubernetes Deployment**: Deploy models to production using KServe

## Contributing

To extend the RLLM integration:

1. Add new reward functions in `rewards/`
2. Implement custom training strategies in `training/`
3. Enhance integration with existing infrastructure in `integration/`
