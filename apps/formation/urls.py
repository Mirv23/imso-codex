from django.urls import path

from . import views

app_name = "formation"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("cours/<int:pk>/", views.course_detail, name="course_detail"),
    path("cours/<int:pk>/inscription/", views.enroll, name="enroll"),
    path("inscription/", views.register, name="register"),
    path("connexion/", views.login_view, name="login"),
    path("deconnexion/", views.logout_view, name="logout"),
    path("espace/", views.dashboard, name="dashboard"),
]
