"""Crée des données de démonstration pour la plateforme de formation.

Étudiants, professeurs (avec différents statuts KYC), inscriptions et progression.
Idempotent (basé sur l'email @demo.imso) — relançable sans doublon.

    python manage.py seed_formation_demo
    python manage.py seed_formation_demo --clear   # supprime les comptes de démo
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.adminpanel.models import (
    Chapter,
    ChapterCompletion,
    Course,
    CourseEnrollment,
    Profile,
)

DEMO_DOMAIN = "@demo.imso"

STUDENTS = [
    "Marie Joseph", "Jean Baptiste", "Nadège Pierre", "Frantz Louis",
    "Guerline Charles", "Widlin Toussaint",
]
TEACHERS = [
    ("Roberto Étienne", "approved"),
    ("Sabine Moïse", "submitted"),
    ("Jacques Dorval", "not_submitted"),
]


class Command(BaseCommand):
    help = "Crée (ou supprime avec --clear) des données de démo pour la formation."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Supprimer les comptes de démo")

    def handle(self, *args, **options):
        if options["clear"]:
            n = User.objects.filter(email__endswith=DEMO_DOMAIN).count()
            User.objects.filter(email__endswith=DEMO_DOMAIN).delete()
            self.stdout.write(self.style.SUCCESS(f"{n} compte(s) de démo supprimé(s)."))
            return

        def make_user(full_name, idx, role, kyc):
            email = f"{role}{idx}{DEMO_DOMAIN}"
            user, created = User.objects.get_or_create(
                username=email, defaults={"email": email}
            )
            if created:
                parts = full_name.split(" ", 1)
                user.first_name = parts[0]
                user.last_name = parts[1] if len(parts) > 1 else ""
                user.email = email
                user.set_password("demo12345")
                user.save()
            Profile.objects.get_or_create(
                user=user,
                defaults={
                    "role": role,
                    "is_approved": (role == "student" or kyc == "approved"),
                    "kyc_status": "approved" if role == "student" else kyc,
                    "id_number": "" if role == "student" else f"CIN-{1000 + idx}",
                    "phone": f"+509 3{idx}{idx} 00 00",
                },
            )
            return user

        students = [make_user(n, i + 1, "student", "approved") for i, n in enumerate(STUDENTS)]
        teachers = [make_user(n, i + 1, "teacher", k) for i, (n, k) in enumerate(TEACHERS)]

        # Assigner les profs approuvés à des cours existants (si présents)
        approved_teachers = [t for t, (_, k) in zip(teachers, TEACHERS) if k == "approved"]
        courses = list(Course.objects.all()[:6])
        for i, co in enumerate(courses):
            if approved_teachers and not co.teacher_id:
                co.teacher = approved_teachers[i % len(approved_teachers)]
                co.save(update_fields=["teacher"])

        # Inscriptions + progression
        enrolls = 0
        for i, stu in enumerate(students):
            for co in courses[: (i % 3) + 1]:
                status = "active" if (co.price_htg == 0 or i % 2 == 0) else "pending_payment"
                _, created = CourseEnrollment.objects.get_or_create(
                    student=stu, course=co, defaults={"status": status}
                )
                if created:
                    enrolls += 1
                if status == "active":
                    for ch in Chapter.objects.filter(course=co)[: i % 3]:
                        ChapterCompletion.objects.get_or_create(student=stu, chapter=ch)

        self.stdout.write(self.style.SUCCESS(
            f"Démo formation : {len(students)} étudiants, {len(teachers)} professeurs, "
            f"{enrolls} inscriptions. Mot de passe : demo12345"
        ))
