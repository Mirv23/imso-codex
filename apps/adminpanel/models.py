from __future__ import annotations

import base64
import hashlib
import os
import secrets

from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from .storage import private_media_storage


_FERNET_PREFIX = "fer:"   # nouveau chiffrement (Fernet / AES)
_LEGACY_PREFIX = "enc:"   # ancien XOR — encore lu pour compatibilité


def _fernet() -> Fernet:
    """Clé Fernet dérivée de FIELD_ENCRYPTION_KEY (ou DJANGO_SECRET_KEY en repli)."""
    key_material = os.environ.get("FIELD_ENCRYPTION_KEY") or os.environ.get("DJANGO_SECRET_KEY", "")
    digest = hashlib.sha256(key_material.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _legacy_xor_decrypt(ciphertext: str) -> str:
    key = (os.environ.get("DJANGO_SECRET_KEY", "") or "imso-fallback-key-32chars!!").encode("utf-8")
    raw = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
    result = bytes(raw[i] ^ key[i % len(key)] for i in range(len(raw)))
    return result.decode("utf-8")


def _decrypt_value(value: str) -> str:
    if value.startswith(_FERNET_PREFIX):
        try:
            return _fernet().decrypt(value[len(_FERNET_PREFIX):].encode("ascii")).decode("utf-8")
        except (InvalidToken, ValueError):
            return ""
    if value.startswith(_LEGACY_PREFIX):
        try:
            return _legacy_xor_decrypt(value[len(_LEGACY_PREFIX):])
        except Exception:
            return ""
    return value  # valeur héritée en clair


class EncryptedCharField(models.CharField):
    """Champ chiffré au repos avec Fernet (AES-128-CBC + HMAC).

    Lit encore les anciennes valeurs XOR (`enc:`) et les valeurs en clair, mais
    réécrit toujours en Fernet (`fer:`).
    """

    def from_db_value(self, value: str | None, expression: Any, connection: Any) -> str | None:
        if value is None:
            return value
        return _decrypt_value(value)

    def to_python(self, value: Any) -> Any:
        if isinstance(value, str) and (value.startswith(_FERNET_PREFIX) or value.startswith(_LEGACY_PREFIX)):
            return _decrypt_value(value)
        return value

    def get_prep_value(self, value: Any) -> str | None:
        if value is None:
            return None
        if value == "":
            return ""
        token = _fernet().encrypt(str(value).encode("utf-8")).decode("ascii")
        return _FERNET_PREFIX + token


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class GEI(TimestampedModel):
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=120)
    coordinator = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "GEI"
        verbose_name_plural = "GEI"
        ordering = ["city", "name"]

    def __str__(self) -> str:
        return f"{self.name} - {self.city}"


class Member(TimestampedModel):
    class Status(models.TextChoices):
        PROSPECT = "prospect", "Prospect"
        ACTIVE = "active", "Actif"
        PAUSED = "paused", "En pause"
        ALUMNI = "alumni", "Ancien membre"

    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    phone = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
    gei = models.ForeignKey(GEI, on_delete=models.SET_NULL, null=True, blank=True, related_name="members")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROSPECT)
    joined_at = models.DateField(null=True, blank=True)
    monthly_saving_htg = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Course(TimestampedModel):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Débutant"
        INTERMEDIATE = "intermediate", "Intermédiaire"
        ADVANCED = "advanced", "Avancé"

    title = models.CharField(max_length=180)
    category = models.CharField(max_length=80)
    instructor = models.CharField(max_length=120)
    city = models.CharField(max_length=120)
    price_htg = models.PositiveIntegerField(default=0)
    capacity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    public_slug = models.SlugField(max_length=200, blank=True, unique=True, null=True)
    description = models.TextField(blank=True)
    # Média (persistant uniquement avec un stockage objet type Supabase Storage)
    banner = models.FileField(upload_to="courses/banners/", blank=True)
    level = models.CharField(max_length=20, choices=Level.choices, blank=True)
    # Professeur (compte utilisateur) responsable du cours sur la plateforme.
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="courses_taught",
    )

    class Meta:
        ordering = ["category", "title"]

    def __str__(self) -> str:
        return self.title


