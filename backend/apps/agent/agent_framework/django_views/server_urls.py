"""
URL patterns for the agent framework server views.
"""

from django.urls import path
from . import server_views

urlpatterns = [
    path('', server_views.root, name='agent_framework_root'),
    path('is_alive/', server_views.is_alive, name='agent_framework_is_alive'),
    path('create_session/', server_views.create_session, name='agent_framework_create_session'),
    path('run_in_session/', server_views.run_in_session, name='agent_framework_run_in_session'),
    path('close_session/', server_views.close_session, name='agent_framework_close_session'),
    path('execute/', server_views.execute, name='agent_framework_execute'),
    path('read_file/', server_views.read_file, name='agent_framework_read_file'),
    path('write_file/', server_views.write_file, name='agent_framework_write_file'),
    path('upload/', server_views.upload, name='agent_framework_upload'),
    path('close/', server_views.close, name='agent_framework_close'),
    path('version/', server_views.version, name='agent_framework_version'),
]
