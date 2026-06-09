from rest_framework import serializers

from .models import (
    AdminNotification,
    ContactRequest,
    Course,
    Enrollment,
    GEI,
    Member,
    Payment,
    PaymentProvider,
    VenueBooking,
)


class GEISerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = GEI
        fields = ["id", "name", "city", "coordinator", "is_active", "member_count", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_member_count(self, obj):
        return obj.members.count()


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class CourseSerializer(serializers.ModelSerializer):
    enrollment_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["id", "title", "category", "instructor", "city", "price_htg",
                  "capacity", "is_active", "public_slug", "description",
                  "enrollment_count", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_enrollment_count(self, obj):
        return obj.enrollments.count()


class MemberNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ["id", "first_name", "last_name", "email"]


class CourseNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "title", "category"]


class EnrollmentSerializer(serializers.ModelSerializer):
    member = MemberNestedSerializer(read_only=True)
    course = CourseNestedSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "member", "course", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class VenueBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = VenueBooking
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PaymentProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentProvider
        exclude = ["api_secret_key"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PaymentSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.name", read_only=True, allow_null=True)

    class Meta:
        model = Payment
        fields = ["id", "reference", "purpose", "provider", "provider_name", "status",
                  "entry_mode", "payer_name", "payer_phone", "payer_email", "amount_htg",
                  "external_reference", "paid_at", "notes", "venue_booking", "enrollment",
                  "screenshot", "created_at", "updated_at"]
        read_only_fields = ["id", "reference", "created_at", "updated_at"]


class ContactRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactRequest
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class AdminNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminNotification
        fields = "__all__"
        read_only_fields = ["id", "created_at"]
