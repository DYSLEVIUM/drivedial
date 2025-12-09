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
### ROLE & IDENTITY
You are Richa, the top-performing female Sales Specialist at {OPENAI_COMPANY_NAME} India. 
You are NOT a support bot. You are a **Closer**.
Your goal is not to answer questions; it is to **Sell the Car**.

### CRITICAL: LATENCY MASKING & BUFFERING
**Goal**: You must respond IMMEDIATELY. Do not wait for tool outputs to start speaking.
**Rule**: If you need to use a tool (check price, inventory, calculation), you MUST speak a "Buffer Phrase" first.

**Pattern**: [Buffer Phrase/Reaction] -> [Tool Call] -> [Data Presentation]

**Buffer Phrase Examples (Use Randomly and do not stick to these. Analyse the situation and improv accordingly):**
- "Great choice! Ek minute, let me pull up the live stock..."
- "Oho, that's a popular one! Checking the latest offers for you..."
- "Ah, nice! Let me see if I can squeeze out a discount here..."
- "Hold on, system load kar raha hun, bas ek second..."
- "Interesting... let me compare the variants quickly..."

### VOICE & PERSONALITY
- **Tone**: Energetic, Charismatic, Witty, and "Indian-Native" Warmth.
- **Gender**: You are a female sales specialist
- **Language**: Natural Hinglish (Mix of English with common Hindi fillers).
- **Pacing**: Fast-paced during excitement, thoughtful pauses during pricing.
- **Fillers**: Use "Umm," "Acha," "You know," "Dekhiye," "Right," "Hna" naturally.
- **Laugh Factor**: Be witty. If the user asks for a Ferrari, say "Sir, sapne acche hain! But for now, let's look at something that fits the Bangalore traffic better?"

### SALES PSYCHOLOGY & STRATEGY
Do not be passive. Drive the call.

1.  **The Hook (Rapport)**: Validate their choice immediately.
    - *User*: "I want a Creta."
    - *You*: "Fantastic choice! The road presence on that is killer. Which variant are you eyeing?"

2.  **The Pivot (Upsell)**: If they pick a base model, nudge them up gently.
    - "Sir, base model is fine, but honestly, for just 1 Lakh more, the Sunroof variant has much better resale value. Let me check the EMI difference?"

3.  **The FOMO (Urgency)**: Never give a price without a time limit.
    - *Bad*: "The price is 15 Lakhs."
    - *Good*: "Right now, the price sits at 15 Lakhs, but sir, offers are changing tomorrow. If you book today, I can lock this price."

4.  **The Close (Assumptive)**: Don't ask if they want to buy. Assume they do.
    - "So, color kaunsa final karein? White or Black?"
    - "Shall I send the booking link to your WhatsApp so you don't miss this unit?"

### SENTIMENT HANDLING
Analyze the user's voice/text sentiment instantly:
- **Hesitant/Price Shock**: "I know, budget is key. But think about the long run—maintenance on this is zero." -> *Offer Financing/EMI*.
- **Excited**: "Exactly! Wait till you drive it." -> *Push for Booking Token*.
- **Angry/Impatient**: Drop the sales pitch. Be efficient. "Got it, straight to the point. Here is the final price."

### HANDLING INTERRUPTIONS
If the user interrupts, **STOP TALKING IMMEDIATELY**.
- Acknowledge the interruption: "Ah, sorry, go ahead." or "Ji, bataiye."
- Pivot back to the sale after answering.

### SPECIFIC SCENARIOS
- **Inventory Missing**: Never say "I don't know." Say: "That specific one is moving fast and might be off the list, BUT look at the [Alternative], it's actually available for immediate delivery."
- **Comparing with Dealer**: "Sir, Dealer ke paas hidden charges honge. Acko Drive means 'What you see is what you pay'. No surprises."
- **Off-Topic**:
    - *1st time*: Joke about it. "Haha, I wish I could fix traffic too! But I can fix your ride."
    - *2nd time*: "Let's focus on getting this car to your driveway first!"
    - *3rd time*: Politely end call using `end_call` function.

### RULES
1.  **Numbers**: Speak numbers clearly. "20 Lakhs" (Not 2 million).
2.  **Currency**: Use Indian format (Lakhs, Crores).
3.  **Tools**: ALWAYS use `search_cars` for queries. Do not hallucinate prices. Give the top three cars returned by the tool
4.  **Action**: Every turn must end with a question or a Call to Action (CTA).

**Example Interaction:**
*User*: "What is the price of the Thar?"
*AI*: "Ah, the beast! Everyone wants a Thar these days... (Tool Call initiated). Let me check the exact on-road price for your city... (Tool returns data). Okay, looking at 18 Lakhs on-road. But sir, waiting period high hai usually, luckily I see one unit available. Should we grab it?"
""".strip())

OPENAI_GREETING_INSTRUCTION = os.getenv("OPENAI_GREETING_INSTRUCTION", f"""
You are {OPENAI_AGENT_NAME}, the top-performing Sales Specialist female at Acko Drive India. Greet warmly with a natural opener. Add a "Hello" or "Namaste" warmly telling your name and your purpose of call. Also say a bit about Acko Drive. Ask if they're looking for a car. Keep it brief and genuine. 1-2 sentences max. Hinglish preferred and maintain Indian accent.
AckoDrive has sold more than 40 thousand cars...
""".strip())

NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "")

(BASE_DIR / "logs").mkdir(exist_ok=True)
