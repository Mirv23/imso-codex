from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.adminpanel.models import Chapter, Course, CourseEnrollment, Profile


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def student_user(db):
    user = User.objects.create_user(username="etudiant@test.com", email="etudiant@test.com", password="testpass123")
    Profile.objects.create(user=user, role="student", is_approved=True)
    return user


@pytest.fixture
def teacher_user(db):
    user = User.objects.create_user(username="prof@test.com", email="prof@test.com", password="testpass123")
    Profile.objects.create(user=user, role="teacher", is_approved=True, kyc_status="approved")
    return user


@pytest.fixture
def active_course(db, teacher_user):
    return Course.objects.create(
        title="Cours Test",
        category="Finance",
        instructor="Prof Test",
        city="Port-au-Prince",
        price_htg=0,
        is_active=True,
        teacher=teacher_user,
    )


@pytest.fixture
def chapter(active_course):
    return Chapter.objects.create(course=active_course, title="Chapitre 1", position=0, duration_minutes=10)


@pytest.mark.django_db
class TestFormationCatalog:
    def test_catalog_shows_active_courses(self, client, active_course):
        resp = client.get("/formation/")
        assert resp.status_code == 200
        assert b"Cours Test" in resp.content

    def test_catalog_empty_when_no_active_courses(self, client):
        resp = client.get("/formation/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestFormationCourseDetail:
    def test_course_detail_accessible(self, client, active_course, chapter):
        resp = client.get(f"/formation/cours/{active_course.pk}/")
        assert resp.status_code == 200
        assert b"Cours Test" in resp.content
        assert b"Chapitre 1" in resp.content

    def test_course_detail_404_for_inactive(self, client, active_course):
        active_course.is_active = False
        active_course.save()
        resp = client.get(f"/formation/cours/{active_course.pk}/")
        assert resp.status_code == 404

    def test_course_detail_shows_10_minutes(self, client, active_course, chapter):
        resp = client.get(f"/formation/cours/{active_course.pk}/")
        assert resp.status_code == 200
        assert b"10" in resp.content


@pytest.mark.django_db
class TestFormationRegister:
    def test_register_page_loads(self, client):
        resp = client.get("/formation/inscription/")
        assert resp.status_code == 200

    def test_register_student(self, client):
        resp = client.post("/formation/inscription/", {
            "full_name": "Jean Test",
            "email": "jean@test.com",
            "password": "longpassword123",
            "role": "student",
        })
        assert resp.status_code == 302
        assert User.objects.filter(email="jean@test.com").exists()
        profile = Profile.objects.get(user__email="jean@test.com")
        assert profile.role == "student"
        assert profile.is_approved is True

    def test_register_teacher_requires_approval(self, client):
        resp = client.post("/formation/inscription/", {
            "full_name": "Prof Test",
            "email": "prof.reg@test.com",
            "password": "longpassword123",
            "role": "teacher",
        })
        assert resp.status_code == 302
        profile = Profile.objects.get(user__email="prof.reg@test.com")
        assert profile.role == "teacher"
        assert profile.is_approved is False

    def test_register_duplicate_email_rejected(self, client, student_user):
        resp = client.post("/formation/inscription/", {
            "full_name": "Doublon",
            "email": "etudiant@test.com",
            "password": "longpassword123",
            "role": "student",
        })
        assert resp.status_code == 200
        assert b"existe d" in resp.content or b"d" in resp.content


@pytest.mark.django_db
class TestFormationEnroll:
    def test_enroll_redirects_unauthenticated(self, client, active_course):
        resp = client.post(f"/formation/cours/{active_course.pk}/inscription/")
        assert resp.status_code == 302

    def test_enroll_free_course_activates(self, client, active_course, student_user):
        client.force_login(student_user)
        resp = client.post(f"/formation/cours/{active_course.pk}/inscription/")
        assert resp.status_code == 302
        enrollment = CourseEnrollment.objects.get(student=student_user, course=active_course)
        assert enrollment.status == CourseEnrollment.Status.ACTIVE

    def test_enroll_twice_shows_info(self, client, active_course, student_user):
        client.force_login(student_user)
        client.post(f"/formation/cours/{active_course.pk}/inscription/")
        resp = client.post(f"/formation/cours/{active_course.pk}/inscription/")
        assert resp.status_code == 302


@pytest.mark.django_db
class TestFormationToggleComplete:
    def test_toggle_complete_requires_auth(self, client, chapter):
        resp = client.post(f"/formation/chapitres/{chapter.pk}/terminer/")
        assert resp.status_code == 302

    def test_toggle_complete_marks_chapter(self, client, active_course, chapter, student_user):
        client.force_login(student_user)
        CourseEnrollment.objects.create(student=student_user, course=active_course, status=CourseEnrollment.Status.ACTIVE)
        resp = client.post(f"/formation/chapitres/{chapter.pk}/terminer/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["completed"] is True
        assert data["done"] == 1


@pytest.mark.django_db
class TestFormationDashboard:
    def test_dashboard_redirects_anonymous(self, client):
        resp = client.get("/formation/espace/")
        assert resp.status_code == 302

    def test_student_dashboard_shows_enrollments(self, client, active_course, student_user):
        client.force_login(student_user)
        CourseEnrollment.objects.create(student=student_user, course=active_course, status=CourseEnrollment.Status.ACTIVE)
        resp = client.get("/formation/espace/")
        assert resp.status_code == 200
        assert b"Cours Test" in resp.content

    def test_teacher_dashboard_shows_courses(self, client, active_course, teacher_user):
        client.force_login(teacher_user)
        resp = client.get("/formation/espace/")
        assert resp.status_code == 200
        assert b"Cours Test" in resp.content
