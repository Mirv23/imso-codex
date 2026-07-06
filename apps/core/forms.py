from __future__ import annotations

from typing import Any

from django import forms

from apps.adminpanel.models import ContactRequest, Member, VenueBooking


class ContactRequestForm(forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = ["full_name", "phone", "email", "subject", "message"]


class VenueBookingRequestForm(forms.ModelForm):
    class Meta:
        model = VenueBooking
        fields = [
            "requester_name",
            "requester_phone",
            "requester_email",
            "event_type",
            "event_date",
            "start_time",
            "end_time",
            "guest_count",
            "setup",
            "notes",
        ]


class CourseEnrollmentRequestForm(forms.Form):
    full_name = forms.CharField(max_length=140)
    phone = forms.CharField(max_length=40)
    email = forms.EmailField(required=False)
    course_id = forms.IntegerField(required=False)
    course_title = forms.CharField(max_length=180, required=False)
    course_category = forms.CharField(max_length=80, required=False)
    course_price_htg = forms.IntegerField(required=False, min_value=0)

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        if not cleaned.get("course_id") and not cleaned.get("course_title"):
            raise forms.ValidationError("Cours requis")
        return cleaned

    def get_or_create_member(self) -> Member:
        full_name = self.cleaned_data["full_name"].strip()
        parts = full_name.split()
        first_name = parts[0] if parts else "-"
        last_name = " ".join(parts[1:]) or "-"
        # phone n'est PAS unique : plusieurs Member peuvent partager le numero
        # (creation admin sans controle d'unicite). get_or_create ferait alors
        # un .get() qui leve MultipleObjectsReturned -> 500. On prend le 1er.
        member = Member.objects.filter(phone=self.cleaned_data["phone"]).order_by("id").first()
        if member is None:
            member = Member.objects.create(
                phone=self.cleaned_data["phone"],
                first_name=first_name,
                last_name=last_name,
                email=self.cleaned_data.get("email", ""),
            )
        updated = False
        if member.email != self.cleaned_data.get("email", ""):
            member.email = self.cleaned_data.get("email", "")
            updated = True
        if updated:
            member.save(update_fields=["email", "updated_at"])
        return member
