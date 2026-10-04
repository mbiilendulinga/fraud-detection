from django.urls import path

from . import views

app_name = "fraud_portal"

urlpatterns = [
    path("", views.overview, name="home"),
    path("assessment/", views.assessment, name="assessment"),
    path("model/", views.model_performance, name="model"),
    path("methodology/", views.methodology, name="methodology"),
    path("plot/<str:filename>", views.plot, name="plot"),
]