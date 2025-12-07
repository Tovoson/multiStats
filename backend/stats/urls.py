from django.urls import path, include
from . import views

urlpatterns = [
    path("kpi-daily", views.KPIDailyView.as_view(), name="kpi-daily"),
]
