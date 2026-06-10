from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Reinitialise toutes les donnees de l'admin panel a zero"

    def add_arguments(self, parser):
        parser.add_argument(
            "--seed",
            action="store_true",
            help="Ajoute les donnees de demonstration apres la reinitialisation",
        )

    def handle(self, *args, **options):
        tables = [
            "adminpanel_testimonial",
            "adminpanel_adminnotification",
            "adminpanel_dashboardmetric",
            "adminpanel_payment",
            "adminpanel_enrollment",
            "adminpanel_venuebooking",
            "adminpanel_contactrequest",
            "adminpanel_paymentprovider",
            "adminpanel_course",
            "adminpanel_member",
            "adminpanel_gei",
        ]

        self.stdout.write("Reinitialisation des donnees en cours...")

        for table in tables:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"DELETE FROM {table}")
                self.stdout.write(f"  + {table} vide")
            except Exception as e:
                self.stdout.write(f"  - {table}: ignore ({e})")

        self.stdout.write(self.style.SUCCESS("Toutes les donnees ont ete reinitialisees a 0."))

        if options.get("seed"):
            call_command("seed_demo")
