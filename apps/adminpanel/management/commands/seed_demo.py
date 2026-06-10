from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.adminpanel.models import (
    AdminNotification,
    ContactRequest,
    Course,
    Enrollment,
    GEI,
    Member,
    Payment,
    PaymentProvider,
    Testimonial,
    VenueBooking,
)


class Command(BaseCommand):
    help = "Ajoute les données de démonstration IMSO"

    def handle(self, *args, **options):
        self.stdout.write("Ajout des données de démonstration...")

        now = timezone.now()
        today = date.today()

        # ── GEI ────────────────────────────────────────────
        gei_data = [
            ("Pétion-Ville", "Pétion-Ville", "Marie-Claude Bernard"),
            ("Delmas", "Delmas", "Jean-Robert Alexis"),
            ("Cap-Haïtien", "Cap-Haïtien", "Pierre-Richard Estimé"),
            ("Jacmel", "Jacmel", "Sophie Destiné"),
            ("Les Cayes", "Les Cayes", "Carline Pierre-Louis"),
            ("Gonaïves", "Gonaïves", "Edner Saint-Vil"),
            ("Saint-Marc", "Saint-Marc", "Marc Donald Noël"),
            ("Jérémie", "Jérémie", "Rose Ménélas"),
            ("Fort-Liberté", "Fort-Liberté", "Paul Emmanuel"),
            ("Port-de-Paix", "Port-de-Paix", "Fabienne Pamphile"),
        ]
        created_geis = []
        for name, city, coord in gei_data:
            gei, created = GEI.objects.get_or_create(
                name=name, city=city,
                defaults={"coordinator": coord, "is_active": True},
            )
            created_geis.append(gei)
            if created:
                self.stdout.write(f"  + GEI: {name} ({city})")
        gei_map = {g.city: g for g in GEI.objects.all()}

        # ── Cours ──────────────────────────────────────────
        courses_data = [
            {
                "title": "Tenir une comptabilité simple pour son commerce",
                "category": "Gestion",
                "instructor": "Rosemène Joseph",
                "city": "Port-au-Prince",
                "price_htg": 2500,
                "capacity": 30,
                "description": "Apprenez les bases de la comptabilité pour gérer les finances de votre commerce au quotidien. Tenue de livre, suivi des dépenses, calcul des bénéfices.",
            },
            {
                "title": "Lancer un atelier de transformation agroalimentaire",
                "category": "Entrepreneuriat",
                "instructor": "Marc-Donald Pierre",
                "city": "Cap-Haïtien",
                "price_htg": 3800,
                "capacity": 25,
                "description": "Formation complète pour lancer votre atelier de transformation de produits locaux : confitures, jus, farines, fruits séchés.",
            },
            {
                "title": "Vendre ses produits sur les marchés et en ligne",
                "category": "Marketing",
                "instructor": "Fabienne Pamphile",
                "city": "Jacmel",
                "price_htg": 2200,
                "capacity": 35,
                "description": "Maîtrisez les techniques de vente sur les marchés traditionnels et les plateformes numériques. Stratégies de prix, relation client, présence digitale.",
            },
            {
                "title": "Épargne et crédit : les bases du GEI",
                "category": "Finance",
                "instructor": "Edner Saint-Vil",
                "city": "Gonaïves",
                "price_htg": 1500,
                "capacity": 40,
                "description": "Comprenez le fonctionnement des Groupes d'Épargne et d'Investissement. Épargne collective, octroi de crédit, suivi des remboursements.",
            },
            {
                "title": "Techniques de leadership féminin",
                "category": "Développement personnel",
                "instructor": "Carline Pierre-Louis",
                "city": "Les Cayes",
                "price_htg": 1800,
                "capacity": 30,
                "description": "Renforcez vos compétences en leadership, prise de parole en public, négociation et gestion d'équipe. Un programme conçu pour les femmes entrepreneures.",
            },
            {
                "title": "Gestion de micro-entreprise",
                "category": "Entrepreneuriat",
                "instructor": "Jean-Robert Alexis",
                "city": "Delmas",
                "price_htg": 3000,
                "capacity": 28,
                "description": "De l'idée au business plan : apprenez à structurer votre micro-entreprise, gérer votre trésorerie, et développer votre clientèle.",
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
                "text": "Un microcrédit obtenu en quelques semaines m'a permis d'acheter un four professionnel. Ma pâtisserie tient grâce à la solidarité du groupe.",
                "sort_order": 5,
            },
            {
                "author_name": "Rose-Michelle Alexis",
                "author_initials": "RA",
                "location": "GEI Delmas · 2 ans",
                "text": "IMSO m'a accompagnée dans la création de ma boutique en ligne. Aujourd'hui je vends mes bijoux artisanaux dans tout le pays et je forme d'autres femmes.",
                "sort_order": 6,
            },
            {
                "author_name": "Jean-Wesley Noël",
                "author_initials": "JN",
                "location": "GEI Saint-Marc · 3 ans",
                "text": "Le crédit obtenu via mon GEI m'a permis d'acheter un terrain pour cultiver des légumes. Je fournis maintenant trois hôtels de la région.",
                "sort_order": 7,
            },
            {
                "author_name": "Anne-Marie Joseph",
                "author_initials": "AJ",
                "location": "GEI Jérémie · 1 an",
                "text": "Je n'avais jamais eu accès à un compte bancaire. IMSO m'a appris l'épargne et aujourd'hui j'ai un petit commerce de produits secs qui nourrit ma famille.",
                "sort_order": 8,
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
                self.stdout.write(f"  + Témoignage: {t['author_name']}")

        # ── Membres ─────────────────────────────────────────
        members_data = [
            # Pétion-Ville
            ("Marie", "Claude Bernard", "mc.bernard@email.com", "+509 31 00 00 01", "Pétion-Ville", Member.Status.ACTIVE, 1500),
            ("Jean", "Baptiste Louis", "jblouis@email.com", "+509 31 00 00 02", "Pétion-Ville", Member.Status.ACTIVE, 2000),
            ("Rose", "Ménélas", "rose.menelas@email.com", "+509 31 00 00 03", "Pétion-Ville", Member.Status.ACTIVE, 1000),
            ("Carline", "Pierre", "carline.pierre@email.com", "+509 31 00 00 09", "Pétion-Ville", Member.Status.ACTIVE, 2500),
            ("Michel", "Ange Jean", "michel.ange@email.com", "+509 31 00 00 08", "Pétion-Ville", Member.Status.PAUSED, 500),
            # Delmas
            ("Jean-Robert", "Alexis", "jr.alexis@email.com", "+509 31 00 00 13", "Delmas", Member.Status.ACTIVE, 3000),
            ("Nadège", "Fontilus", "nadege.font@email.com", "+509 31 00 00 14", "Delmas", Member.Status.ACTIVE, 1200),
            ("Frantz", "Sénèque", "frantz.seneque@email.com", "+509 31 00 00 15", "Delmas", Member.Status.ACTIVE, 1800),
            ("Bénita", "Auguste", "benita.auguste@email.com", "+509 31 00 00 16", "Delmas", Member.Status.PROSPECT, 0),
            # Cap-Haïtien
            ("Pierre", "Richard Estimé", "pr.estime@email.com", "+509 31 00 00 04", "Cap-Haïtien", Member.Status.ACTIVE, 2200),
            ("Anne", "Marie Noël", "anne.noel@email.com", "+509 31 00 00 05", "Cap-Haïtien", Member.Status.ACTIVE, 1700),
            ("Paul", "Emmanuel", "paul.emmanuel@email.com", "+509 31 00 00 06", "Cap-Haïtien", Member.Status.ACTIVE, 1300),
            ("Marc", "Donald Jean", "md.jean@email.com", "+509 31 00 00 12", "Cap-Haïtien", Member.Status.ALUMNI, 0),
            ("Lunise", "Pierre-Louis", "lunise.pl@email.com", "+509 31 00 00 17", "Cap-Haïtien", Member.Status.ACTIVE, 900),
            # Jacmel
            ("Sophie", "Destiné", "sophie.destine@email.com", "+509 31 00 00 07", "Jacmel", Member.Status.ACTIVE, 1600),
            ("Fabienne", "Pamphile", "fabienne.pamphile@email.com", "+509 31 00 00 11", "Jacmel", Member.Status.ACTIVE, 1400),
            ("Edwidge", "Danticat", "edwidge.danticat@email.com", "+509 31 00 00 18", "Jacmel", Member.Status.ACTIVE, 2000),
            ("René", "Préval", "rene.preval@email.com", "+509 31 00 00 19", "Jacmel", Member.Status.PAUSED, 800),
            # Les Cayes
            ("Carline", "Louis", "carline.louis@email.com", "+509 31 00 00 10", "Les Cayes", Member.Status.ACTIVE, 1900),
            ("Dieudonné", "Fils-Aimé", "d.filsaime@email.com", "+509 31 00 00 20", "Les Cayes", Member.Status.ACTIVE, 1100),
            ("Magalie", "Fleurant", "magalie.fleurant@email.com", "+509 31 00 00 21", "Les Cayes", Member.Status.PROSPECT, 0),
            # Gonaïves
            ("Edner", "Saint-Vil", "edner.saintvil@email.com", "+509 31 00 00 22", "Gonaïves", Member.Status.ACTIVE, 2800),
            ("Wideline", "Sylvain", "wideline.sylvain@email.com", "+509 31 00 00 23", "Gonaïves", Member.Status.ACTIVE, 900),
            # Saint-Marc
            ("Marc", "Donald Noël", "md.noel@email.com", "+509 31 00 00 24", "Saint-Marc", Member.Status.ACTIVE, 2100),
            ("Marie", "Josèphe", "marie.josephe@email.com", "+509 31 00 00 25", "Saint-Marc", Member.Status.ACTIVE, 1300),
            # Jérémie
            ("Rose", "Ménélas", "rose.menelas2@email.com", "+509 31 00 00 26", "Jérémie", Member.Status.ACTIVE, 1000),
            ("Alcide", "Fénélus", "alcide.fenelus@email.com", "+509 31 00 00 27", "Jérémie", Member.Status.PROSPECT, 0),
            # Fort-Liberté
            ("Paul", "Emmanuel", "paul.emmanuel2@email.com", "+509 31 00 00 28", "Fort-Liberté", Member.Status.ACTIVE, 1200),
            ("Marie", "Carole", "marie.carole@email.com", "+509 31 00 00 29", "Fort-Liberté", Member.Status.PAUSED, 700),
            # Port-de-Paix
            ("Fabienne", "Pamphile", "fabienne.pamphile2@email.com", "+509 31 00 00 30", "Port-de-Paix", Member.Status.ACTIVE, 1500),
        ]

        member_objects = []
        for first, last, email, phone, city, status, saving in members_data:
            gei = gei_map.get(city)
            member, created = Member.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "phone": phone,
                    "gei": gei,
                    "status": status,
                    "joined_at": today - timedelta(days=hash(f"{first}{last}") % 730),
                    "monthly_saving_htg": saving,
                },
            )
            if created:
                self.stdout.write(f"  + Membre: {first} {last}")
            member_objects.append(member)

        # ── Paiements ───────────────────────────────────────
        courses = list(Course.objects.all())
        active_members = Member.objects.filter(status=Member.Status.ACTIVE)[:15]

        for i, m in enumerate(active_members):
            if i % 3 == 0:
                continue
            purpose = Payment.Purpose.MEMBERSHIP if i % 2 == 0 else Payment.Purpose.COURSE
            amount = 500 + (i * 250) if purpose == "membership" else 2500
            status = Payment.Status.PAID if i % 4 != 0 else Payment.Status.PENDING
            pay, created = Payment.objects.get_or_create(
                reference=f"IMSO-SEED-{i+1:04d}",
                defaults={
                    "purpose": purpose,
                    "status": status,
                    "entry_mode": Payment.EntryMode.MANUAL,
                    "payer_name": str(m),
                    "payer_phone": m.phone,
                    "payer_email": m.email,
                    "amount_htg": amount,
                    "paid_at": now - timedelta(days=i * 5) if status == "paid" else None,
                    "notes": "",
                },
            )
            if created:
                self.stdout.write(f"  + Paiement: {pay.reference} - {amount} HTG")

        # ── Réservations de salle ───────────────────────────
        booking_data = [
            ("Sophie Destiné", "+509 31 00 00 07", "sophie.destine@email.com", "Mariage civil", today + timedelta(days=30), "09:00", "16:00", 80, VenueBooking.Status.CONFIRMED),
            ("Jean-Baptiste Louis", "+509 31 00 00 02", "jblouis@email.com", "Séminaire", today + timedelta(days=14), "08:00", "17:00", 40, VenueBooking.Status.CONFIRMED),
            ("Nadège Fontilus", "+509 31 00 00 14", "nadege.font@email.com", "Atelier artisanal", today + timedelta(days=7), "13:00", "18:00", 25, VenueBooking.Status.PAYMENT_PENDING),
            ("Magalie Fleurant", "+509 31 00 00 21", "magalie.fleurant@email.com", "Anniversaire", today + timedelta(days=60), "10:00", "22:00", 100, VenueBooking.Status.REQUESTED),
            ("Frantz Sénèque", "+509 31 00 00 15", "frantz.seneque@email.com", "Formation entreprise", today + timedelta(days=21), "08:00", "15:00", 35, VenueBooking.Status.CONFIRMED),
            ("Alcide Fénélus", "+509 31 00 00 27", "alcide.fenelus@email.com", "Conférence", today + timedelta(days=45), "14:00", "18:00", 60, VenueBooking.Status.REQUESTED),
        ]
        for name, phone, email, etype, edate, stime, etime, guests, status in booking_data:
            booking, created = VenueBooking.objects.get_or_create(
                requester_name=name,
                event_date=edate,
                defaults={
                    "requester_phone": phone,
                    "requester_email": email,
                    "event_type": etype,
                    "start_time": stime,
                    "end_time": etime,
                    "guest_count": guests,
                    "status": status,
                    "notes": "",
                },
            )
            if created:
                self.stdout.write(f"  + Réservation: {etype} - {edate}")

        # ── Inscriptions (Enrollments) ──────────────────────
        for i, m in enumerate(active_members[:10]):
            course = courses[i % len(courses)]
            enrollment, created = Enrollment.objects.get_or_create(
                member=m,
                course=course,
                defaults={"status": Enrollment.Status.CONFIRMED if i < 7 else Enrollment.Status.PENDING},
            )
            if created:
                self.stdout.write(f"  + Inscription: {m} -> {course.title}")

        # ── Contacts ────────────────────────────────────────
        contacts_data = [
            ("Marie-Ange Pierre", "+509 37 00 00 01", "ma.pierre@email.com", ContactRequest.Subject.MEMBERSHIP, "Bonjour, je souhaite rejoindre un GEI à Pétion-Ville. Pouvez-vous m'indiquer la marche à suivre ?"),
            ("Daniel Saint-Jean", "+509 37 00 00 02", "d.saintjean@email.com", ContactRequest.Subject.COURSE, "Je suis intéressé par le cours de comptabilité. Avez-vous des sessions le samedi ?"),
            ("Claudine Morisset", "+509 37 00 00 03", "", ContactRequest.Subject.VENUE, "Je voudrais réserver la salle pour une réunion de 15 personnes le mois prochain."),
            ("Wilson Charles", "+509 37 00 00 04", "w.charles@email.com", ContactRequest.Subject.MENTOR, "Je suis retraité et je voudrais devenir mentor pour aider les jeunes entrepreneurs."),
        ]
        for full_name, phone, email, subject, message in contacts_data:
            contact, created = ContactRequest.objects.get_or_create(
                full_name=full_name,
                defaults={
                    "phone": phone,
                    "email": email,
                    "subject": subject,
                    "message": message,
                    "is_processed": False,
                },
            )
            if created:
                self.stdout.write(f"  + Contact: {full_name}")

        # ── Pourvoyeurs de paiement ─────────────────────────
        providers_data = [
            ("MonCash", PaymentProvider.ProviderType.MONCASH, True, "Envoyez votre paiement via MonCash au 509 37 00 00 10", 0),
            ("NatCash", PaymentProvider.ProviderType.NATCASH, True, "Envoyez votre paiement via NatCash au 509 37 00 00 11", 1),
            ("Virement bancaire", PaymentProvider.ProviderType.BANK, True, "Banque de la République d'Haïti (BRH) - Compte: 001-234-5678", 2),
            ("Paiement en espèces", PaymentProvider.ProviderType.CASH, True, "Rendez-vous à notre bureau du lundi au vendredi de 9h à 16h", 3),
        ]
        for name, ptype, active, instructions, sort_order in providers_data:
            provider, created = PaymentProvider.objects.get_or_create(
                name=name,
                defaults={
                    "provider_type": ptype,
                    "is_active": active,
                    "instructions": instructions,
                    "sort_order": sort_order,
                },
            )
            if created:
                self.stdout.write(f"  + Fournisseur: {name}")

        # ── Notifications ───────────────────────────────────
        notifications_data = [
            ("Nouvelle réservation de salle par Nadège Fontilus", AdminNotification.NotificationType.NEW_BOOKING),
            ("Paiement reçu de Sophie Destiné - 2500 HTG", AdminNotification.NotificationType.PAYMENT_RECEIVED),
            ("Nouveau message de Marie-Ange Pierre", AdminNotification.NotificationType.NEW_CONTACT),
            ("Inscription au cours : Tenir une comptabilité simple", AdminNotification.NotificationType.NEW_ENROLLMENT),
        ]
        for msg, ntype in notifications_data:
            notif, created = AdminNotification.objects.get_or_create(
                message=msg,
                notification_type=ntype,
                defaults={"is_read": False, "created_at": now - timedelta(hours=len(msg))},
            )
            if created:
                self.stdout.write(f"  + Notification: {ntype}")

        # ── Résumé ──────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS("Données de démonstration ajoutées avec succès."))
        self.stdout.write("")
        self.stdout.write("Résumé :")
        self.stdout.write(f"  GEI          : {GEI.objects.count()}")
        self.stdout.write(f"  Cours         : {Course.objects.filter(is_active=True).count()}")
        self.stdout.write(f"  Témoignages   : {Testimonial.objects.filter(is_active=True).count()}")
        self.stdout.write(f"  Membres       : {Member.objects.count()} (actifs: {Member.objects.filter(status=Member.Status.ACTIVE).count()})")
        self.stdout.write(f"  Paiements     : {Payment.objects.count()}")
        self.stdout.write(f"  Réservations  : {VenueBooking.objects.count()}")
        self.stdout.write(f"  Inscriptions  : {Enrollment.objects.count()}")
        self.stdout.write(f"  Contacts      : {ContactRequest.objects.count()}")
        self.stdout.write(f"  Fournisseurs  : {PaymentProvider.objects.count()}")
