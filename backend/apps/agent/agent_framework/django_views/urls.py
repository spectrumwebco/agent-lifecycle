from django.urls import path
from . import views

app_name = "agent_framework"

urlpatterns = [
    path("", views.root, name="root"),
    path("is_alive/", views.is_alive, name="is_alive"),
    path("create_session/", views.create_session, name="create_session"),
    path("run_in_session/", views.run_in_session, name="run_in_session"),
    path("close_session/", views.close_session, name="close_session"),
    path("execute/", views.execute, name="execute"),
    path("read_file/", views.read_file, name="read_file"),
    path("write_file/", views.write_file, name="write_file"),
    path("upload/", views.UploadFileView.as_view(), name="upload"),
    path("close/", views.close, name="close"),
]
