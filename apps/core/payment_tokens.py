"""Jetons opaques pour les liens de paiement.

Les URLs de paiement utilisaient l'identifiant séquentiel de la réservation /
inscription / commande (`/paiement/cours/42/`). N'importe qui pouvait incrémenter
ce numéro et voir les coordonnées (nom, téléphone, e-mail) pré-remplies d'autrui
— une fuite de données personnelles par énumération (IDOR).

On remplace l'identifiant par un jeton **signé** (SECRET_KEY) : impossible à
deviner ou à forger pour un autre enregistrement. Le jeton n'est pas chiffré (l'id
n'est pas un secret) — il empêche l'énumération, pas la lecture de l'id.
"""
from __future__ import annotations

from django.core import signing

_SALT = "imso.payment.link"


def make_payment_token(kind: str, obj_id: int) -> str:
    """Jeton opaque pour (type, id). `kind` = reservation | cours | commande."""
    return signing.dumps(int(obj_id), salt=f"{_SALT}:{kind}")


def read_payment_token(kind: str, token: str) -> int:
    """Renvoie l'id d'origine. Lève signing.BadSignature si le jeton est
    invalide ou ne correspond pas au type — l'appelant doit renvoyer un 404."""
    return int(signing.loads(token, salt=f"{_SALT}:{kind}"))
