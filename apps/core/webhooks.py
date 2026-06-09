import json
import logging
import os

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.adminpanel.models import Payment

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_receiver(request, provider):
    secret = request.META.get("HTTP_X_WEBHOOK_SECRET", "")
    expected = os.environ.get("WEBHOOK_SECRET", "")
    if expected and secret != expected:
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
        logger.info("Webhook received from provider=%s payload=%s", provider, payload)
        return JsonResponse({"status": "ok"})

    if not external_ref:
        logger.warning("No external reference found in %s webhook payload", provider)
        return JsonResponse({"status": "ok", "payment": None})

    try:
        payment = Payment.objects.get(external_reference=external_ref)
    except Payment.DoesNotExist:
        logger.info("No payment found for external_reference=%s (provider=%s)", external_ref, provider)
        return JsonResponse({"status": "ok", "payment": None})

    if payment.status == Payment.Status.PENDING:
        payment.status = Payment.Status.PAID
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "paid_at"])
        logger.info(
            "Payment %s marked PAID from webhook (external_reference=%s, provider=%s)",
            payment.reference, external_ref, provider,
        )
    else:
        logger.info(
            "Payment %s already in status %s (external_reference=%s, provider=%s)",
            payment.reference, payment.status, external_ref, provider,
        )

    return JsonResponse({"status": "ok", "payment": payment.reference})
