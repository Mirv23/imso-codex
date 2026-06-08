from django.contrib import admin
from django.utils.html import format_html

from .models import (
    ContactRequest,
    Course,
    DashboardMetric,
    Enrollment,
    GEI,
    Member,
    Payment,
    PaymentProvider,
    VenueBooking,
)


admin.site.site_header = "IMSO Administration"
admin.site.site_title = "IMSO Admin"
admin.site.index_title = "Tableau de bord"
admin.site.site_url = "/"


@admin.register(GEI)
class GEIAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "coordinator", "is_active", "member_count")
    list_filter = ("is_active", "city")
    search_fields = ("name", "city", "coordinator")
    list_editable = ("is_active",)
    actions = ["activate", "deactivate"]

    def member_count(self, obj):
        return obj.members.count()

    member_count.short_description = "Membres"

    def activate(self, request, queryset):
        queryset.update(is_active=True)

    activate.short_description = "Activer les GEI sélectionnés"

    def deactivate(self, request, queryset):
        queryset.update(is_active=False)

    deactivate.short_description = "Désactiver les GEI sélectionnés"


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "phone",
        "email_display",
        "gei",
        "status",
        "monthly_saving_htg",
        "joined_at",
    )
    list_filter = ("status", "gei", "joined_at")
    search_fields = ("first_name", "last_name", "phone", "email")
    list_editable = ("status",)
    date_hierarchy = "joined_at"
    actions = ["mark_active", "mark_alumni"]

    def email_display(self, obj):
        return obj.email or "—"

    email_display.short_description = "Email"

    def status_colored(self, obj):
        colors = {
            "prospect": "amber",
            "active": "green",
            "paused": "blue",
            "alumni": "gray",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span class="pill pill-{}">{}</span>', color, obj.get_status_display()
        )

    status_colored.short_description = "Statut"

    def mark_active(self, request, queryset):
        queryset.update(status=Member.Status.ACTIVE)

    mark_active.short_description = "Marquer comme Actif"

    def mark_alumni(self, request, queryset):
        queryset.update(status=Member.Status.ALUMNI)

    mark_alumni.short_description = "Marquer comme Ancien membre"


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "city",
        "instructor",
        "price_htg",
        "enrolled_count",
        "capacity",
        "is_active",
    )
    list_filter = ("category", "city", "is_active")
    search_fields = ("title", "instructor", "city", "description")
    list_editable = ("is_active",)
    prepopulated_fields = {"public_slug": ("title",)}
    actions = ["activate", "deactivate"]

    def enrolled_count(self, obj):
        return obj.enrollments.count()

    enrolled_count.short_description = "Inscrits"

    def is_active_colored(self, obj):
        if obj.is_active:
            return format_html('<span class="pill pill-green">Actif</span>')
        return format_html('<span class="pill pill-gray">Inactif</span>')

    is_active_colored.short_description = "Statut"

    def activate(self, request, queryset):
        queryset.update(is_active=True)

    activate.short_description = "Activer les cours sélectionnés"

    def deactivate(self, request, queryset):
        queryset.update(is_active=False)

    deactivate.short_description = "Désactiver les cours sélectionnés"


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("member", "course", "status_colored", "created_at")
    list_filter = ("status", "course", "created_at")
    search_fields = ("member__first_name", "member__last_name", "course__title")
    date_hierarchy = "created_at"
    actions = ["confirm", "cancel"]

    def status_colored(self, obj):
        colors = {
            "pending": "amber",
            "confirmed": "green",
            "cancelled": "red",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span class="pill pill-{}">{}</span>', color, obj.get_status_display()
        )

    status_colored.short_description = "Statut"

    def confirm(self, request, queryset):
        queryset.update(status=Enrollment.Status.CONFIRMED)

    confirm.short_description = "Confirmer les inscriptions sélectionnées"

    def cancel(self, request, queryset):
        queryset.update(status=Enrollment.Status.CANCELLED)

    cancel.short_description = "Annuler les inscriptions sélectionnées"


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("reference", "amount_htg", "status", "entry_mode", "paid_at")
    readonly_fields = ("reference", "created_at")
    can_delete = False
    show_change_link = True


