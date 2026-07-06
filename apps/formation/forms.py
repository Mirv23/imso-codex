from __future__ import annotations

from django import forms
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction

from apps.adminpanel.models import Profile


class RegisterForm(forms.Form):
    """Inscription d'un étudiant ou d'un professeur. L'email sert d'identifiant."""
    full_name = forms.CharField(max_length=120, label="Nom complet")
    email = forms.EmailField(label="Adresse email")
    phone = forms.CharField(max_length=40, required=False, label="Téléphone (facultatif)")
    role = forms.ChoiceField(
        choices=[("student", "Étudiant"), ("teacher", "Professeur")],
        initial="student", label="Je m'inscris en tant que",
    )
    password = forms.CharField(
        min_length=8, widget=forms.PasswordInput, label="Mot de passe (8 caractères min.)"
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un compte existe déjà avec cette adresse email.")
        return email

    def save(self) -> User:
        d = self.cleaned_data
        parts = d["full_name"].strip().split(" ", 1)
        # Atomique : soit User+Profile sont crees ensemble, soit rien (pas de
        # compte orphelin sans profil). En cas de course sur le meme email (deux
        # inscriptions concurrentes passent clean_email), la contrainte unique
        # username leve IntegrityError -> message clair au lieu d'un 500.
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=d["email"],
                    email=d["email"],
                    password=d["password"],
                    first_name=parts[0],
                    last_name=parts[1] if len(parts) > 1 else "",
                )
                Profile.objects.create(
                    user=user,
                    role=d["role"],
                    phone=d.get("phone", ""),
                    is_approved=(d["role"] == "student"),  # les profs attendent l'approbation admin
                )
        except IntegrityError:
            raise forms.ValidationError("Un compte existe déjà avec cette adresse email.")
        return user
