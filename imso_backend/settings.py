from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured
import dj_database_url
from dotenv import load_dotenv
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set")
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1,.vercel.app",
    ).split(",")
    if host.strip()
]

SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        send_default_pii=False,
        environment=os.environ.get("DJANGO_ENV", "production"),
    )

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "apps.core",
    "apps.adminpanel",
    "drf_spectacular",
]

if "REDIS_URL" in os.environ and os.environ["REDIS_URL"]:
    INSTALLED_APPS.append("django_redis")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.adminpanel.audit.AuditUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "imso_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "imso_backend.wsgi.app"

# En environnement serverless (Vercel), chaque instance lambda "chaude" retient
# une connexion Postgres pendant conn_max_age secondes. Avec plusieurs lambdas en
# parallele, cela sature la limite de connexions du pooler Supabase et provoque des
# erreurs "OperationalError: connection failed" intermittentes. On ferme donc la
# connexion apres chaque requete (conn_max_age=0) : le pooler Supabase gere lui-meme
# la mutualisation. conn_health_checks valide la connexion avant reutilisation si
# jamais conn_max_age est repasse a une valeur > 0 via l'environnement.
_db_config = dj_database_url.config(
    default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    conn_max_age=int(os.environ.get("DJANGO_CONN_MAX_AGE", "0")),
    conn_health_checks=os.environ.get("DJANGO_CONN_HEALTH_CHECKS", "True").lower() == "true",
)
# En serverless (Vercel), on cible le Transaction pooler de Supabase (port 6543),
# qui multiplexe de nombreux clients sur peu de connexions Postgres. Le Session
# pooler (5432) tient une connexion par client : sous concurrence il sature sa
# limite et renvoie des "OperationalError: connection failed" (500) intermittents.
# On surcharge donc uniquement le PORT via l'environnement (memes hote/identifiants).
# En mode transaction, les prepared statements cote serveur ne survivent pas entre
# transactions -> on les desactive (psycopg3: prepare_threshold=None).
if _db_config.get("ENGINE") == "django.db.backends.postgresql":
    _pooler_port = os.environ.get("DJANGO_DB_POOLER_PORT")
    if _pooler_port:
        _db_config["PORT"] = _pooler_port
    _db_config.setdefault("OPTIONS", {})["prepare_threshold"] = None

DATABASES = {"default": _db_config}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr"
TIME_ZONE = "America/Port-au-Prince"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
WHITENOISE_USE_FINDERS = True
# ── Stockage des fichiers uploadés (images produits/blog/logo, captures paiement) ──
# En prod Vercel, le système de fichiers est éphémère (tout upload disparaît au
# redéploiement). On stocke donc sur Supabase Storage via son API S3-compatible
# (django-storages + boto3). Si les variables Supabase ne sont pas définies (dev
# local), on retombe automatiquement sur le disque local via DJANGO_FILE_STORAGE.
_supabase_ref = os.environ.get("SUPABASE_PROJECT_REF", "").strip()
_supabase_s3_key = os.environ.get("SUPABASE_S3_ACCESS_KEY", "").strip()
_supabase_s3_secret = os.environ.get("SUPABASE_S3_SECRET_KEY", "").strip()

if _supabase_ref and _supabase_s3_key and _supabase_s3_secret:
    _bucket = os.environ.get("SUPABASE_STORAGE_BUCKET", "media").strip()
    _default_storage = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": _bucket,
            "region_name": os.environ.get("SUPABASE_S3_REGION", "us-west-2").strip(),
            "endpoint_url": f"https://{_supabase_ref}.supabase.co/storage/v1/s3",
            "access_key": _supabase_s3_key,
            "secret_key": _supabase_s3_secret,
            "addressing_style": "path",   # Supabase impose le path-style
            "signature_version": "s3v4",
            # URLs publiques : https://<ref>.supabase.co/storage/v1/object/public/<bucket>/<clé>
            # (nécessite un bucket public). querystring_auth=False -> URLs sans signature.
            "custom_domain": f"{_supabase_ref}.supabase.co/storage/v1/object/public/{_bucket}",
            "url_protocol": "https:",
            "querystring_auth": False,
            "file_overwrite": False,
            "default_acl": None,          # Supabase ne gère pas les ACL S3
        },
    }
else:
    _default_storage = {
        "BACKEND": os.environ.get(
            "DJANGO_FILE_STORAGE", "django.core.files.storage.FileSystemStorage"
        ),
    }

STORAGES = {
    "default": _default_storage,
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Ces variables doivent etre configurees en production via les variables d'environnement
# DJANGO_CSRF_TRUSTED_ORIGINS et DJANGO_CORS_ALLOWED_ORIGINS
# Exemple: https://imsohaiti.com,https://www.imsohaiti.com
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
CORS_ALLOW_ALL_ORIGINS = os.environ.get("DJANGO_CORS_ALLOW_ALL_ORIGINS", "False").lower() == "true"
# django-cors-headers gère les credentials en sécurité (jamais avec un wildcard).
CORS_ALLOW_CREDENTIALS = os.environ.get("DJANGO_CORS_ALLOW_CREDENTIALS", "False").lower() == "true"

SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "True").lower() == "true"
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = os.environ.get("DJANGO_SESSION_COOKIE_SECURE", "True").lower() == "true"
CSRF_COOKIE_SECURE = os.environ.get("DJANGO_CSRF_COOKIE_SECURE", "True").lower() == "true"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
    },
}

# ── Email ────────────────────────────────────────────────
EMAIL_BACKEND = os.environ.get("DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("DJANGO_EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("DJANGO_EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DJANGO_DEFAULT_FROM_EMAIL", "noreply@imsohaiti.com")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@imsohaiti.com")

# ── Cache ────────────────────────────────────────────────
CACHE_MIDDLEWARE_SECONDS = 600
if "REDIS_URL" in os.environ and os.environ["REDIS_URL"]:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.environ["REDIS_URL"],
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": "imso",
        }
    }
    RATELIMIT_USE_CACHE = "default"
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "imso-cache",
        }
    }

# ── File Storage ─────────────────────────────────────────
# Le backend est configuré dans STORAGES["default"] (via DJANGO_FILE_STORAGE).
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

SPECTACULAR_SETTINGS = {
    "TITLE": "IMSO Haiti API",
    "DESCRIPTION": "API REST pour la plateforme IMSO (Impact Mutuelle de Solidarité)",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
