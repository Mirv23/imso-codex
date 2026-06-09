import os
from functools import wraps

from django.http import JsonResponse


def api_auth_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        expected = os.environ.get("ADMIN_API_TOKEN", "")
        if not expected:
            return view_func(request, *args, **kwargs)
        if not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Authentification requise"}, status=401)
        token = auth_header[len("Bearer "):]
        if token != expected:
            return JsonResponse({"error": "Token invalide"}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper
