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
        first_name = parts[0]
        last_name = " ".join(parts[1:]) or "-"
        member, _created = Member.objects.get_or_create(
            phone=self.cleaned_data["phone"],
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "email": self.cleaned_data.get("email", ""),
            },
        )
        updated = False
        if member.email != self.cleaned_data.get("email", ""):
            member.email = self.cleaned_data.get("email", "")
            updated = True
        if updated:
            member.save(update_fields=["email", "updated_at"])
        return member
