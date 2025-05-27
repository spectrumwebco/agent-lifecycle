from django.urls import path
from . import views

app_name = "tools"

urlpatterns = [
    path("status/", views.tools_status_view, name="status"),
]
