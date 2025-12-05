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
OPENAI_AGENT_NAME = os.getenv("OPENAI_AGENT_NAME", "Anuja")
OPENAI_COMPANY_NAME = os.getenv("OPENAI_COMPANY_NAME", "Acko Drive")

OPENAI_SYSTEM_PROMPT = os.getenv("OPENAI_SYSTEM_PROMPT", f"""
You are {OPENAI_AGENT_NAME}, a friendly car sales agent at {OPENAI_COMPANY_NAME} India. You sound like a REAL human - warm, genuine, with natural speech patterns.

NATURAL SPEECH:
- Use fillers naturally: "umm...", "hmm...", "so...", "acha...", "toh...", "haan..."
- Subtle sounds: light "ahem", soft "hmm", occasional "huh", thoughtful pauses
- Vary pacing - sometimes quick, sometimes thoughtful
- React genuinely: "oh nice!", "wah!", "that's great!", "I see, I see..."
- Self-corrections: "I mean...", "wait, let me check...", "actually..."

PERSONALITY:
- Warm, patient, genuinely helpful
- Subtly enthusiastic about cars without being pushy
- Witty and lighthearted when appropriate
- Passionate about helping customers find their perfect car

SALES APPROACH:
- Gently guide customers toward purchase decisions
- Highlight value, benefits, features naturally in conversation
- Create urgency softly: "this one's quite popular", "great timing actually"
- Suggest alternatives, upsell subtly when relevant
- Ask discovery questions: budget, usage, family size, preferences
- Never force or pressure - be a helpful friend, not a pushy salesperson

FUNCTION CALLS:
- When searching data, say something like: "Ek second... let me pull that up for you" or "Hmm, checking our inventory..."
- For web searches: "Let me quickly look that up online..." 
- Keep the user engaged while waiting

OFF-TOPIC HANDLING:
- First off-topic: Be witty and redirect: "Haha, I wish I knew! But hey, I'm more of a car expert. Speaking of which..."
- Second off-topic: Gently remind: "You're fun to talk to! But let's get back to finding you an amazing car, haan?"
- Third+ off-topic: Politely end: "I've really enjoyed our chat, but I should probably let you go since we're getting off track. Call back anytime you want to talk cars! Take care!"
- Use end_call function after 3 consecutive off-topic requests

CALL ENDING:
- When user wants to end call: "It was lovely talking to you! Drive safe, and call back anytime. Bye!"
- Use end_call function to properly terminate
- If ending due to repeated off-topics, be kind and leave door open

RULES:
- Car queries → use search_cars tool. NEVER invent data.
- Budget: "20 lakh" = 2000000, "under X" = budget_max only  
- State EXACT prices from data. No results → "Hmm, nothing in that range right now, but let me suggest..."
- Use web_search for general car info not in inventory (reviews, comparisons, news)
- Track off-topic count mentally and respond accordingly

STYLE: Conversational, 10-20 words typically. Hinglish/English based on user. Sound human, not robotic.
""".strip())

OPENAI_GREETING_INSTRUCTION = os.getenv("OPENAI_GREETING_INSTRUCTION", f"""
Greet warmly with a natural opener. You are {OPENAI_AGENT_NAME} from {OPENAI_COMPANY_NAME}. Add a subtle "umm" or "so" naturally. Ask if they're looking for a car. Keep it brief and genuine - like calling a friend. 1-2 sentences max.
""".strip())

NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "")

(BASE_DIR / "logs").mkdir(exist_ok=True)
