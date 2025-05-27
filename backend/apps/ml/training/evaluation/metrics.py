"""
Model Evaluation Metrics

This module defines metrics for evaluating fine-tuned Llama 4 models on
GitOps, Terraform, and Kubernetes issue data.
"""

import json
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any, Callable
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


@dataclass
class ModelEvaluationMetrics:
    """Metrics for evaluating fine-tuned Llama 4 models."""

    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0

    bleu_score: float = 0.0
    rouge_score: Dict[str, float] = field(default_factory=dict)

    trajectory_similarity: float = 0.0
    trajectory_completeness: float = 0.0
    trajectory_efficiency: float = 0.0

    swe_agent_score: float = 0.0
    swe_agent_pass_rate: float = 0.0

    gitops_accuracy: float = 0.0
    terraform_accuracy: float = 0.0
    kubernetes_accuracy: float = 0.0

    latency: float = 0.0
    memory_usage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to a dictionary."""
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, metrics_dict: Dict[str, Any]) -> "ModelEvaluationMetrics":
        """Create metrics from a dictionary."""
        return cls(**metrics_dict)

    def to_json(self) -> str:
        """Convert metrics to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ModelEvaluationMetrics":
        """Create metrics from a JSON string."""
        return cls.from_dict(json.loads(json_str))


