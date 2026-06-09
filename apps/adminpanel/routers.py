from rest_framework.routers import DefaultRouter

from .views_api import (
    AdminNotificationViewSet,
    ContactRequestViewSet,
    CourseViewSet,
    DashboardSummaryViewSet,
    EnrollmentViewSet,
    GEIViewSet,
    MemberViewSet,
    PaymentViewSet,
    PaymentProviderViewSet,
    VenueBookingViewSet,
)

router = DefaultRouter()
router.register(r"geis", GEIViewSet, basename="v2-gei")
router.register(r"members", MemberViewSet, basename="v2-member")
router.register(r"courses", CourseViewSet, basename="v2-course")
router.register(r"enrollments", EnrollmentViewSet, basename="v2-enrollment")
router.register(r"bookings", VenueBookingViewSet, basename="v2-booking")
router.register(r"providers", PaymentProviderViewSet, basename="v2-provider")
router.register(r"payments", PaymentViewSet, basename="v2-payment")
router.register(r"contacts", ContactRequestViewSet, basename="v2-contact")
router.register(r"notifications", AdminNotificationViewSet, basename="v2-notification")
router.register(r"dashboard", DashboardSummaryViewSet, basename="v2-dashboard")
