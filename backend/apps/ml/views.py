"""
Views for the ML app.
"""

import os
import json
import logging
import asyncio

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.ml.api.client import MLInfrastructureAPIClient
from .integration.eventstream_integration import (
    event_stream,
    Event,
    EventType,
    EventSource,
)
from .integration.k8s_integration import k8s_client
from .scrapers.github_scraper import GitHubScraper
from .scrapers.gitee_scraper import GiteeScraper
from .trajectories.generator import TrajectoryGenerator
from .benchmarking.historical_benchmark import HistoricalBenchmark

logger = logging.getLogger(__name__)
client = MLInfrastructureAPIClient()

# Initialize components
data_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data"
)
github_scraper = GitHubScraper(output_dir=os.path.join(data_dir, "github"))
gitee_scraper = GiteeScraper(output_dir=os.path.join(data_dir, "gitee"))
trajectory_generator = TrajectoryGenerator(
    output_dir=os.path.join(data_dir, "trajectories")
)
historical_benchmark = HistoricalBenchmark(
    output_dir=os.path.join(data_dir, "benchmarks"),
    trajectories_dir=os.path.join(data_dir, "trajectories"),
)


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint."""
    return JsonResponse({"status": "ok"})


@csrf_exempt
@require_http_methods(["GET"])
def ml_info(request):
    """ML app information endpoint."""
    return JsonResponse(
        {
            "name": "ML App",
            "version": "1.0.0",
            "components": [
                "GitHub Scraper",
                "Gitee Scraper",
                "Trajectory Generator",
                "Historical Benchmark",
                "Eventstream Integration",
                "Kubernetes Integration",
                "ML Infrastructure API Client",
            ],
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def scrape_github(request):
    """
    Scrape GitHub repositories and issues.

    Request body:
    {
        "topics": ["gitops", "terraform", "kubernetes"],
        "languages": ["python", "go"],
        "min_stars": 100,
        "max_repos": 25,
        "max_issues_per_repo": 50,
        "include_pull_requests": false
    }
    """
    try:
        data = json.loads(request.body)

        topics = data.get("topics", ["gitops", "terraform", "kubernetes"])
        languages = data.get("languages")
        min_stars = data.get("min_stars", 100)
        max_repos = data.get("max_repos", 25)
        max_issues_per_repo = data.get("max_issues_per_repo", 50)
        include_pull_requests = data.get("include_pull_requests", False)

        async def scrape():
            try:
                issues_path, training_data_path = await github_scraper.scrape_and_save(
                    topics=topics,
                    languages=languages,
                    min_stars=min_stars,
                    max_repos=max_repos,
                    max_issues_per_repo=max_issues_per_repo,
                    include_pull_requests=include_pull_requests,
                )

                if event_stream:
                    event_data = {
                        "action": "scrape_complete",
                        "source": "github",
                        "issues_path": issues_path,
                        "training_data_path": training_data_path,
                    }
                    await event_stream.publish(
                        Event.new(EventType.STATE_UPDATE, EventSource.ML, event_data)
                    )
            except Exception as e:
                logger.error(f"Error in background scraping: {e}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(scrape())

        return JsonResponse(
            {
                "status": "started",
                "message": "GitHub scraping started in background",
                "config": {
                    "topics": topics,
                    "languages": languages,
                    "min_stars": min_stars,
                    "max_repos": max_repos,
                    "max_issues_per_repo": max_issues_per_repo,
                    "include_pull_requests": include_pull_requests,
                },
            }
        )
    except Exception as e:
        logger.error(f"Error in scrape_github: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def scrape_gitee(request):
    """
    Scrape Gitee repositories and issues.

    Request body:
    {
        "topics": ["gitops", "terraform", "kubernetes"],
        "languages": ["python", "go"],
        "max_repos": 25,
        "max_issues_per_repo": 50,
        "include_pull_requests": false
    }
    """
    try:
        data = json.loads(request.body)

        topics = data.get("topics", ["gitops", "terraform", "kubernetes"])
        languages = data.get("languages")
        max_repos = data.get("max_repos", 25)
        max_issues_per_repo = data.get("max_issues_per_repo", 50)
        include_pull_requests = data.get("include_pull_requests", False)

        async def scrape():
            try:
                issues_path, training_data_path = await gitee_scraper.scrape_and_save(
                    topics=topics,
                    languages=languages,
                    max_repos=max_repos,
                    max_issues_per_repo=max_issues_per_repo,
                    include_pull_requests=include_pull_requests,
                )

                if event_stream:
                    event_data = {
                        "action": "scrape_complete",
                        "source": "gitee",
                        "issues_path": issues_path,
                        "training_data_path": training_data_path,
                    }
                    await event_stream.publish(
                        Event.new(EventType.STATE_UPDATE, EventSource.ML, event_data)
                    )
            except Exception as e:
                logger.error(f"Error in background Gitee scraping: {e}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(scrape())

        return JsonResponse(
            {
                "status": "started",
                "message": "Gitee scraping started in background",
                "config": {
                    "topics": topics,
                    "languages": languages,
                    "max_repos": max_repos,
                    "max_issues_per_repo": max_issues_per_repo,
                    "include_pull_requests": include_pull_requests,
                },
            }
        )
    except Exception as e:
        logger.error(f"Error in scrape_gitee: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_trajectories(request):
    """
    Generate trajectories from issues.

    Request body:
    {
        "issues_file": "issues.json",
        "detailed": true,
        "output_file": "trajectories.json"
    }
    """
    try:
        data = json.loads(request.body)

        issues_file = data.get("issues_file", "issues.json")
        detailed = data.get("detailed", True)
        output_file = data.get("output_file", "trajectories.json")

        async def generate():
            try:
                issues_path = os.path.join(data_dir, "github", issues_file)

                if not os.path.exists(issues_path):
                    logger.error(f"Issues file not found: {issues_path}")
                    return

                with open(issues_path, "r") as f:
                    issues = json.load(f)

                trajectories = await trajectory_generator.generate_trajectories(
                    issues, detailed=detailed
                )

                trajectories_path = await trajectory_generator.save_trajectories(
                    trajectories, filename=output_file
                )

                if event_stream:
                    event_data = {
                        "action": "trajectories_generated",
                        "count": len(trajectories),
                        "trajectories_path": trajectories_path,
                    }
                    await event_stream.publish(
                        Event.new(EventType.STATE_UPDATE, EventSource.ML, event_data)
                    )
            except Exception as e:
                logger.error(f"Error in background trajectory generation: {e}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(generate())

        return JsonResponse(
            {
                "status": "started",
                "message": "Trajectory generation started in background",
                "config": {
                    "issues_file": issues_file,
                    "detailed": detailed,
                    "output_file": output_file,
                },
            }
        )
    except Exception as e:
        logger.error(f"Error in generate_trajectories: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def run_benchmark(request):
    """
    Run historical benchmark.

    Request body:
    {
        "issues_file": "issues.json",
        "detailed_trajectories": true,
        "log_to_mlflow": true
    }
    """
    try:
        data = json.loads(request.body)

        issues_file = data.get("issues_file", "issues.json")
        detailed_trajectories = data.get("detailed_trajectories", True)
        log_to_mlflow = data.get("log_to_mlflow", True)

        async def benchmark():
            try:
                issues_path = os.path.join(data_dir, "github", issues_file)

                if not os.path.exists(issues_path):
                    logger.error(f"Issues file not found: {issues_path}")
                    return

                with open(issues_path, "r") as f:
                    issues = json.load(f)

                result = await historical_benchmark.run_benchmark(
                    issues,
                    detailed_trajectories=detailed_trajectories,
                    log_to_mlflow=log_to_mlflow,
                )

                if event_stream:
                    event_data = {
                        "action": "benchmark_complete",
                        "benchmark_id": result.benchmark_id,
                        "result_summary": {
                            "total_issues": result.total_issues,
                            "successful_issues": result.successful_issues,
                            "failed_issues": result.failed_issues,
                            "skipped_issues": result.skipped_issues,
                            "average_steps": result.average_steps,
                        },
                    }
                    await event_stream.publish(
                        Event.new(EventType.STATE_UPDATE, EventSource.ML, event_data)
                    )
            except Exception as e:
                logger.error(f"Error in background benchmark: {e}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(benchmark())

        return JsonResponse(
            {
                "status": "started",
                "message": "Historical benchmark started in background",
                "config": {
                    "issues_file": issues_file,
                    "detailed_trajectories": detailed_trajectories,
                    "log_to_mlflow": log_to_mlflow,
                },
            }
        )
    except Exception as e:
        logger.error(f"Error in run_benchmark: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_benchmark_result(request, benchmark_id):
    """Get benchmark result."""
    try:
        result_path = os.path.join(
            data_dir, "benchmarks", f"result_{benchmark_id}.json"
        )

        if not os.path.exists(result_path):
            return JsonResponse(
                {"status": "error", "message": "Benchmark result not found"}, status=404
            )

        with open(result_path, "r") as f:
            result = json.load(f)

        return JsonResponse({"status": "success", "result": result})
    except Exception as e:
        logger.error(f"Error in get_benchmark_result: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def run_inference_view(request):
    """
    Run ML inference with the provided data.
    """
    try:
        data = json.loads(request.body)

        service_id = data.get("service_id")
        input_text = data.get("input_text")
        parameters = data.get("parameters", {})

        if not service_id or not input_text:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Missing required parameters: service_id and input_text",
                },
                status=400,
            )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        event_data = {"service_id": service_id, "input_length": len(input_text)}
        loop.run_until_complete(
            event_stream.publish(
                Event.new(
                    EventType.ACTION,
                    EventSource.ML,
                    event_data,
                    {"action": "inference_request"},
                )
            )
        )

        result = loop.run_until_complete(
            client.predict(service_id, input_text, parameters)
        )

        if hasattr(result, "model_dump"):
            result_dict = result.model_dump()
        else:
            result_dict = result.model_dump()

        event_data = {
            "service_id": service_id,
            "latency_ms": result_dict.get("latency_ms", 0),
        }
        loop.run_until_complete(
            event_stream.publish(
                Event.new(
                    EventType.OBSERVATION,
                    EventSource.ML,
                    event_data,
                    {"action": "inference_response"},
                )
            )
        )

        return JsonResponse({"status": "success", "result": result_dict})
    except Exception as e:
        logger.exception("Error running ML inference")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def fine_tune_model_view(request):
    """
    Fine-tune a model with the provided data.
    """
    try:
        data = json.loads(request.body)

        model_type = data.get("model_type")
        training_data_path = data.get("training_data_path")
        validation_data_path = data.get("validation_data_path")
        hyperparameters = data.get("hyperparameters", {})

        if not model_type or not training_data_path:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Missing required parameters: model_type and training_data_path",
                },
                status=400,
            )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        event_data = {
            "model_type": model_type,
            "training_data_path": training_data_path,
        }
        loop.run_until_complete(
            event_stream.publish(
                Event.new(
                    EventType.ACTION,
                    EventSource.ML,
                    event_data,
                    {"action": "fine_tuning_request"},
                )
            )
        )

        result = loop.run_until_complete(
            client.create_fine_tuning_job(
                model_type, training_data_path, validation_data_path, hyperparameters
            )
        )

        if hasattr(result, "model_dump"):
            result_dict = result.model_dump()
        else:
            result_dict = result.model_dump()

        event_data = {
            "job_id": result_dict.get("id", ""),
            "model_type": model_type,
            "status": result_dict.get("status", "created"),
        }
        loop.run_until_complete(
            event_stream.publish(
                Event.new(
                    EventType.STATE_UPDATE,
                    EventSource.ML,
                    event_data,
                    {"action": "fine_tuning_job_created"},
                )
            )
        )

        return JsonResponse({"status": "success", "result": result_dict})
    except Exception as e:
        logger.exception("Error fine-tuning model")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def deploy_ml_infrastructure_view(request):
    """
    Deploy ML infrastructure to Kubernetes.
    """
    try:
        data = json.loads(request.body)

        namespace = data.get("namespace", "ml-infrastructure")
        components = data.get("components", ["mlflow", "kubeflow", "kserve"])

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        event_data = {"namespace": namespace, "components": components}
        loop.run_until_complete(
            event_stream.publish(
                Event.new(
                    EventType.ACTION,
                    EventSource.ML,
                    event_data,
                    {"action": "deploy_ml_infrastructure"},
                )
            )
        )

        results = {}
        if "mlflow" in components:
            results["mlflow"] = loop.run_until_complete(
                k8s_client.deploy_mlflow(namespace)
            )

        if "kubeflow" in components:
            results["kubeflow"] = loop.run_until_complete(
                k8s_client.deploy_kubeflow(namespace)
            )

        if "kserve" in components:
            results["kserve"] = loop.run_until_complete(
                k8s_client.deploy_kserve(namespace)
            )

        return JsonResponse({"status": "success", "results": results})
    except Exception as e:
        logger.exception("Error deploying ML infrastructure")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
