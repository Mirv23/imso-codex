"""Enregistrement des modèles dans l'admin Django natif.

Fournit une interface de secours (`/django-admin/`) en complément du dashboard
custom, et un accès en lecture seule au journal d'audit.
"""

from django.contrib import admin

from .models import (
    AdminNotification,
    AuditLog,
    BlogPost,
    Chapter,
    ChapterCompletion,
    ContactRequest,
    Course,
    CourseEnrollment,
    Enrollment,
    GEI,
    Member,
    Order,
    OrderItem,
    Payment,
    PaymentProvider,
    Product,
    Profile,
    SiteSetting,
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


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "price_htg", "stock", "is_active", "sort_order")
    list_filter = ("kind", "is_active")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "unit_price_htg")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "customer_name", "city", "total_htg", "status", "created_at")
    list_filter = ("status", "city")
    search_fields = ("reference", "customer_name", "customer_phone", "customer_email")
    readonly_fields = ("reference", "total_htg")
    inlines = [OrderItemInline]


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ("site_name", "contact_email", "updated_at")

    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "author", "published_at", "scheduled_for")
    list_filter = ("status",)
    search_fields = ("title", "body", "author")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ("notification_type", "message", "is_read", "created_at")
    list_filter = ("notification_type", "is_read")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "is_approved", "kyc_status", "phone")
    list_filter = ("role", "is_approved", "kyc_status")
    search_fields = ("user__username", "user__email", "phone")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("student__username", "course__title")


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "position", "duration_minutes", "video")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ChapterCompletion)
class ChapterCompletionAdmin(admin.ModelAdmin):
    list_display = ("student", "chapter", "created_at")
    search_fields = ("student__username", "chapter__title")
    readonly_fields = ("created_at",)


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
