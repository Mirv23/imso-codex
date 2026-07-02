from django.urls import path

from .views import (
    BlogDetailView,
    BlogListView,
    ContactRequestCreateView,
    CourseEnrollmentCreateView,
    HomeView,
    OrderCreateView,
    PaymentConfirmationView,
    PaymentPageView,
    PaymentProcessView,
    VenueBookingCreateView,
    confirm_manual_payment,
    get_active_courses,
    get_active_products,
    get_active_providers,
    healthcheck,
)
from .webhooks import webhook_receiver


app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("api/contact-requests/", ContactRequestCreateView.as_view(), name="contact_request_create"),
    path("api/venue-bookings/", VenueBookingCreateView.as_view(), name="venue_booking_create"),
    path("api/course-enrollments/", CourseEnrollmentCreateView.as_view(), name="course_enrollment_create"),
    path("api/providers/", get_active_providers, name="active_providers"),
    path("api/courses/", get_active_courses, name="active_courses"),
    path("api/products/", get_active_products, name="active_products"),
    path("api/orders/", OrderCreateView.as_view(), name="order_create"),
    path("api/paiement/<str:type>/<int:id>/", PaymentProcessView.as_view(), name="payment_process"),
    path("api/paiement/confirm-manual/", confirm_manual_payment, name="payment_confirm_manual"),
    path("api/paiement/confirmation/<str:reference>/", PaymentConfirmationView.as_view(), name="payment_confirmation"),
    path("paiement/<str:type>/<int:id>/", PaymentPageView.as_view(), name="payment_page"),
    path("blog/", BlogListView.as_view(), name="blog_list"),
    path("blog/<slug:slug>/", BlogDetailView.as_view(), name="blog_detail"),
    path("health/", healthcheck, name="healthcheck"),
    path("api/webhook/<str:provider>/", webhook_receiver, name="webhook"),
]