class Chapter(TimestampedModel):
    """Un chapitre (leçon) d'un cours, avec un titre et une vidéo optionnelle."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=180)
    position = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    # La vidéo transite en direct navigateur -> stockage objet (jamais par l'app,
    # à cause de la limite de taille des fonctions serverless Vercel).
    # Bucket PRIVÉ : contenu payant, servi seulement via URL signée temporaire.
    video = models.FileField(
        upload_to="courses/videos/", blank=True, storage=private_media_storage
    )

    class Meta:
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return f"{self.course_id} · {self.position}. {self.title}"


class Profile(TimestampedModel):
    """Profil d'un utilisateur de la plateforme de formation (étudiant ou prof)."""
    class Role(models.TextChoices):
        STUDENT = "student", "Étudiant"
        TEACHER = "teacher", "Professeur"

    class KycStatus(models.TextChoices):
        NOT_SUBMITTED = "not_submitted", "Non soumis"
        SUBMITTED = "submitted", "En attente de vérification"
        APPROVED = "approved", "Vérifié"
        REJECTED = "rejected", "Rejeté"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField(max_length=40, blank=True)
    bio = models.TextField(blank=True)
    # Les profs restent en attente jusqu'à l'approbation d'un admin ; étudiants OK d'emblée.
    is_approved = models.BooleanField(default=True)
    # KYC (vérification d'identité des professeurs)
    kyc_status = models.CharField(max_length=20, choices=KycStatus.choices, default=KycStatus.NOT_SUBMITTED)
    id_number = models.CharField(max_length=60, blank=True)
    # Bucket PRIVÉ : pièce d'identité, servie seulement via URL signée temporaire.
    id_document = models.FileField(
        upload_to="kyc/", blank=True, storage=private_media_storage
    )
    kyc_note = models.CharField(max_length=200, blank=True)  # motif de rejet éventuel

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.username} ({self.role})"


class CourseEnrollment(TimestampedModel):
    """Inscription d'un étudiant (compte utilisateur) à un cours de la plateforme."""
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Paiement en attente"
        ACTIVE = "active", "Actif"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_enrollments"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="student_enrollments")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["student", "course"], name="unique_student_course")
        ]
        indexes = [models.Index(fields=["status"])]

    def __str__(self) -> str:
        return f"{self.student_id} -> {self.course_id} ({self.status})"


