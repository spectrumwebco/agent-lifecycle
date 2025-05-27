from django.urls import path, include
from .views import trajectory_views
from .agent.django_views import agent_views as agent_views

app_name = "python_agent"

urlpatterns = [
    path("run/", agent_views.run_agent_view, name="run_agent"),
    path("agent_framework/", include("apps.python_agent.agent_framework.django_views.urls")),
    path("agent/", include("apps.python_agent.agent.django_views.urls")),
    path("server/", include("apps.python_agent.agent_framework.django_views.server_urls")),
    
    path("trajectories/", trajectory_views.list_trajectories, name="list_trajectories"),
    path("trajectories/<str:trajectory_id>/", trajectory_views.get_trajectory, name="get_trajectory"),
    path("trajectories/save/", trajectory_views.save_trajectory, name="save_trajectory"),
    path("trajectories/<str:trajectory_id>/delete/", trajectory_views.delete_trajectory, name="delete_trajectory"),
    path("trajectories/<str:trajectory_id>/download/", trajectory_views.download_trajectory, name="download_trajectory"),
]
