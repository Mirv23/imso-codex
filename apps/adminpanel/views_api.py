from datetime import timedelta

from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
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
from .serializers import (
    AdminNotificationSerializer,
    ContactRequestSerializer,
    CourseSerializer,
    EnrollmentSerializer,
    GEISerializer,
    MemberSerializer,
    PaymentSerializer,
    PaymentProviderSerializer,
    TestimonialSerializer,
    VenueBookingSerializer,
)


class GEIViewSet(viewsets.ModelViewSet):
    queryset = GEI.objects.annotate(member_count=Count("members")).all()
    serializer_class = GEISerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "city", "coordinator"]
    ordering_fields = ["name", "city", "created_at"]
    ordering = ["city", "name"]


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.select_related("gei").all()
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["first_name", "last_name", "email", "phone"]
    ordering_fields = ["last_name", "first_name", "created_at", "monthly_saving_htg"]
    ordering = ["-created_at"]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.annotate(enrollment_count=Count("enrollments")).all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "instructor", "category", "city"]
    ordering_fields = ["title", "category", "price_htg", "created_at"]
    ordering = ["-created_at"]


class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.select_related("member", "course").all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["member__first_name", "member__last_name", "course__title"]
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]


class VenueBookingViewSet(viewsets.ModelViewSet):
    queryset = VenueBooking.objects.prefetch_related("payments").all()
    serializer_class = VenueBookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["requester_name", "requester_phone", "requester_email", "event_type"]
    ordering_fields = ["event_date", "start_time", "created_at"]
    ordering = ["-created_at"]


class PaymentProviderViewSet(viewsets.ModelViewSet):
    queryset = PaymentProvider.objects.all()
    serializer_class = PaymentProviderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "provider_type"]
    ordering_fields = ["sort_order", "name"]
    ordering = ["sort_order", "name"]


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("provider").all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["reference", "payer_name", "payer_phone", "payer_email", "external_reference"]
    ordering_fields = ["created_at", "amount_htg", "paid_at"]
    ordering = ["-created_at"]


class ContactRequestViewSet(viewsets.ModelViewSet):
    queryset = ContactRequest.objects.all()
    serializer_class = ContactRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["full_name", "phone", "email", "message"]
    ordering_fields = ["created_at", "subject"]
    ordering = ["-created_at"]


class AdminNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AdminNotification.objects.all()
    serializer_class = AdminNotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ["-is_read", "-created_at"]

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"ok": True}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        AdminNotification.objects.filter(is_read=False).update(is_read=True)
        return Response({"ok": True}, status=status.HTTP_200_OK)


class TestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["author_name", "location", "text"]
    ordering_fields = ["sort_order", "created_at", "author_name"]
    ordering = ["sort_order", "-created_at"]


class DashboardSummaryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def summary(self, request):
        savings = Member.objects.aggregate(total=Sum("monthly_saving_htg"))["total"] or 0
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_bookings = VenueBooking.objects.filter(created_at__gte=seven_days_ago).count()
        recent_payments_qs = Payment.objects.filter(created_at__gte=seven_days_ago)
        recent_payments_count = recent_payments_qs.count()
        recent_payments_sum = recent_payments_qs.aggregate(total=Sum("amount_htg"))["total"] or 0
        data = {
            "active_members": Member.objects.filter(status=Member.Status.ACTIVE).count(),
            "active_gei": GEI.objects.filter(is_active=True).count(),
            "active_courses": Course.objects.filter(is_active=True).count(),
            "pending_contacts": ContactRequest.objects.filter(is_processed=False).count(),
            "pending_bookings": VenueBooking.objects.filter(status=VenueBooking.Status.REQUESTED).count(),
            "savings_htg": savings,
            "total_members": Member.objects.count(),
            "total_courses": Course.objects.count(),
            "total_revenue_htg": Payment.objects.filter(status=Payment.Status.PAID).aggregate(
                total=Sum("amount_htg")
            )["total"] or 0,
            "pending_enrollments": Enrollment.objects.filter(status=Enrollment.Status.PENDING).count(),
            "recent_bookings": recent_bookings,
            "recent_payments_count": recent_payments_count,
            "recent_payments_sum": recent_payments_sum,
        }
        return Response(data)
