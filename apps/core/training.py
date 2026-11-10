"""Formation affichee sur la page publique /register/ (lien imprime sur le flyer).

Pour une prochaine session : changer ce bloc (et `slug`, pour que les inscrits
des deux sessions restent separes dans le panel admin).
"""

from __future__ import annotations

import datetime

CURRENT_TRAINING = {
    "slug": "education-financiere-2026-11",
    "partners": "IMSO | CCFOR",
    "kicker": "Spécial fin d'année",
    "title": "Formation en éducation financière",
    "dates": "Samedi 21 et dimanche 22 novembre 2026",
    "hours": "14 h – 18 h, soit 8 heures de formation",
    "place": "45, rue Général Borgella, Les Cayes",
    "fee_registration": "250 gourdes",
    "fee_participation": "2 500 gourdes",
    "included": "Livre + cahier d'exercices, certificat",
    "whatsapp": "50933707662",
    "whatsapp_display": "+509 33 70 7662",
    # Inscriptions ouvertes jusqu'au dernier jour de la formation inclus.
    "last_day": datetime.date(2026, 11, 22),
}
