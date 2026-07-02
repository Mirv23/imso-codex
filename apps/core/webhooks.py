import hmac
import json
import logging
import os

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.adminpanel.models import Payment

logger = logging.getLogger(__name__)


def _amount_from_payload(payload: dict) -> int | None:
    """Extrait un montant HTG du payload si présent (sinon None)."""
    for key in ("amount_htg", "amount"):
        if key in payload:
            try:
                return int(payload[key])
            except (TypeError, ValueError):
                return None
    return None


@csrf_exempt
@require_http_methods(["POST"])
def webhook_receiver(request, provider):
    # S1 — fail-closed : sans secret configuré, on refuse (jamais fail-open).
    expected = os.environ.get("WEBHOOK_SECRET", "")
    if not expected:
        logger.error("WEBHOOK_SECRET non configuré — webhook refusé (provider=%s)", provider)
        return JsonResponse({"error": "Webhook non configuré"}, status=503)

    secret = request.META.get("HTTP_X_WEBHOOK_SECRET", "")
    # Comparaison à temps constant (anti-timing).
    if not hmac.compare_digest(secret, expected):
        logger.warning("Webhook secret mismatch for provider=%s", provider)
        return JsonResponse({"error": "Invalid secret"}, status=401)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        payload = {"raw": request.body.decode("utf-8", errors="replace")}

    if provider == "stripe":
        external_ref = payload.get("payment_intent", "")
    elif provider == "moncash":
        external_ref = payload.get("transactionId", "")
    else:
        # Ne pas logger le payload complet (peut contenir des données sensibles).
        logger.info("Webhook received from provider=%s", provider)
        return JsonResponse({"status": "ok"})

    if not external_ref:
        logger.warning("No external reference found in %s webhook payload", provider)
        return JsonResponse({"status": "ok", "payment": None})

    try:
        payment = Payment.objects.get(external_reference=external_ref)
    except Payment.DoesNotExist:
        logger.info("No payment found for external_reference=%s (provider=%s)", external_ref, provider)
        return JsonResponse({"status": "ok", "payment": None})

    # Vérification du montant quand le fournisseur le transmet : empêche de valider
    # un paiement dont le montant reçu ne correspond pas à celui attendu.
    payload_amount = _amount_from_payload(payload)
    if payload_amount is not None and payload_amount != payment.amount_htg:
        logger.warning(
            "Montant webhook incohérent pour %s: reçu=%s attendu=%s (provider=%s)",
            payment.reference, payload_amount, payment.amount_htg, provider,
        )
        return JsonResponse({"error": "Montant incohérent"}, status=400)

    if payment.status == Payment.Status.PENDING:
        payment.status = Payment.Status.PAID
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "paid_at"])
        logger.info(
            "Payment %s marked PAID from webhook (provider=%s)",
            payment.reference, provider,
        )
    else:
        logger.info(
            "Payment %s already in status %s (provider=%s)",
            payment.reference, payment.status, provider,
        )

    return JsonResponse({"status": "ok", "payment": payment.reference})
