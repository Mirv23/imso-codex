"""Enregistrement des modèles dans l'admin Django natif.

Fournit une interface de secours (`/django-admin/`) en complément du dashboard
custom, et un accès en lecture seule au journal d'audit.
"""

from django.contrib import admin

from .models import (
    AdminNotification,
    AuditLog,
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


@admin.register(GEI)
class GEIAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "coordinator", "is_active")
    list_filter = ("is_active", "city")
    search_fields = ("name", "city", "coordinator")


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "phone", "gei", "status")
    list_filter = ("status", "gei")
    search_fields = ("first_name", "last_name", "phone", "email")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "instructor", "city", "price_htg", "is_active")
    list_filter = ("is_active", "category", "city")
    search_fields = ("title", "instructor", "category")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("member", "course", "status", "created_at")
    list_filter = ("status",)


@admin.register(VenueBooking)
class VenueBookingAdmin(admin.ModelAdmin):
    list_display = ("event_type", "requester_name", "event_date", "status")
    list_filter = ("status", "event_date")
    search_fields = ("requester_name", "requester_phone", "event_type")


@admin.register(PaymentProvider)
class PaymentProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "provider_type", "is_active", "sort_order")
    list_filter = ("provider_type", "is_active")
    # Ne jamais afficher la clé secrète dans une liste ; l'édition reste possible en détail.


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "payer_name", "purpose", "amount_htg", "status", "paid_at")
    list_filter = ("status", "purpose", "entry_mode")
    search_fields = ("reference", "payer_name", "payer_phone", "external_reference")
    readonly_fields = ("reference",)


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "subject", "phone", "is_processed", "created_at")
    list_filter = ("subject", "is_processed")
    search_fields = ("full_name", "phone", "email")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("author_name", "location", "is_active", "sort_order")
    list_filter = ("is_active",)


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ("notification_type", "message", "is_read", "created_at")
    list_filter = ("notification_type", "is_read")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "username", "action", "model_name", "object_id", "object_label")
    list_filter = ("action", "model_name")
    search_fields = ("username", "object_label", "object_id")
    readonly_fields = ("user", "username", "action", "model_name", "object_id", "object_label", "detail", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
