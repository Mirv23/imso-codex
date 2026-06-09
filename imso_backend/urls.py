from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


urlpatterns = [
    path("", include("apps.core.urls")),
    path("dashboard/", include("apps.adminpanel.urls")),
    path("login/", LoginView.as_view(template_name="adminpanel/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
