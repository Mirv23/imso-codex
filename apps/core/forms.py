from __future__ import annotations

import re
from typing import Any

from django import forms

from apps.adminpanel.models import ContactRequest, Member, TrainingRegistration, VenueBooking


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


class TrainingRegistrationForm(forms.ModelForm):
    """Formulaire public de /register/. L'age n'est jamais demande : seulement
    une tranche, choisie au curseur. `website` est un pot de miel anti-robots
    (champ cache : un humain le laisse vide)."""

    website = forms.CharField(required=False)

    class Meta:
        model = TrainingRegistration
        fields = ["first_name", "last_name", "phone", "status", "status_other", "age_range", "interests"]
        error_messages = {
            "first_name": {"required": "Indiquez votre prénom."},
            "last_name": {"required": "Indiquez votre nom."},
            "phone": {"required": "Indiquez un numéro pour vous joindre."},
            "status": {"required": "Choisissez votre statut.", "invalid_choice": "Choisissez votre statut."},
            "age_range": {
                "required": "Faites glisser le curseur pour indiquer votre tranche d'âge.",
                "invalid_choice": "Faites glisser le curseur pour indiquer votre tranche d'âge.",
            },
            "interests": {"required": "Dites-nous en quelques mots ce que vous voulez apprendre."},
        }

    def __init__(self, *args: Any, event: str = "", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.event = event

    def clean_first_name(self) -> str:
        return " ".join(self.cleaned_data["first_name"].split())

    def clean_last_name(self) -> str:
        return " ".join(self.cleaned_data["last_name"].split())

    def clean_phone(self) -> str:
        phone = " ".join(self.cleaned_data["phone"].split())
        if not re.fullmatch(r"[+0-9 ().-]+", phone) or len(re.sub(r"\D", "", phone)) < 8:
            raise forms.ValidationError("Ce numéro ne semble pas valide (ex. : +509 33 70 7662).")
        return phone

    def clean_interests(self) -> str:
        return self.cleaned_data["interests"].strip()

    def clean(self) -> dict[str, Any]:
        data = super().clean()
        if data.get("status") == TrainingRegistration.Status.OTHER and not (data.get("status_other") or "").strip():
            self.add_error("status_other", "Précisez votre statut.")
        elif data.get("status") != TrainingRegistration.Status.OTHER:
            data["status_other"] = ""
        phone = data.get("phone")
        if phone and self.event:
            digits = re.sub(r"\D", "", phone)[-8:]
            for existing in TrainingRegistration.objects.filter(event=self.event).values_list("phone", flat=True):
                if re.sub(r"\D", "", existing)[-8:] == digits:
                    self.add_error("phone", "Ce numéro est déjà inscrit à cette formation.")
                    break
        return data

    def save(self, commit: bool = True) -> TrainingRegistration:
        obj = super().save(commit=False)
        obj.event = self.event
        if commit:
            obj.save()
        return obj

