from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("", include("apps.core.urls")),
    path("dashboard/", include("apps.adminpanel.urls")),
    path("django-admin/", admin.site.urls),
]