class TrajectoryEvaluator:
    """Evaluator for model trajectories."""

    def __init__(self, reference_trajectories: Optional[List[Dict[str, Any]]] = None):
        """Initialize the trajectory evaluator."""
        self.reference_trajectories = reference_trajectories or []

    def evaluate_trajectory(
        self, predicted_trajectory: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Evaluate a predicted trajectory against reference trajectories."""
        if not self.reference_trajectories:
            return {
                "trajectory_similarity": 0.0,
                "trajectory_completeness": 0.0,
                "trajectory_efficiency": 0.0,
            }

        similarities = []
        for reference in self.reference_trajectories:
            similarity = self._calculate_trajectory_similarity(
                predicted_trajectory, reference
            )
            similarities.append(similarity)

        best_match_idx = np.argmax(similarities)
        best_match = self.reference_trajectories[best_match_idx]
        best_similarity = similarities[best_match_idx]

        completeness = self._calculate_trajectory_completeness(
            predicted_trajectory, best_match
        )
        efficiency = self._calculate_trajectory_efficiency(
            predicted_trajectory, best_match
        )

        return {
            "trajectory_similarity": best_similarity,
            "trajectory_completeness": completeness,
            "trajectory_efficiency": efficiency,
        }

    def _calculate_trajectory_similarity(
        self, predicted: List[Dict[str, Any]], reference: List[Dict[str, Any]]
    ) -> float:
        """Calculate similarity between predicted and reference trajectories."""
        pred_steps = [(step.get("type"), step.get("action")) for step in predicted]
        ref_steps = [(step.get("type"), step.get("action")) for step in reference]

        pred_set = set(pred_steps)
        ref_set = set(ref_steps)

        intersection = len(pred_set.intersection(ref_set))
        union = len(pred_set.union(ref_set))

        return intersection / union if union > 0 else 0.0

    def _calculate_trajectory_completeness(
        self, predicted: List[Dict[str, Any]], reference: List[Dict[str, Any]]
    ) -> float:
        """Calculate completeness of predicted trajectory compared to reference."""
        pred_steps = [(step.get("type"), step.get("action")) for step in predicted]
        ref_steps = [(step.get("type"), step.get("action")) for step in reference]

        pred_set = set(pred_steps)
        ref_set = set(ref_steps)

        return len(pred_set.intersection(ref_set)) / len(ref_set) if ref_set else 0.0

    def _calculate_trajectory_efficiency(
        self, predicted: List[Dict[str, Any]], reference: List[Dict[str, Any]]
    ) -> float:
        """Calculate efficiency of predicted trajectory compared to reference."""
        if len(predicted) == 0:
            return 0.0

        completeness = self._calculate_trajectory_completeness(predicted, reference)

        relative_length = len(predicted) / len(reference) if reference else float("inf")

        relative_length = max(1.0, relative_length)

        return completeness / relative_length


class SWEAgentEvaluator:
    """Evaluator for SWE Agent benchmarking."""

    def __init__(self, benchmark_tasks: Optional[List[Dict[str, Any]]] = None):
        """Initialize the SWE Agent evaluator."""
        self.benchmark_tasks = benchmark_tasks or []

    def evaluate_model(
        self,
        model_predictions: List[Dict[str, Any]],
        task_ids: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Evaluate model predictions on SWE Agent benchmark tasks."""
        if not self.benchmark_tasks or not model_predictions:
            return {
                "swe_agent_score": 0.0,
                "swe_agent_pass_rate": 0.0,
            }

        if task_ids:
            tasks = [
                task for task in self.benchmark_tasks if task.get("task_id") in task_ids
            ]
        else:
            tasks = self.benchmark_tasks

        if not tasks:
            return {
                "swe_agent_score": 0.0,
                "swe_agent_pass_rate": 0.0,
            }

        task_results = []
        for task in tasks:
            task_id = task.get("task_id")
            prediction = next(
                (p for p in model_predictions if p.get("task_id") == task_id), None
            )

            if prediction:
                result = self._evaluate_task(task, prediction)
                task_results.append(result)

        if not task_results:
            return {
                "swe_agent_score": 0.0,
                "swe_agent_pass_rate": 0.0,
            }

        pass_rate = sum(1 for r in task_results if r.get("passed", False)) / len(
            task_results
        )
        scores = [r.get("score", 0.0) for r in task_results]
        avg_score = sum(scores) / len(scores)

        return {
            "swe_agent_score": avg_score,
            "swe_agent_pass_rate": pass_rate,
        }

    def _evaluate_task(
        self, task: Dict[str, Any], prediction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a single task prediction."""
        task_type = task.get("type", "")
        expected_output = task.get("expected_output", {})

        predicted_output = prediction.get("output", {})
        trajectory = prediction.get("trajectory", [])

        if task_type == "code_generation":
            return self._evaluate_code_generation(
                expected_output, predicted_output, trajectory
            )
        elif task_type == "code_repair":
            return self._evaluate_code_repair(
                expected_output, predicted_output, trajectory
            )
        elif task_type == "issue_resolution":
            return self._evaluate_issue_resolution(
                expected_output, predicted_output, trajectory
            )
        else:
            return {
                "passed": False,
                "score": 0.0,
                "details": "Unknown task type",
            }

    def _evaluate_code_generation(
        self,
        expected: Dict[str, Any],
        predicted: Dict[str, Any],
        trajectory: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Evaluate code generation task."""
        compiles = predicted.get("compiles", False)
        if not compiles:
            return {
                "passed": False,
                "score": 0.0,
                "details": "Code does not compile",
            }

        tests_pass = predicted.get("tests_pass", False)

        code_similarity = self._calculate_code_similarity(
            expected.get("code", ""), predicted.get("code", "")
        )

        score = 0.3 * float(compiles) + 0.5 * float(tests_pass) + 0.2 * code_similarity

        return {
            "passed": tests_pass,
            "score": score,
            "details": {
                "compiles": compiles,
                "tests_pass": tests_pass,
                "code_similarity": code_similarity,
            },
        }

    def _evaluate_code_repair(
        self,
        expected: Dict[str, Any],
        predicted: Dict[str, Any],
        trajectory: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Evaluate code repair task."""
        compiles = predicted.get("compiles", False)
        if not compiles:
            return {
                "passed": False,
                "score": 0.0,
                "details": "Code does not compile",
            }

        tests_pass = predicted.get("tests_pass", False)

        issue_fixed = predicted.get("issue_fixed", False)

        score = (
            0.2 * float(compiles) + 0.3 * float(tests_pass) + 0.5 * float(issue_fixed)
        )

        return {
            "passed": issue_fixed and tests_pass,
            "score": score,
            "details": {
                "compiles": compiles,
                "tests_pass": tests_pass,
                "issue_fixed": issue_fixed,
            },
        }

    def _evaluate_issue_resolution(
        self,
        expected: Dict[str, Any],
        predicted: Dict[str, Any],
        trajectory: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Evaluate issue resolution task."""
        solution_correct = predicted.get("solution_correct", False)

        has_explanation = bool(predicted.get("explanation", ""))

        trajectory_evaluator = TrajectoryEvaluator([expected.get("trajectory", [])])
        trajectory_metrics = trajectory_evaluator.evaluate_trajectory(trajectory)

        score = (
            0.6 * float(solution_correct)
            + 0.1 * float(has_explanation)
            + 0.3 * trajectory_metrics.get("trajectory_completeness", 0.0)
        )

        return {
            "passed": solution_correct,
            "score": score,
            "details": {
                "solution_correct": solution_correct,
                "has_explanation": has_explanation,
                "trajectory_metrics": trajectory_metrics,
            },
        }

    def _calculate_code_similarity(
        self, expected_code: str, predicted_code: str
    ) -> float:
        """Calculate similarity between expected and predicted code."""
        expected_norm = self._normalize_code(expected_code)
        predicted_norm = self._normalize_code(predicted_code)

        expected_tokens = set(expected_norm.split())
        predicted_tokens = set(predicted_norm.split())

        intersection = len(expected_tokens.intersection(predicted_tokens))
        union = len(expected_tokens.union(predicted_tokens))

        return intersection / union if union > 0 else 0.0

    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison."""
        return " ".join(code.lower().split())


def calculate_metrics(
    predictions: List[Any], references: List[Any], task_type: str = "issue_resolution"
) -> ModelEvaluationMetrics:
    """Calculate evaluation metrics for model predictions."""
    metrics = ModelEvaluationMetrics()

    if task_type == "issue_resolution":
        y_true = [int(ref.get("solution_correct", False)) for ref in references]
        y_pred = [int(pred.get("solution_correct", False)) for pred in predictions]

        if len(y_true) > 0 and len(y_pred) > 0:
            metrics.accuracy = accuracy_score(y_true, y_pred)
            metrics.precision = precision_score(y_true, y_pred, zero_division=0)
            metrics.recall = recall_score(y_true, y_pred, zero_division=0)
            metrics.f1 = f1_score(y_true, y_pred, zero_division=0)

        gitops_preds = [
            p for p, r in zip(predictions, references) if "gitops" in r.get("tags", [])
        ]
        gitops_refs = [r for r in references if "gitops" in r.get("tags", [])]

        terraform_preds = [
            p
            for p, r in zip(predictions, references)
            if "terraform" in r.get("tags", [])
        ]
        terraform_refs = [r for r in references if "terraform" in r.get("tags", [])]

        kubernetes_preds = [
            p
            for p, r in zip(predictions, references)
            if "kubernetes" in r.get("tags", [])
        ]
        kubernetes_refs = [r for r in references if "kubernetes" in r.get("tags", [])]

        if gitops_refs:
            gitops_correct = sum(
                1 for p in gitops_preds if p.get("solution_correct", False)
            )
            metrics.gitops_accuracy = gitops_correct / len(gitops_refs)

        if terraform_refs:
            terraform_correct = sum(
                1 for p in terraform_preds if p.get("solution_correct", False)
            )
            metrics.terraform_accuracy = terraform_correct / len(terraform_refs)

        if kubernetes_refs:
            kubernetes_correct = sum(
                1 for p in kubernetes_preds if p.get("solution_correct", False)
            )
            metrics.kubernetes_accuracy = kubernetes_correct / len(kubernetes_refs)

        trajectory_evaluator = TrajectoryEvaluator(
            [r.get("trajectory", []) for r in references]
        )
        trajectory_metrics_list = [
            trajectory_evaluator.evaluate_trajectory(p.get("trajectory", []))
            for p in predictions
        ]

        if trajectory_metrics_list:
            metrics.trajectory_similarity = np.mean(
                [m.get("trajectory_similarity", 0.0) for m in trajectory_metrics_list]
            )
            metrics.trajectory_completeness = np.mean(
                [m.get("trajectory_completeness", 0.0) for m in trajectory_metrics_list]
            )
            metrics.trajectory_efficiency = np.mean(
                [m.get("trajectory_efficiency", 0.0) for m in trajectory_metrics_list]
            )

        swe_evaluator = SWEAgentEvaluator(references)
        swe_metrics = swe_evaluator.evaluate_model(predictions)

        metrics.swe_agent_score = swe_metrics.get("swe_agent_score", 0.0)
        metrics.swe_agent_pass_rate = swe_metrics.get("swe_agent_pass_rate", 0.0)

    return metrics
