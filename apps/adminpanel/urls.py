from django.urls import path

from .views import DashboardView, dashboard_summary


app_name = "adminpanel"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("api/summary/", dashboard_summary, name="summary"),
]
