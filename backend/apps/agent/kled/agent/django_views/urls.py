"""
URL patterns for the agent API.

This module provides URL patterns for the agent API, converting
the Flask routes from the original implementation to Django URL patterns.
"""

from django.urls import path
from . import agent_views

app_name = "agent"

urlpatterns = [
    path("", agent_views.index_view, name="index"),
    path("run/", agent_views.run_agent_view, name="run_agent"),
    path("stop/", agent_views.stop_agent_view, name="stop_agent"),
    path("status/<uuid:thread_id>/", agent_views.agent_status_view, name="agent_status"),
]
