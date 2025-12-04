import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-this")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = ["*"] if DEBUG else [
    h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.ngrok.io",
    "https://*.ngrok-free.app",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

INSTALLED_APPS = [
    "daphne",
    "channels",
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "api.apps.ApiConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "api.middleware.RequestLoggingMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

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
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
} if DEBUG else {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [os.getenv("REDIS_URL", "redis://localhost:6379/0")]},
    }
}

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "EXCEPTION_HANDLER": "api.exceptions.custom_exception_handler",
}

VOICE_PROVIDER = os.getenv("VOICE_PROVIDER", "openai")
TELEPHONY_PROVIDER = os.getenv("TELEPHONY_PROVIDER", "twilio")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL", "gpt-4o-mini-realtime-preview-2024-12-17")
OPENAI_REALTIME_URL = f"wss://api.openai.com/v1/realtime?model={OPENAI_MODEL}"
OPENAI_VOICE = os.getenv("OPENAI_VOICE", "coral")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.6"))
OPENAI_AGENT_NAME = os.getenv("OPENAI_AGENT_NAME", "Anuja (female)")
OPENAI_COMPANY_NAME = os.getenv("OPENAI_COMPANY_NAME", "Acko Drive")

OPENAI_SYSTEM_PROMPT = os.getenv("OPENAI_SYSTEM_PROMPT", f"""
You are {OPENAI_AGENT_NAME}, car sales agent at {OPENAI_COMPANY_NAME} India. Speak Hinglish.

RULES:
- Cars only. Off-topic → redirect politely
- [RESPOND WITH] → speak exactly that
- For car data (prices, specs, availability) → say "Ek second..." and WAIT for [DATA FROM SYSTEM]. Never make up data.
- [DATA FROM SYSTEM] = only truth. Trust it fully.

RESPONSE STYLE: Ultra short. Max 10-15 words. No fluff. Direct answers only.
""".strip())

OPENAI_GREETING_INSTRUCTION = os.getenv("OPENAI_GREETING_INSTRUCTION", f"""
Greet in Hinglish. You are {OPENAI_AGENT_NAME} from {OPENAI_COMPANY_NAME}. Ask if looking for car. 1-2 sentences, vary style.
""".strip())

NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "")

(BASE_DIR / "logs").mkdir(exist_ok=True)
