from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import JsonResponse
from django.views.generic import TemplateView

from .models import ContactRequest, Course, GEI, Member, VenueBooking


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "adminpanel/dashboard.html"
    login_url = "/django-admin/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = get_dashboard_summary()
        return context


def dashboard_summary(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required"}, status=401)
    return JsonResponse(get_dashboard_summary())


def get_dashboard_summary():
    savings = Member.objects.aggregate(total=Sum("monthly_saving_htg"))["total"] or 0
    return {
        "active_members": Member.objects.filter(status=Member.Status.ACTIVE).count(),
        "active_gei": GEI.objects.filter(is_active=True).count(),
        "active_courses": Course.objects.filter(is_active=True).count(),
        "pending_contacts": ContactRequest.objects.filter(is_processed=False).count(),
        "pending_bookings": VenueBooking.objects.filter(status=VenueBooking.Status.REQUESTED).count(),
        "savings_htg": savings,
    }
