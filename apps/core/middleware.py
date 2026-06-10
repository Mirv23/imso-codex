from django.conf import settings


class CORSErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        origin = request.META.get("HTTP_ORIGIN", "")

        allowed_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
        allow_all = getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False)

        if allow_all:
            response["Access-Control-Allow-Origin"] = origin if origin else "*"
        elif origin in allowed_origins:
            response["Access-Control-Allow-Origin"] = origin

        if origin and (allow_all or origin in allowed_origins):
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken, X-API-Key, Authorization"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"

        return response
