from django.urls import path

from .views import (
    ContactRequestCreateView,
    CourseEnrollmentCreateView,
    HomeView,
    PaymentConfirmationView,
    PaymentPageView,
    PaymentProcessView,
    VenueBookingCreateView,
    get_active_courses,
    get_active_providers,
    healthcheck,
)


app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("api/contact-requests/", ContactRequestCreateView.as_view(), name="contact_request_create"),
    path("api/venue-bookings/", VenueBookingCreateView.as_view(), name="venue_booking_create"),
    path("api/course-enrollments/", CourseEnrollmentCreateView.as_view(), name="course_enrollment_create"),
    path("api/providers/", get_active_providers, name="active_providers"),
    path("api/courses/", get_active_courses, name="active_courses"),
    path("api/paiement/<str:type>/<int:id>/", PaymentProcessView.as_view(), name="payment_process"),
    path("api/paiement/confirmation/<str:reference>/", PaymentConfirmationView.as_view(), name="payment_confirmation"),
    path("paiement/<str:type>/<int:id>/", PaymentPageView.as_view(), name="payment_page"),
    path("health/", healthcheck, name="healthcheck"),
]