class ChapterCompletion(TimestampedModel):
    """Marque un chapitre comme terminé par un étudiant (suivi de progression)."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chapter_completions"
    )
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="completions")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "chapter"], name="unique_student_chapter")
        ]

    def __str__(self) -> str:
        return f"{self.student_id} ✓ {self.chapter_id}"


class Enrollment(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        CONFIRMED = "confirmed", "Confirmee"
        CANCELLED = "cancelled", "Annulee"

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollments")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        unique_together = ["member", "course"]
        constraints = [
            models.UniqueConstraint(
                fields=["member", "course"],
                name="unique_member_course",
                nulls_distinct=False,
            )
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.member} - {self.course}"


class VenueBooking(TimestampedModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Demandee"
        PAYMENT_PENDING = "payment_pending", "Paiement attendu"
        ADMIN_REVIEW = "admin_review", "Paiement recu - validation admin"
        CONFIRMED = "confirmed", "Confirmee"
        CANCELLED = "cancelled", "Annulee"

    requester_name = models.CharField(max_length=140)
    requester_phone = models.CharField(max_length=40)
    requester_email = models.EmailField(blank=True)
    event_type = models.CharField(max_length=80)
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    guest_count = models.PositiveIntegerField(default=0)
    setup = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["event_date", "start_time"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["-created_at"])]

    def __str__(self) -> str:
        return f"{self.event_type} - {self.event_date}"


class PaymentProvider(TimestampedModel):
    class ProviderType(models.TextChoices):
        MANUAL = "manual", "Paiement manuel"
        MONCASH = "moncash", "MonCash"
        NATCASH = "natcash", "NatCash"
        BANK = "bank", "Virement bancaire"
        CASH = "cash", "Cash"
        STRIPE = "stripe", "Stripe"
        PAYPAL = "paypal", "PayPal"
        OTHER = "other", "Autre"

    class Mode(models.TextChoices):
        MANUAL = "manual", "Manuel (le client paie puis on confirme)"
        API = "api", "API (paiement en ligne automatisé)"

    name = models.CharField(max_length=120)
    provider_type = models.CharField(max_length=30, choices=ProviderType.choices, default=ProviderType.MANUAL)
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.MANUAL)
    is_active = models.BooleanField(default=True)
    logo = models.FileField(upload_to="payment_logos/", blank=True)
    instructions = models.TextField(
        blank=True,
        help_text="Texte montre au client: numero MonCash, compte bancaire, consignes, etc.",
    )
    # Coordonnées de paiement (mobile money / banque locale) pour les moyens manuels
    account_name = models.CharField(max_length=120, blank=True)
    account_number = models.CharField(max_length=80, blank=True)
    checkout_url = models.URLField(
        blank=True,
        help_text="Lien de paiement externe optionnel. Laisse vide pour un paiement manuel.",
    )
    api_public_key = models.CharField(max_length=255, blank=True)
    api_secret_key = EncryptedCharField(max_length=512, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class Payment(TimestampedModel):
    class Purpose(models.TextChoices):
        VENUE = "venue", "Reservation de salle"
        COURSE = "course", "Inscription cours"
        MEMBERSHIP = "membership", "Adhesion"
        PRODUCT = "product", "Commande boutique"
        OTHER = "other", "Autre"

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        PAID = "paid", "Paye"
        FAILED = "failed", "Echoue"
        CANCELLED = "cancelled", "Annule"
        REFUNDED = "refunded", "Rembourse"

    class EntryMode(models.TextChoices):
        MANUAL = "manual", "Saisie manuelle"
        API = "api", "API"
        CLIENT = "client", "Client"

    reference = models.CharField(max_length=40, unique=True, blank=True)
    purpose = models.CharField(max_length=30, choices=Purpose.choices)
    provider = models.ForeignKey(PaymentProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    entry_mode = models.CharField(max_length=20, choices=EntryMode.choices, default=EntryMode.CLIENT)
    payer_name = models.CharField(max_length=140)
    payer_phone = models.CharField(max_length=40, blank=True)
    payer_email = models.EmailField(blank=True)
    amount_htg = models.PositiveIntegerField(default=0)
    external_reference = models.CharField(max_length=120, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    venue_booking = models.ForeignKey(VenueBooking, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    enrollment = models.ForeignKey(Enrollment, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    order = models.ForeignKey("Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    # Bucket PRIVÉ : capture de paiement (PII/preuve), servie via URL signée temporaire.
    screenshot = models.FileField(
        upload_to="screenshots/", blank=True, storage=private_media_storage
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["purpose"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.reference} - {self.get_status_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.reference:
            stamp = timezone.now().strftime("%Y%m%d%H%M%S")
            prefix = self.purpose.upper()[:3]
            # Suffixe aleatoire : sans lui, deux paiements du meme type crees dans
            # la meme seconde violent la contrainte unique -> IntegrityError/500
            # (frequent en serverless ou plusieurs lambdas repondent en parallele).
            self.reference = f"IMSO-{prefix}-{stamp}-{secrets.token_hex(3)}"
        if self.status == self.Status.PAID and not self.paid_at:
            self.paid_at = timezone.now()
        super().save(*args, **kwargs)


class ContactRequest(TimestampedModel):
    class Subject(models.TextChoices):
        MEMBERSHIP = "membership", "Adhesion a un GEI"
        COURSE = "course", "Inscription a un cours"
        VENUE = "venue", "Location de salle"
        MENTOR = "mentor", "Devenir mentor"
        OTHER = "other", "Autre"

    full_name = models.CharField(max_length=140)
    phone = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
    subject = models.CharField(max_length=30, choices=Subject.choices, default=Subject.MEMBERSHIP)
    message = models.TextField(blank=True)
    is_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name} - {self.get_subject_display()}"


class DashboardMetric(TimestampedModel):
    label = models.CharField(max_length=120)
    value = models.CharField(max_length=40)
    helper = models.CharField(max_length=160, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "label"]

    def __str__(self) -> str:
        return self.label


class Testimonial(TimestampedModel):
    author_name = models.CharField(max_length=140)
    author_initials = models.CharField(max_length=6, blank=True, help_text="Ex: MJ, JV")
    location = models.CharField(max_length=140, blank=True, help_text="Ex: GEI Pétion-Ville · 2 ans")
    text = models.TextField()
    photo = models.FileField(upload_to="testimonials/", blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.author_initials and self.author_name:
            parts = self.author_name.strip().split()
            self.author_initials = "".join(p[0].upper() for p in parts if p)[:4]
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.author_name} - {self.location}"


class CoreValue(TimestampedModel):
    """Valeur affichee dans la section « Nos valeurs » du site vitrine.

    Modele simple/CRUD : si aucune ligne active n'existe, le template garde son
    contenu code en dur (fallback via {% empty %}).
    """

    title = models.CharField(max_length=120)
    text = models.TextField()
    icon = models.CharField(
        max_length=8, blank=True,
        help_text="Emoji affiche (ex. \U0001F91D, \U0001F331). Laisse vide pour une icone par defaut.",
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.title


class ProcessStep(TimestampedModel):
    """Etape affichee dans la section « Notre processus » du site vitrine.

    Le numero d'etape (1, 2, 3) est genere par le template (forloop.counter),
    on ne le stocke pas. Fallback via {% empty %} si aucune ligne active.
    """

    title = models.CharField(max_length=120)
    text = models.TextField()
    meta = models.CharField(
        max_length=80, blank=True,
        help_text="Duree / info courte (ex. « ⏱ 1 semaine »).",
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.title


class SiteText(TimestampedModel):
    """Registre de textes editables du site vitrine (titres, intitules, intros...).

    Chaque chaine editable a une cle stable (ex. « hero_label »). Le template
    affiche {{ texts.<cle>|default:"texte actuel" }} : si l'admin renseigne une
    valeur, elle remplace le texte code en dur ; sinon le defaut du template est
    utilise (aucun changement visuel tant que vide). Charge en UNE requete par
    page via le context processor -> pas de N+1.
    """

    key = models.CharField(max_length=80, unique=True)
    label = models.CharField(max_length=200, help_text="Description lisible pour l'admin")
    group = models.CharField(max_length=60, blank=True, help_text="Section/page (regroupement dans l'admin)")
    value = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["group", "sort_order", "key"]

    def __str__(self) -> str:
        return f"{self.group} · {self.key}" if self.group else self.key


class SiteImage(TimestampedModel):
    """Registre d'images editables du site vitrine (photos hero, galerie...).

    Meme principe que SiteText mais pour les images : chaque image a une cle
    stable (ex. « hero_photo_1 »). Le template affiche l'image televersee si
    elle existe, sinon garde l'image codee en dur (fallback). Chargees en UNE
    requete par page via le context processor (dict {cle: objet}).
    """

    key = models.CharField(max_length=80, unique=True)
    label = models.CharField(max_length=200, help_text="Description lisible pour l'admin")
    group = models.CharField(max_length=60, blank=True, help_text="Section/page (regroupement dans l'admin)")
    # Stockage public par defaut (comme Product.image), servi via URL directe.
    image = models.FileField(upload_to="site/images/", blank=True)
    alt = models.CharField(max_length=200, blank=True, help_text="Texte alternatif (accessibilite/SEO)")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["group", "sort_order", "key"]

    def __str__(self) -> str:
        return f"{self.group} · {self.key}" if self.group else self.key


class Product(TimestampedModel):
    """Article vendu en boutique (kit d'éducation financière : livre, cahier…)."""

    class Kind(models.TextChoices):
        BOOK = "book", "Livre"
        WORKBOOK = "workbook", "Cahier"
        KIT = "kit", "Kit complet"
        OTHER = "other", "Autre"

    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.KIT)
    description = models.TextField(blank=True)
    price_htg = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)
    image = models.FileField(upload_to="products/", blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug and self.name:
            base = slugify(self.name)[:190] or "produit"
            slug = base
            i = 2
            while Product.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    def __str__(self) -> str:
        return self.name


class Order(TimestampedModel):
    """Commande boutique. Le paiement (manuel) est géré via le modèle Payment."""

    class Status(models.TextChoices):
        PENDING = "pending", "En attente de paiement"
        PAID = "paid", "Payée"
        PREPARING = "preparing", "En préparation"
        SHIPPED = "shipped", "Expédiée"
        DELIVERED = "delivered", "Livrée"
        CANCELLED = "cancelled", "Annulée"

    reference = models.CharField(max_length=40, unique=True, blank=True)
    customer_name = models.CharField(max_length=140)
    customer_phone = models.CharField(max_length=40)
    customer_email = models.EmailField(blank=True)
    delivery_address = models.TextField()
    city = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_htg = models.PositiveIntegerField(default=0)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["-created_at"])]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.reference:
            stamp = timezone.now().strftime("%Y%m%d%H%M%S")
            # Suffixe aleatoire : evite la collision de reference (unique) quand
            # deux commandes tombent dans la meme seconde -> IntegrityError/500.
            self.reference = f"IMSO-CMD-{stamp}-{secrets.token_hex(3)}"
        super().save(*args, **kwargs)

    def recompute_total(self) -> int:
        total = sum(item.line_total for item in self.items.all())
        self.total_htg = total
        return total

    def __str__(self) -> str:
        return f"{self.reference} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items")
    product_name = models.CharField(max_length=180)  # figé au moment de la commande
    quantity = models.PositiveIntegerField(default=1)
    unit_price_htg = models.PositiveIntegerField(default=0)  # figé au moment de la commande

    def __str__(self) -> str:
        return f"{self.quantity} × {self.product_name}"

    @property
    def line_total(self) -> int:
        return self.quantity * self.unit_price_htg