@admin.register(VenueBooking)
class VenueBookingAdmin(admin.ModelAdmin):
    list_display = (
        "event_date",
        "start_time",
        "end_time",
        "requester_name",
        "event_type",
        "status_colored",
        "payment_status",
    )
    list_filter = ("status", "event_type", "event_date")
    search_fields = ("requester_name", "requester_phone", "event_type", "requester_email")
    date_hierarchy = "event_date"
    actions = ["mark_payment_pending", "confirm_booking", "cancel_booking"]
    inlines = [PaymentInline]

    def status_colored(self, obj):
        colors = {
            "requested": "amber",
            "payment_pending": "blue",
            "admin_review": "violet",
            "confirmed": "green",
            "cancelled": "red",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span class="pill pill-{}">{}</span>', color, obj.get_status_display()
        )

    status_colored.short_description = "Statut"

    def payment_status(self, obj):
        payments = obj.payments.all()
        if not payments:
            return format_html('<span class="pill pill-gray">Aucun</span>')
        paid = payments.filter(status=Payment.Status.PAID).count()
        total = payments.count()
        if paid == total and paid > 0:
            return format_html('<span class="pill pill-green">{}/{} payé</span>', paid, total)
        elif paid > 0:
            return format_html('<span class="pill pill-amber">{}/{} payé</span>', paid, total)
        return format_html('<span class="pill pill-gray">{}/{} payé</span>', paid, total)

    payment_status.short_description = "Paiement"

    def mark_payment_pending(self, request, queryset):
        queryset.update(status=VenueBooking.Status.PAYMENT_PENDING)

    mark_payment_pending.short_description = "Marquer 'Paiement attendu'"

    def confirm_booking(self, request, queryset):
        queryset.update(status=VenueBooking.Status.CONFIRMED)

    confirm_booking.short_description = "Confirmer les réservations"

    def cancel_booking(self, request, queryset):
        queryset.update(status=VenueBooking.Status.CANCELLED)

    cancel_booking.short_description = "Annuler les réservations"


