"""
URL patterns for the ML app.
"""

from django.urls import path
from . import views

app_name = "python_ml"

urlpatterns = [
    path("health/", views.health_check, name="health_check"),
    path("info/", views.ml_info, name="ml_info"),
    path("inference/", views.run_inference_view, name="run_inference"),
    path("fine-tune/", views.fine_tune_model_view, name="fine_tune_model"),
    path(
        "deploy/", views.deploy_ml_infrastructure_view, name="deploy_ml_infrastructure"
    ),
    path("github/scrape/", views.scrape_github, name="scrape_github"),
    path("gitee/scrape/", views.scrape_gitee, name="scrape_gitee"),
    path(
        "trajectories/generate/",
        views.generate_trajectories,
        name="generate_trajectories",
    ),
    path("benchmark/run/", views.run_benchmark, name="run_benchmark"),
    path(
        "benchmark/result/<str:benchmark_id>/",
        views.get_benchmark_result,
        name="get_benchmark_result",
    ),
]
