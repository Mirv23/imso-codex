from __future__ import annotations

import base64
import os

from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone


def _obfuscation_key() -> bytes:
    key = os.environ.get("DJANGO_SECRET_KEY", "")
    return key.encode("utf-8") if key else b"imso-fallback-key-32chars!!"


def _xor_encrypt(plaintext: str) -> str:
    key = _obfuscation_key()
    plain_bytes = plaintext.encode("utf-8")
    result = bytes(plain_bytes[i] ^ key[i % len(key)] for i in range(len(plain_bytes)))
    return base64.urlsafe_b64encode(result).decode("ascii")


def _xor_decrypt(ciphertext: str) -> str:
    key = _obfuscation_key()
    raw = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
    result = bytes(raw[i] ^ key[i % len(key)] for i in range(len(raw)))
    return result.decode("utf-8")


class EncryptedCharField(models.CharField):
    def from_db_value(self, value: str | None, expression: Any, connection: Any) -> str | None:
        if value is None:
            return value
        # Cohérent avec get_prep_value qui préfixe "enc:". Sans ce strip, le
        # base64 échoue (Incorrect padding). On tolère aussi les valeurs
        # héritées non chiffrées (sans préfixe).
        if value.startswith("enc:"):
            return _xor_decrypt(value[4:])
        return value

    def to_python(self, value: Any) -> Any:
        if isinstance(value, str) and value.startswith("enc:"):
            return _xor_decrypt(value[4:])
        return value

    def get_prep_value(self, value: Any) -> str | None:
        if value is None:
            return None
        return "enc:" + _xor_encrypt(value)


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

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Course(TimestampedModel):
    title = models.CharField(max_length=180)
    category = models.CharField(max_length=80)
    instructor = models.CharField(max_length=120)
    city = models.CharField(max_length=120)
    price_htg = models.PositiveIntegerField(default=0)
    capacity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    public_slug = models.SlugField(max_length=200, blank=True, unique=True, null=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["category", "title"]

    def __str__(self) -> str:
        return self.title


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
        OTHER = "other", "Autre"

    name = models.CharField(max_length=120)
    provider_type = models.CharField(max_length=30, choices=ProviderType.choices, default=ProviderType.MANUAL)
    is_active = models.BooleanField(default=True)
    instructions = models.TextField(
        blank=True,
        help_text="Texte montre au client: numero MonCash, compte bancaire, consignes, etc.",
    )
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
    screenshot = models.FileField(upload_to="screenshots/", blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.reference} - {self.get_status_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.reference:
            stamp = timezone.now().strftime("%Y%m%d%H%M%S")
            prefix = self.purpose.upper()[:3]
            self.reference = f"IMSO-{prefix}-{stamp}"
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
