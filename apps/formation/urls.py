from django.urls import path

from . import views

app_name = "formation"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("cours/<int:pk>/", views.course_detail, name="course_detail"),
    path("cours/<int:pk>/inscription/", views.enroll, name="enroll"),
    path("chapitres/<int:pk>/terminer/", views.toggle_complete, name="toggle_complete"),
    path("inscription/", views.register, name="register"),
    path("connexion/", views.login_view, name="login"),
    path("deconnexion/", views.logout_view, name="logout"),
    path("espace/", views.dashboard, name="dashboard"),
    path("verification/", views.kyc, name="kyc"),
    # Espace professeur — gestion du contenu de ses cours
    path("cours/<int:pk>/gerer/", views.course_manage, name="course_manage"),
    path("cours/<int:pk>/chapitres/creer/", views.t_chapter_create, name="t_chapter_create"),
    path("cours/<int:pk>/chapitres/reordonner/", views.t_chapter_reorder, name="t_chapter_reorder"),
    path("cours/<int:pk>/banniere/", views.t_banner_upload, name="t_banner_upload"),
    path("chapitres/<int:pk>/", views.t_chapter_detail, name="t_chapter_detail"),
    path("chapitres/<int:pk>/video-url/", views.t_video_url, name="t_video_url"),
    path("chapitres/<int:pk>/video-confirm/", views.t_video_confirm, name="t_video_confirm"),
    path("chapitres/<int:pk>/video-remove/", views.t_video_remove, name="t_video_remove"),
]