@admin.register(PaymentProvider)
class PaymentProviderAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "provider_type_colored",
        "is_active",
        "sort_order",
        "payment_count",
    )
    list_filter = ("provider_type", "is_active")
    list_editable = ("sort_order", "is_active")
    search_fields = ("name", "instructions")
    fieldsets = (
        (
            "Informations générales",
            {
                "fields": (
                    "name",
                    "provider_type",
                    "is_active",
                    "sort_order",
                    "instructions",
                )
            },
        ),
        (
            "Paiement en ligne (API)",
            {
                "classes": ("collapse",),
                "fields": (
                    "checkout_url",
                    "api_public_key",
                    "api_secret_key",
                ),
                "description": "Configurez les clés API pour le paiement automatique. "
                "Laissez vide pour un paiement manuel.",
            },
        ),
    )

    def provider_type_colored(self, obj):
        colors = {
            "manual": "gray",
            "moncash": "green",
            "natcash": "blue",
            "bank": "violet",
            "cash": "amber",
            "stripe": "violet",
            "other": "gray",
        }
        color = colors.get(obj.provider_type, "gray")
        return format_html(
            '<span class="pill pill-{}">{}</span>', color, obj.get_provider_type_display()
        )

    provider_type_colored.short_description = "Type"

    def is_active_colored(self, obj):
        if obj.is_active:
            return format_html('<span class="pill pill-green">Actif</span>')
        return format_html('<span class="pill pill-gray">Inactif</span>')

    is_active_colored.short_description = "Statut"

    def payment_count(self, obj):
        return obj.payments.count()

    payment_count.short_description = "Paiements"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "purpose_colored",
        "payer_name",
        "amount_htg",
        "provider",
        "status_colored",
        "entry_mode",
        "paid_at",
    )
    list_filter = ("status", "purpose", "entry_mode", "provider", "created_at")
    search_fields = (
        "reference",
        "payer_name",
        "payer_phone",
        "payer_email",
        "external_reference",
    )
    date_hierarchy = "created_at"
    readonly_fields = ("reference", "created_at", "updated_at")
    actions = ["mark_paid", "mark_failed", "mark_refunded"]
    fieldsets = (
        (
            "Référence",
            {
                "fields": (
                    "reference",
                    "purpose",
                    "entry_mode",
                    "status",
                )
            },
        ),
        (
            "Payeur",
            {
                "fields": (
                    "payer_name",
                    "payer_phone",
                    "payer_email",
                )
            },
        ),
        (
            "Paiement",
            {
                "fields": (
                    "provider",
                    "amount_htg",
                    "external_reference",
                    "paid_at",
                    "notes",
                )
            },
        ),
        (
            "Liens",
            {
                "classes": ("collapse",),
                "fields": (
                    "venue_booking",
                    "enrollment",
                ),
            },
        ),
        (
            "Horodatage",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    def purpose_colored(self, obj):
        colors = {
            "venue": "blue",
            "course": "green",
            "membership": "violet",
            "other": "gray",
        }
        color = colors.get(obj.purpose, "gray")
        return format_html(
            '<span class="pill pill-{}">{}</span>', color, obj.get_purpose_display()
        )

    purpose_colored.short_description = "Motif"

    def status_colored(self, obj):
        colors = {
            "pending": "amber",
            "paid": "green",
            "failed": "red",
            "cancelled": "gray",
            "refunded": "violet",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span class="pill pill-{}">{}</span>', color, obj.get_status_display()
        )

    status_colored.short_description = "Statut"

    def mark_paid(self, request, queryset):
        from django.utils import timezone

        for payment in queryset:
            payment.status = Payment.Status.PAID
            payment.paid_at = timezone.now()
            payment.save()

    mark_paid.short_description = "Marquer comme payé"

    def mark_failed(self, request, queryset):
        queryset.update(status=Payment.Status.FAILED)

    mark_failed.short_description = "Marquer comme échoué"

    def mark_refunded(self, request, queryset):
        queryset.update(status=Payment.Status.REFUNDED)

    mark_refunded.short_description = "Marquer comme remboursé"


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "phone",
        "subject_colored",
        "is_processed_colored",
        "created_at",
    )
    list_filter = ("subject", "is_processed", "created_at")
    search_fields = ("full_name", "phone", "email", "message")
    date_hierarchy = "created_at"
    actions = ["mark_processed", "mark_unprocessed"]

    def subject_colored(self, obj):
        colors = {
            "membership": "green",
            "course": "blue",
            "venue": "amber",
            "mentor": "violet",
            "other": "gray",
        }
        color = colors.get(obj.subject, "gray")
        return format_html(
            '<span class="pill pill-{}">{}</span>', color, obj.get_subject_display()
        )

    subject_colored.short_description = "Sujet"

    def is_processed_colored(self, obj):
        if obj.is_processed:
            return format_html('<span class="pill pill-green">Traité</span>')
        return format_html('<span class="pill pill-amber">En attente</span>')

    is_processed_colored.short_description = "Statut"

    def mark_processed(self, request, queryset):
        queryset.update(is_processed=True)

    mark_processed.short_description = "Marquer comme traité"

    def mark_unprocessed(self, request, queryset):
        queryset.update(is_processed=False)

    mark_unprocessed.short_description = "Marquer comme non traité"


@admin.register(DashboardMetric)
class DashboardMetricAdmin(admin.ModelAdmin):
    list_display = ("label", "value", "helper", "sort_order")
    list_editable = ("sort_order",)
