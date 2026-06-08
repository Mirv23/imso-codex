from django.db import models
from django.utils import timezone


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

    def __str__(self):
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

    def __str__(self):
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

    def __str__(self):
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

    def __str__(self):
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

    def __str__(self):
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
    api_secret_key = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
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

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.reference:
            stamp = timezone.now().strftime("%Y%m%d%H%M%S")
            prefix = self.purpose.upper()[:3]
            self.reference = f"IMSO-{prefix}-{stamp}"
        if self.status == self.Status.PAID and not self.paid_at:
            self.paid_at = timezone.now()
        super().save(*args, **kwargs)
        if self.status == self.Status.PAID:
            if self.venue_booking and self.venue_booking.status == VenueBooking.Status.PAYMENT_PENDING:
                self.venue_booking.status = VenueBooking.Status.ADMIN_REVIEW
                self.venue_booking.save(update_fields=["status", "updated_at"])
            if self.enrollment and self.enrollment.status == Enrollment.Status.PENDING:
                self.enrollment.status = Enrollment.Status.CONFIRMED
                self.enrollment.save(update_fields=["status", "updated_at"])


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

    def __str__(self):
        return f"{self.full_name} - {self.get_subject_display()}"


class DashboardMetric(TimestampedModel):
    label = models.CharField(max_length=120)
    value = models.CharField(max_length=40)
    helper = models.CharField(max_length=160, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "label"]

    def __str__(self):
        return self.label


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

    def __str__(self):
        return f"[{self.get_notification_type_display()}] {self.message}"
