from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from .models import ContactRequest, Course, GEI, Member, VenueBooking


@method_decorator(login_required(login_url="/django-admin/login/"), name="dispatch")
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "adminpanel/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = get_dashboard_summary()
        return context


@login_required(login_url="/django-admin/login/")
def dashboard_summary(request):
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
