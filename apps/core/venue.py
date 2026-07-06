"""Disponibilité des créneaux de réservation de salle.

Source de vérité côté serveur des créneaux et de leur occupation. Un créneau est
« occupé » (donc plus disponible sur le site public) dès qu'une réservation le
concernant est en paiement / validée / confirmée — c.-à-d. dès qu'un admin
accepte le paiement en attente. Les créneaux définis ici doivent rester synchro
avec SLOT_DEFS de templates/core/partials/footer.html.
"""
from __future__ import annotations

from datetime import time

from apps.adminpanel.models import VenueBooking

# (id, heure de début, heure de fin) — mêmes valeurs que SLOT_DEFS côté public.
VENUE_SLOTS = [
    ("matin", time(8, 0), time(12, 0)),
    ("aprem", time(13, 0), time(17, 0)),
    ("soir", time(18, 0), time(22, 0)),
]

# Statuts qui rendent un créneau indisponible : dès qu'un paiement est attendu,
# reçu (validation admin) ou la réservation confirmée, le créneau est pris.
OCCUPIED_STATUSES = (
    VenueBooking.Status.PAYMENT_PENDING,
    VenueBooking.Status.ADMIN_REVIEW,
    VenueBooking.Status.CONFIRMED,
)


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    """Deux plages horaires se chevauchent-elles ?"""
    return a_start < b_end and a_end > b_start


def occupied_slots_for(bookings) -> dict[str, set[str]]:
    """{ 'YYYY-MM-DD': {'matin', 'soir'} } des créneaux occupés par ces réservations."""
    result: dict[str, set[str]] = {}
    for b in bookings:
        for sid, s_start, s_end in VENUE_SLOTS:
            if _overlaps(b.start_time, b.end_time, s_start, s_end):
                result.setdefault(b.event_date.isoformat(), set()).add(sid)
    return result


def slot_taken(event_date, start_time, end_time, exclude_pk=None) -> bool:
    """Un créneau qui chevauche [start_time, end_time) ce jour-là est-il déjà pris
    par une réservation occupante (paiement/validée/confirmée) ?"""
    qs = VenueBooking.objects.filter(event_date=event_date, status__in=OCCUPIED_STATUSES)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return any(_overlaps(start_time, end_time, b.start_time, b.end_time) for b in qs)
