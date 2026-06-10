from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.adminpanel.models import (
    Course,
    GEI,
    Member,
    Testimonial,
)


class Command(BaseCommand):
    help = "Ajoute les données de démonstration IMSO"

    def handle(self, *args, **options):
        self.stdout.write("Ajout des données de démonstration...")

        # ── GEI ────────────────────────────────────────────
        geis_data = [
            ("Pétion-Ville", "Pétion-Ville"),
            ("Cap-Haïtien", "Cap-Haïtien"),
            ("Jacmel", "Jacmel"),
            ("Gonaïves", "Gonaïves"),
            ("Les Cayes", "Les Cayes"),
        ]
        for name, city in geis_data:
            gei, created = GEI.objects.get_or_create(
                name=name, city=city,
                defaults={"coordinator": "", "is_active": True},
            )
            if created:
                self.stdout.write(f"  + GEI: {name}")

        # ── Cours ──────────────────────────────────────────
        courses_data = [
            {
                "title": "Tenir une comptabilité simple pour son commerce",
                "category": "Gestion",
                "instructor": "Rosemène Joseph",
                "city": "Port-au-Prince",
                "price_htg": 2500,
                "capacity": 30,
                "description": "Apprenez les bases de la comptabilité pour gérer les finances de votre commerce.",
            },
            {
                "title": "Lancer un atelier de transformation agroalimentaire",
                "category": "Entrepreneuriat",
                "instructor": "Marc-Donald Pierre",
                "city": "Cap-Haïtien",
                "price_htg": 3800,
                "capacity": 25,
                "description": "Formation complète pour lancer votre atelier de transformation de produits locaux.",
            },
            {
                "title": "Vendre ses produits sur les marchés et en ligne",
                "category": "Marketing",
                "instructor": "Fabienne Pamphile",
                "city": "Jacmel",
                "price_htg": 2200,
                "capacity": 35,
                "description": "Maîtrisez les techniques de vente sur les marchés traditionnels et les plateformes numériques.",
            },
        ]
        for c in courses_data:
            course, created = Course.objects.get_or_create(
                title=c["title"],
                defaults={
                    "category": c["category"],
                    "instructor": c["instructor"],
                    "city": c["city"],
                    "price_htg": c["price_htg"],
                    "capacity": c["capacity"],
                    "description": c["description"],
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(f"  + Cours: {c['title']}")

        # ── Témoignages ────────────────────────────────────
        testimonials_data = [
            {
                "author_name": "Mirlande Jean-Baptiste",
                "author_initials": "MJ",
                "location": "GEI Pétion-Ville · 2 ans",
                "text": "Grâce à IMSO, j'ai pu agrandir mon atelier de couture et embaucher deux apprenties. Le mentorat m'a appris à tenir mes comptes correctement pour la première fois.",
                "sort_order": 1,
            },
            {
                "author_name": "Jacques Villard",
                "author_initials": "JV",
                "location": "GEI Cap-Haïtien · 1 an",
                "text": "Le GEI m'a fait confiance pour lancer ma petite épicerie de quartier. Les remboursements sont alignés sur mes revenus, et la formation en marketing local a changé ma façon de vendre.",
                "sort_order": 2,
            },
            {
                "author_name": "Sherline Désir",
                "author_initials": "SD",
                "location": "GEI Jacmel · 3 ans",
                "text": "Ce que j'aime à IMSO, c'est la transparence. Chaque cotisation est tracée et les décisions se prennent ensemble. Je me sens vraiment actrice de mon avenir financier.",
                "sort_order": 3,
            },
            {
                "author_name": "Edner Beauvais",
                "author_initials": "EB",
                "location": "GEI Gonaïves · 4 ans",
                "text": "J'ai débuté comme épargnant. Aujourd'hui je forme moi-même les nouveaux membres en comptabilité simple. IMSO transforme les parcours en compétences partagées.",
                "sort_order": 4,
            },
            {
                "author_name": "Carline Louis",
                "author_initials": "CL",
                "location": "GEI Les Cayes · 1 an",
                "text": "Un microcrédit obtenu en quelques semaines m'a permis d'acheter un four professionnel. Ma pâtisserie tient grâce à la solidarité du groupe, pas grâce à un collatéral impossible à fournir.",
                "sort_order": 5,
            },
        ]
        for t in testimonials_data:
            testimonial, created = Testimonial.objects.get_or_create(
                author_name=t["author_name"],
                defaults={
                    "author_initials": t["author_initials"],
                    "location": t["location"],
                    "text": t["text"],
                    "sort_order": t["sort_order"],
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(f"  + Temoignage: {t['author_name']}")

        # ── Membres ─────────────────────────────────────────
        from datetime import date

        members_data = [
            ("Marie", "Claude", "marie.claude@email.com", "+509 31 00 00 01", "Pétion-Ville", Member.Status.ACTIVE),
            ("Jean", "Baptiste", "jean.baptiste@email.com", "+509 31 00 00 02", "Pétion-Ville", Member.Status.ACTIVE),
            ("Rose", "Meneus", "rose.meneus@email.com", "+509 31 00 00 03", "Pétion-Ville", Member.Status.ACTIVE),
            ("Pierre", "Richard", "pierre.richard@email.com", "+509 31 00 00 04", "Cap-Haïtien", Member.Status.ACTIVE),
            ("Anne", "Marie", "anne.marie@email.com", "+509 31 00 00 05", "Cap-Haïtien", Member.Status.ACTIVE),
            ("Paul", "Emmanuel", "paul.emmanuel@email.com", "+509 31 00 00 06", "Cap-Haïtien", Member.Status.ACTIVE),
            ("Sophie", "Destin", "sophie.destin@email.com", "+509 31 00 00 07", "Jacmel", Member.Status.ACTIVE),
            ("Michel", "Ange", "michel.ange@email.com", "+509 31 00 00 08", "Jacmel", Member.Status.ACTIVE),
            ("Carline", "Pierre", "carline.pierre@email.com", "+509 31 00 00 09", "Pétion-Ville", Member.Status.ACTIVE),
            ("Edner", "Saint", "edner.saint@email.com", "+509 31 00 00 10", "Gonaïves", Member.Status.ACTIVE),
            ("Fabienne", "Noel", "fabienne.noel@email.com", "+509 31 00 00 11", "Jacmel", Member.Status.ACTIVE),
            ("Marc", "Donald", "marc.donald@email.com", "+509 31 00 00 12", "Cap-Haïtien", Member.Status.ACTIVE),
        ]

        gei_map = {g.city: g for g in GEI.objects.all()}

        for first, last, email, phone, city, status in members_data:
            gei = gei_map.get(city)
            member, created = Member.objects.get_or_create(
                first_name=first,
                last_name=last,
                defaults={
                    "email": email,
                    "phone": phone,
                    "gei": gei,
                    "status": status,
                    "joined_at": date.today(),
                    "monthly_saving_htg": 0,
                },
            )
            if created:
                self.stdout.write(f"  + Membre: {first} {last}")

        self.stdout.write(self.style.SUCCESS("Donnees de demonstration ajoutees avec succes."))
        self.stdout.write("")
        self.stdout.write("Resume :")
        self.stdout.write(f"  GEI : {GEI.objects.count()}")
        self.stdout.write(f"  Cours : {Course.objects.filter(is_active=True).count()}")
        self.stdout.write(f"  Temoignages : {Testimonial.objects.filter(is_active=True).count()}")
        self.stdout.write(f"  Membres actifs : {Member.objects.filter(status=Member.Status.ACTIVE).count()}")
