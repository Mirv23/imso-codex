from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from apps.adminpanel.views import RateLimitedLoginView


urlpatterns = [
    path("", include("apps.core.urls")),
    path("django-admin/", admin.site.urls),
    path("dashboard/", include("apps.adminpanel.urls")),
    path("login/", RateLimitedLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# En développement, sert les fichiers média (images produits/blog) localement.
# En production Vercel, utiliser un stockage objet (cf. Phase 0 du plan).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
