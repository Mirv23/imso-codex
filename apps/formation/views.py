from __future__ import annotations

import json
import uuid

from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.files.storage import default_storage
from django.db.models import Count, Max
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.adminpanel import views as av
from apps.adminpanel.models import (
    Chapter,
    ChapterCompletion,
    Course,
    CourseEnrollment,
    Profile,
    SiteSetting,
)

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
    completed_ids: set[int] = set()
    if request.user.is_authenticated and chapters:
        completed_ids = set(
            ChapterCompletion.objects.filter(
                student=request.user, chapter__course=course
            ).values_list("chapter_id", flat=True)
        )
    total_ch = len(chapters)
    done = len([c for c in chapters if c.id in completed_ids])
    progress = round(done / total_ch * 100) if total_ch else 0
    return render(request, "formation/course_detail.html", {
        "course": course,
        "chapters": chapters,
        "enrollment": enrollment,
        "has_access": has_access,
        "is_owner": is_owner,
        "total_minutes": total_minutes,
        "completed_ids": completed_ids,
        "progress": progress,
        "done": done,
        "total_ch": total_ch,
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


def _student_has_access(user, course: Course) -> bool:
    if not user.is_authenticated:
        return False
    if course.teacher_id == user.id or user.is_staff:
        return True
    return CourseEnrollment.objects.filter(
        student=user, course=course, status=CourseEnrollment.Status.ACTIVE
    ).exists()


@login_required(login_url=LOGIN_PATH)
@require_http_methods(["POST"])
def toggle_complete(request: HttpRequest, pk: int) -> HttpResponse:
    """Bascule l'état 'terminé' d'un chapitre pour l'étudiant connecté."""
    try:
        ch = Chapter.objects.select_related("course").get(pk=pk)
    except Chapter.DoesNotExist:
        return JsonResponse({"error": "Chapitre introuvable."}, status=404)
    if not _student_has_access(request.user, ch.course):
        return JsonResponse({"error": "Accès refusé."}, status=403)
    existing = ChapterCompletion.objects.filter(student=request.user, chapter=ch).first()
    if existing:
        existing.delete()
        completed = False
    else:
        ChapterCompletion.objects.get_or_create(student=request.user, chapter=ch)
        completed = True
    total = ch.course.chapters.count()
    done = ChapterCompletion.objects.filter(student=request.user, chapter__course=ch.course).count()
    return JsonResponse({
        "completed": completed,
        "done": done,
        "total": total,
        "progress": round(done / total * 100) if total else 0,
    })


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
def kyc(request: HttpRequest) -> HttpResponse:
    """Soumission de la vérification d'identité (KYC) par un professeur."""
    profile = _profile(request.user)
    if not profile or profile.role != Profile.Role.TEACHER:
        return redirect("formation:dashboard")
    if profile.kyc_status == Profile.KycStatus.APPROVED:
        return redirect("formation:dashboard")
    if request.method == "POST":
        id_number = str(request.POST.get("id_number") or "").strip()
        doc = request.FILES.get("id_document")
        if not id_number:
            messages.error(request, "Le numéro de votre pièce d'identité est obligatoire.")
        elif not doc and not profile.id_document:
            messages.error(request, "Veuillez joindre une photo de votre pièce d'identité.")
        elif doc and doc.size > 5 * 1024 * 1024:
            messages.error(request, "Le fichier est trop volumineux (max 5 Mo).")
        elif doc and not (getattr(doc, "content_type", "") or "").startswith("image/"):
            messages.error(request, "Le document doit être une image (photo de la pièce).")
        else:
            profile.id_number = id_number[:60]
            if doc:
                ext = doc.name.rsplit(".", 1)[-1].lower() if "." in doc.name else "jpg"
                doc.name = f"{uuid.uuid4().hex}.{ext}"  # nom illisible (confidentialité)
                profile.id_document = doc
            profile.kyc_status = Profile.KycStatus.SUBMITTED
            profile.kyc_note = ""
            profile.save()
            messages.success(request, "Vérification soumise ! Notre équipe l'examinera prochainement.")
            return redirect("formation:dashboard")
    return render(request, "formation/kyc.html", {"profile": profile})


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
    enrollments = list(
        CourseEnrollment.objects.filter(student=request.user)
        .select_related("course")
        .annotate(total_chapters=Count("course__chapters", distinct=True))
        .order_by("-created_at")
    )
    done_map = {
        r["chapter__course"]: r["n"]
        for r in ChapterCompletion.objects.filter(student=request.user)
        .values("chapter__course").annotate(n=Count("id"))
    }
    for e in enrollments:
        e.done_count = done_map.get(e.course_id, 0)
        e.progress = round(e.done_count / e.total_chapters * 100) if e.total_chapters else 0
    return render(request, "formation/dashboard_student.html", {
        "enrollments": enrollments, "profile": profile,
    })


# ── Espace professeur : gestion du contenu de SES cours ──────────────────

def _json(request: HttpRequest) -> dict:
    try:
        return json.loads(request.body)
    except (ValueError, TypeError):
        return {}


def _can_manage(user, course: Course) -> bool:
    """Un prof ne gère que ses propres cours (l'admin peut tout)."""
    return bool(course.teacher_id == user.id or user.is_staff)


def _owned_course(request: HttpRequest, pk: int):
    try:
        course = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return None, JsonResponse({"error": "Cours introuvable."}, status=404)
    if not _can_manage(request.user, course):
        return None, JsonResponse({"error": "Vous ne pouvez gérer que vos propres cours."}, status=403)
    return course, None


def _owned_chapter(request: HttpRequest, pk: int):
    try:
        ch = Chapter.objects.select_related("course").get(pk=pk)
    except Chapter.DoesNotExist:
        return None, JsonResponse({"error": "Chapitre introuvable."}, status=404)
    if not _can_manage(request.user, ch.course):
        return None, JsonResponse({"error": "Accès refusé."}, status=403)
    return ch, None


@login_required(login_url=LOGIN_PATH)
def course_manage(request: HttpRequest, pk: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=pk)
    if not _can_manage(request.user, course):
        messages.error(request, "Vous ne pouvez gérer que les cours qui vous sont attribués.")
        return redirect("formation:dashboard")
    return render(request, "formation/course_manage.html", {
        "course": course,
        "chapters_json": json.dumps([av._serialize_chapter(c) for c in course.chapters.all()]),
        "banner_url": course.banner.url if course.banner else "",
        "storage_enabled": av._storage_enabled(),
        "profile": _profile(request.user),
    })


@login_required(login_url=LOGIN_PATH)
@require_http_methods(["POST"])
def t_chapter_create(request: HttpRequest, pk: int) -> HttpResponse:
    course, err = _owned_course(request, pk)
    if err:
        return err
    cleaned, e = av._clean_chapter_data(_json(request), partial=False)
    if e:
        return JsonResponse({"error": e}, status=400)
    last = course.chapters.aggregate(m=Max("position"))["m"]
    cleaned["position"] = (last + 1) if last is not None else 0
    ch = Chapter.objects.create(course=course, **cleaned)
    return JsonResponse(av._serialize_chapter(ch), status=201)


@login_required(login_url=LOGIN_PATH)
@require_http_methods(["PUT", "DELETE"])
def t_chapter_detail(request: HttpRequest, pk: int) -> HttpResponse:
    ch, err = _owned_chapter(request, pk)
    if err:
        return err
    if request.method == "PUT":
        cleaned, e = av._clean_chapter_data(_json(request), partial=True)
        if e:
            return JsonResponse({"error": e}, status=400)
        for k, v in cleaned.items():
            setattr(ch, k, v)
        ch.save()
        return JsonResponse(av._serialize_chapter(ch))
    ch.delete()
    return JsonResponse({"ok": True})


@login_required(login_url=LOGIN_PATH)
@require_http_methods(["POST"])
def t_chapter_reorder(request: HttpRequest, pk: int) -> HttpResponse:
    course, err = _owned_course(request, pk)
    if err:
        return err
    for idx, cid in enumerate(_json(request).get("order") or []):
        if str(cid).isdigit():
            Chapter.objects.filter(pk=int(cid), course_id=course.pk).update(position=idx)
    return JsonResponse({"ok": True})


@login_required(login_url=LOGIN_PATH)
@require_http_methods(["POST"])
def t_video_url(request: HttpRequest, pk: int) -> HttpResponse:
    ch, err = _owned_chapter(request, pk)
    if err:
        return err
    if not av._storage_enabled():
        return JsonResponse({"error": "Le stockage n'est pas configuré."}, status=400)
    data = _json(request)
    filename = str(data.get("filename") or "video.mp4")
    content_type = str(data.get("content_type") or "").strip() or "video/mp4"
    if not content_type.startswith("video/"):
        return JsonResponse({"error": "Le fichier doit être une vidéo."}, status=400)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "mp4"
    if ext not in av._ALLOWED_VIDEO_EXT:
        return JsonResponse({"error": "Format vidéo non supporté (mp4, webm, mov…)."}, status=400)
    key = f"courses/videos/chapter_{pk}.{ext}"
    client, bucket = av._s3_client_and_bucket(private=True)
    url = client.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=3600,
    )
    return JsonResponse({"url": url, "key": key, "content_type": content_type})


@login_required(login_url=LOGIN_PATH)
@require_http_methods(["POST"])
def t_video_confirm(request: HttpRequest, pk: int) -> HttpResponse:
    ch, err = _owned_chapter(request, pk)
    if err:
        return err
    key = str(_json(request).get("key") or "").strip()
    if not key or not key.startswith(f"courses/videos/chapter_{pk}."):
        return JsonResponse({"error": "Clé de fichier invalide."}, status=400)
    old_name = ch.video.name if ch.video else ""
    ch.video.name = key
    ch.save(update_fields=["video"])
    # Storage du champ (bucket PRIVÉ), pas le storage public par défaut.
    if old_name and old_name != key:
        try:
            ch.video.storage.delete(old_name)
        except Exception:
            pass
    return JsonResponse(av._serialize_chapter(ch))


@login_required(login_url=LOGIN_PATH)
@require_http_methods(["POST"])
def t_video_remove(request: HttpRequest, pk: int) -> HttpResponse:
    ch, err = _owned_chapter(request, pk)
    if err:
        return err
    if ch.video:
        try:
            ch.video.delete(save=False)
        except Exception:
            pass
        ch.video = ""
        ch.save(update_fields=["video"])
    return JsonResponse(av._serialize_chapter(ch))


@login_required(login_url=LOGIN_PATH)
@require_http_methods(["POST"])
def t_banner_upload(request: HttpRequest, pk: int) -> HttpResponse:
    course, err = _owned_course(request, pk)
    if err:
        return err
    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"error": "Aucun fichier fourni."}, status=400)
    if f.size > av._MAX_UPLOAD_BYTES:
        return JsonResponse({"error": "Image trop volumineuse (max 5 Mo)."}, status=400)
    if not (getattr(f, "content_type", "") or "").startswith("image/"):
        return JsonResponse({"error": "Le fichier doit être une image."}, status=400)
    old_name = course.banner.name if course.banner else ""
    course.banner = f
    course.save(update_fields=["banner"])
    new_name = course.banner.name
    if old_name and old_name != new_name:
        try:
            default_storage.delete(old_name)
        except Exception:
            pass
    return JsonResponse({"ok": True, "url": course.banner.url})