class SiteSetting(models.Model):
    """Paramètres globaux du site (singleton, pk=1). Édités depuis le dashboard."""

    # ── Identité ──
    site_name = models.CharField(max_length=120, default="IMSO")
    tagline = models.CharField(max_length=200, blank=True, default="Impact Mutuelle de Solidarité")
    logo = models.FileField(upload_to="site/", blank=True)

    # ── Contact ──
    contact_phone = models.CharField(max_length=60, blank=True)
    contact_whatsapp = models.CharField(max_length=60, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_address = models.CharField(max_length=255, blank=True)

    # ── Réseaux sociaux ──
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)

    # ── Couleurs (thème) ──
    color_primary = models.CharField(max_length=9, blank=True, default="#3C9626", help_text="Couleur principale (hex)")
    color_primary_dark = models.CharField(max_length=9, blank=True, default="#2A6E1B")
    color_accent = models.CharField(max_length=9, blank=True, default="#5BB143")
    color_highlight = models.CharField(max_length=9, blank=True, default="#E87A18")

    # ── Textes éditables (page d'accueil) ──
    hero_title = models.CharField(max_length=200, blank=True)
    hero_subtitle = models.TextField(blank=True)
    hero_cta_text = models.CharField(max_length=60, blank=True, default="Adhérer")
    about_title = models.CharField(max_length=200, blank=True)
    about_text = models.TextField(blank=True)
    shop_intro = models.TextField(blank=True, help_text="Texte d'intro de la boutique")
    footer_text = models.TextField(blank=True)

    # ── Statistiques marketing (vitrine) — vide = valeur d'origine du template ──
    # Héro (float-cards)
    stat_members = models.CharField(max_length=40, blank=True, help_text="Ex: 248 membres")
    stat_members_label = models.CharField(max_length=80, blank=True, help_text="Ex: Actifs en avril 2026")
    stat_growth = models.CharField(max_length=40, blank=True, help_text="Ex: +38%")
    stat_growth_label = models.CharField(max_length=80, blank=True, help_text="Ex: Épargne collective")
    # Section Mission (tuiles)
    stat_savings = models.CharField(max_length=40, blank=True, help_text="Ex: 3.2M")
    stat_savings_label = models.CharField(max_length=80, blank=True, help_text="Ex: HTG d'épargne mobilisée")
    stat_repayment = models.CharField(max_length=40, blank=True, help_text="Ex: 96%")
    stat_repayment_label = models.CharField(max_length=80, blank=True, help_text="Ex: Taux de remboursement")
    stat_workshops = models.CharField(max_length=40, blank=True, help_text="Ex: 52")
    stat_workshops_label = models.CharField(max_length=80, blank=True, help_text="Ex: Ateliers tenus en 2025")
    stat_women = models.CharField(max_length=40, blank=True, help_text="Ex: 61%")
    stat_women_label = models.CharField(max_length=80, blank=True, help_text="Ex: Membres femmes")

    # ── Hero formation (catalogue /formation/) ──
    formation_hero_title = models.CharField(max_length=200, blank=True)
    formation_hero_subtitle = models.TextField(blank=True)

    # ── Liens footer (ressources / légaux) — vide = #contact ──
    url_statuts = models.CharField(max_length=200, blank=True)
    url_calendrier = models.CharField(max_length=200, blank=True)
    url_rapport = models.CharField(max_length=200, blank=True)
    url_mentor = models.CharField(max_length=200, blank=True)
    url_presse = models.CharField(max_length=200, blank=True)
    url_mentions = models.CharField(max_length=200, blank=True)
    url_confidentialite = models.CharField(max_length=200, blank=True)

    # ── Affichage (toggles) ──
    show_shop = models.BooleanField(default=True)
    show_blog = models.BooleanField(default=True)
    show_courses = models.BooleanField(default=True)
    show_testimonials = models.BooleanField(default=True)
    maintenance_mode = models.BooleanField(default=False, help_text="Affiche un bandeau maintenance")

    # ── SEO ──
    meta_description = models.CharField(max_length=300, blank=True)
    meta_keywords = models.CharField(max_length=300, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paramètres du site"
        verbose_name_plural = "Paramètres du site"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.pk = 1  # singleton
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SiteSetting":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self) -> str:
        return "Paramètres du site"


class BlogPost(TimestampedModel):
    """Article de blog. Publication immédiate, brouillon ou programmée."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Brouillon"
        PUBLISHED = "published", "Publié"
        SCHEDULED = "scheduled", "Programmé"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    excerpt = models.CharField(max_length=300, blank=True)
    body = models.TextField()
    cover_image = models.FileField(upload_to="blog/", blank=True)
    author = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug and self.title:
            base = slugify(self.title)[:210] or "article"
            slug = base
            i = 2
            while BlogPost.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_public(self) -> bool:
        return (
            self.status == self.Status.PUBLISHED
            and self.published_at is not None
            and self.published_at <= timezone.now()
        )

    def __str__(self) -> str:
        return self.title


class AdminNotification(models.Model):
    class NotificationType(models.TextChoices):
        NEW_BOOKING = "new_booking", "Nouvelle réservation"
        NEW_PAYMENT = "new_payment", "Nouveau paiement"
        NEW_CONTACT = "new_contact", "Nouveau message"
        NEW_ENROLLMENT = "new_enrollment", "Nouvelle inscription"
        PAYMENT_RECEIVED = "payment_received", "Paiement reçu"
        BOOKING_CONFIRMED = "booking_confirmed", "Réservation confirmée"
        BOOKING_CANCELLED = "booking_cancelled", "Réservation annulée"

    message = models.CharField(max_length=255)
    notification_type = models.CharField(
        max_length=30, choices=NotificationType.choices
    )
    related_id = models.PositiveIntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.get_notification_type_display()}] {self.message}"


class AuditLog(models.Model):
    """Trace persistante des actions du personnel (qui, quoi, quand).

    Indispensable dès qu'on manipule de l'argent : permet de savoir qui a validé
    un paiement, modifié un montant ou supprimé un enregistrement.
    """

    class Action(models.TextChoices):
        CREATE = "create", "Création"
        UPDATE = "update", "Modification"
        DELETE = "delete", "Suppression"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    username = models.CharField(max_length=150, blank=True)  # figé même si le compte est supprimé
    action = models.CharField(max_length=20, choices=Action.choices)
    model_name = models.CharField(max_length=80)
    object_id = models.CharField(max_length=40, blank=True)
    object_label = models.CharField(max_length=200, blank=True)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.created_at:%Y-%m-%d %H:%M} · {self.username} · {self.action} {self.model_name}#{self.object_id}"
