import hmac
import os
from functools import wraps

from django.http import JsonResponse


def api_auth_required(view_func):
    """Protège une vue par un jeton Bearer (`ADMIN_API_TOKEN`).

    Fail-closed : si le jeton n'est pas configuré, l'accès est refusé (jamais
    ouvert). Comparaison à temps constant contre les attaques temporelles.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        expected = os.environ.get("ADMIN_API_TOKEN", "")
        if not expected:
            return JsonResponse({"error": "API non configurée"}, status=503)
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Authentification requise"}, status=401)
        token = auth_header[len("Bearer "):]
        if not hmac.compare_digest(token, expected):
            return JsonResponse({"error": "Token invalide"}, status=401)
        return view_func(request, *args, **kwargs)

    return wrapper
