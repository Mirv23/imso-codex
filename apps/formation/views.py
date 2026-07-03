from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.adminpanel.models import Course, CourseEnrollment, Profile, SiteSetting

LOGIN_PATH = "/formation/connexion/"


def _profile(user) -> Profile | None:
    return getattr(user, "profile", None) if user.is_authenticated else None


def _payment_info() -> SiteSetting:
    return SiteSetting.load()


def catalog(request: HttpRequest) -> HttpResponse:
    courses = (
        Course.objects.filter(is_active=True)
        .select_related("teacher")
        .annotate(chapter_count=Count("chapters", distinct=True))
        .order_by("-created_at")
    )
    enrolled_ids = set()
    if request.user.is_authenticated:
        enrolled_ids = set(
            CourseEnrollment.objects.filter(student=request.user).values_list("course_id", flat=True)
        )
    return render(request, "formation/catalog.html", {
        "courses": courses,
        "enrolled_ids": enrolled_ids,
        "profile": _profile(request.user),
    })


def course_detail(request: HttpRequest, pk: int) -> HttpResponse:
    course = get_object_or_404(Course.objects.select_related("teacher"), pk=pk, is_active=True)
    chapters = list(course.chapters.all())
    enrollment = None
    is_owner = False
    if request.user.is_authenticated:
        enrollment = CourseEnrollment.objects.filter(student=request.user, course=course).first()
        is_owner = course.teacher_id == request.user.id or request.user.is_staff
    has_access = bool(is_owner or (enrollment and enrollment.status == CourseEnrollment.Status.ACTIVE))
    total_minutes = sum(c.duration_minutes for c in chapters)
    return render(request, "formation/course_detail.html", {
        "course": course,
        "chapters": chapters,
        "enrollment": enrollment,
        "has_access": has_access,
        "is_owner": is_owner,
        "total_minutes": total_minutes,
        "settings": _payment_info(),
        "profile": _profile(request.user),
    })


@login_required(login_url=LOGIN_PATH)
@require_http_methods(["POST"])
def enroll(request: HttpRequest, pk: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=pk, is_active=True)
    is_free = not course.price_htg or course.price_htg == 0
    enr, created = CourseEnrollment.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={
            "status": CourseEnrollment.Status.ACTIVE if is_free else CourseEnrollment.Status.PENDING_PAYMENT
        },
    )
    if not created:
        messages.info(request, "Vous êtes déjà inscrit à ce cours.")
    elif is_free:
        messages.success(request, "Inscription confirmée ! Bon apprentissage. 🎓")
    else:
        messages.info(request, "Inscription enregistrée. Effectuez le paiement pour débloquer l'accès aux vidéos.")
    return redirect("formation:course_detail", pk=pk)


def register(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("formation:dashboard")
    from .forms import RegisterForm
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        if form.cleaned_data["role"] == "teacher":
            messages.success(request, "Compte professeur créé. Il sera actif dès qu'un administrateur l'aura validé.")
            return redirect("formation:login")
        auth_login(request, user)
        messages.success(request, "Bienvenue sur IMSO Formation ! 🎉")
        return redirect("formation:dashboard")
    return render(request, "formation/register.html", {"form": form})


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("formation:dashboard")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        nxt = request.GET.get("next")
        return redirect(nxt if nxt and nxt.startswith("/formation/") else "formation:dashboard")
    return render(request, "formation/login.html", {"form": form})


@require_http_methods(["POST", "GET"])
def logout_view(request: HttpRequest) -> HttpResponse:
    auth_logout(request)
    return redirect("formation:catalog")


@login_required(login_url=LOGIN_PATH)
def dashboard(request: HttpRequest) -> HttpResponse:
    profile = _profile(request.user)
    role = profile.role if profile else Profile.Role.STUDENT
    if role == Profile.Role.TEACHER:
        if not (profile and profile.is_approved):
            return render(request, "formation/pending.html", {"profile": profile})
        courses = (
            Course.objects.filter(teacher=request.user)
            .annotate(
                student_count=Count("student_enrollments", distinct=True),
                chapter_count=Count("chapters", distinct=True),
            )
            .order_by("-created_at")
        )
        return render(request, "formation/dashboard_teacher.html", {
            "courses": courses, "profile": profile,
        })
    enrollments = (
        CourseEnrollment.objects.filter(student=request.user)
        .select_related("course")
        .order_by("-created_at")
    )
    return render(request, "formation/dashboard_student.html", {
        "enrollments": enrollments, "profile": profile,
    })
