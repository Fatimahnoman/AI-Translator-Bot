"""
TranslateHub — AI-Powered Translator
Supports Gemini and OpenRouter providers with 14 languages.
"""

import os
import re
import time
import logging
import html
from typing import Optional
from collections import defaultdict
from datetime import datetime, timezone
from dotenv import load_dotenv
import chainlit as cl
from litellm import completion
import psycopg2
import psycopg2.extras

# ─── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("translatehub")

# ─── Environment ───────────────────────────────────────────
load_dotenv()

GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")

if not GEMINI_API_KEY and not OPENROUTER_API_KEY:
    logger.critical("No API keys found. Set GEMINI_API_KEY or OPENROUTER_API_KEY in .env")
    raise ValueError("At least one API key is required in .env: GEMINI_API_KEY or OPENROUTER_API_KEY")

# ─── Database (Neon PostgreSQL) ───────────────────────────
DATABASE_URL: Optional[str] = os.getenv("NEON_DATABASE_URL")


def get_db_connection():
    """Get a PostgreSQL connection from DATABASE_URL."""
    if not DATABASE_URL:
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        logger.error("Database connection failed: %s", e)
        return None


def init_db() -> None:
    """Create the chat_sessions and messages tables if they don't exist."""
    conn = get_db_connection()
    if not conn:
        logger.warning("NEON_DATABASE_URL not set — chat history will not be persisted")
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    provider VARCHAR(50) DEFAULT 'gemini',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id, created_at)
            """)
        conn.commit()
        logger.info("Database tables initialized")
    except psycopg2.Error as e:
        logger.error("Failed to initialize database: %s", e)
    finally:
        conn.close()


def save_message(session_id: str, role: str, content: str, metadata: dict | None = None) -> bool:
    """Save a single message to the database."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chat_sessions (session_id, updated_at)
                VALUES (%s, NOW())
                ON CONFLICT (session_id) DO UPDATE SET updated_at = NOW()
            """, (session_id,))
            cur.execute("""
                INSERT INTO messages (session_id, role, content, metadata)
                VALUES (%s, %s, %s, %s)
            """, (session_id, role, content, psycopg2.extras.Json(metadata or {})))
        conn.commit()
        return True
    except psycopg2.Error as e:
        logger.error("Failed to save message: %s", e)
        return False
    finally:
        conn.close()


def get_session_history(session_id: str, limit: int = 50) -> list[dict]:
    """Retrieve recent messages for a session."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT role, content, created_at
                FROM messages
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (session_id, limit))
            rows = cur.fetchall()
            return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
    except psycopg2.Error as e:
        logger.error("Failed to fetch history: %s", e)
        return []
    finally:
        conn.close()


# Initialize DB on startup
init_db()

# ─── Providers ─────────────────────────────────────────────
PROVIDERS: dict[str, dict[str, Optional[str]]] = {
    "gemini": {
        "model": "gemini/gemini-2.0-flash",
        "api_key": GEMINI_API_KEY,
    },
    "openrouter": {
        "model": "openrouter/openai/gpt-3.5-turbo",
        "api_key": OPENROUTER_API_KEY,
    },
}

DEFAULT_PROVIDER: str = "gemini" if GEMINI_API_KEY else "openrouter"
logger.info("Default provider: %s", DEFAULT_PROVIDER)

# ─── Supported Languages ──────────────────────────────────
SUPPORTED_LANGUAGES: dict[str, str] = {
    "english": "English",
    "urdu": "Urdu",
    "arabic": "Arabic",
    "french": "French",
    "german": "German",
    "spanish": "Spanish",
    "hindi": "Hindi",
    "japanese": "Japanese",
    "chinese": "Chinese",
    "turkish": "Turkish",
    "italian": "Italian",
    "russian": "Russian",
    "portuguese": "Portuguese",
    "korean": "Korean",
}

EXAMPLE_LANGUAGES: str = "Urdu, Arabic, French, German, Spanish"

# ─── Rate Limiting ─────────────────────────────────────────
RATE_LIMIT_WINDOW: int = 60  # seconds
RATE_LIMIT_MAX: int = 15     # max messages per window

_rate_store: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(user_id: str) -> bool:
    """Returns True if allowed, False if rate-limited."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    _rate_store[user_id] = [t for t in _rate_store[user_id] if t > window_start]
    if len(_rate_store[user_id]) >= RATE_LIMIT_MAX:
        return False
    _rate_store[user_id].append(now)
    return True


# ─── Sanitization ──────────────────────────────────────────
_TAG_RE = re.compile(r"<[^>]+>")


def sanitize_input(text: str, max_length: int = 2000) -> str:
    """Strip HTML tags, escape entities, enforce length limit."""
    cleaned = _TAG_RE.sub("", text)
    cleaned = html.escape(cleaned)
    return cleaned[:max_length].strip()


def sanitize_for_output(text: str, max_length: int = 5000) -> str:
    """Escape HTML in LLM output for safe rendering."""
    return html.escape(text)[:max_length].strip()


# ─── Language Validation ──────────────────────────────────
def validate_language(text: str) -> Optional[str]:
    """Validate if input is a supported language. Returns title-case name or None."""
    cleaned = text.strip().lower()
    return SUPPORTED_LANGUAGES.get(cleaned)


# ─── Chat Start ───────────────────────────────────────────
@cl.on_chat_start
async def on_chat_start() -> None:
    import uuid
    session_id = str(uuid.uuid4())
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("chat_history", [])
    cl.user_session.set("awaiting_language", True)
    cl.user_session.set("awaiting_text", False)
    cl.user_session.set("target_language", None)
    cl.user_session.set("provider", DEFAULT_PROVIDER)
    logger.info("New session: %s", session_id)

    await cl.Message(
        author="",
        content=(
            '<div class="welcome-header">'
            '<div class="welcome-logo">🌐</div>'
            '<h1 class="welcome-title">TranslateHub</h1>'
            '<p class="welcome-subtitle">Translate naturally into 100+ Languages using Gemini or OpenRouter</p>'
            '</div>\n\n'
            '<div class="welcome-guide">'
            '   💡 Tip: If one AI Model is slow or not working, switch anytime with:\n'
            '`/model gemini` or `/model openrouter`'
            '</div>'
        ),
    ).send()

    await cl.Message(
        content="🌍 **Break language barriers instantly — Type a Language below to get Started**",
    ).send()


# ─── Message Handler ──────────────────────────────────────
@cl.on_message
async def on_message(message: cl.Message) -> None:
    raw_text = message.content
    msg_text = sanitize_input(raw_text)

    if not msg_text:
        await cl.Message(content="⚠️ Please enter a valid message.").send()
        return

    # Rate limit check
    user_id = cl.user_session.get("user_id", "anonymous")
    if not _check_rate_limit(user_id):
        logger.warning("Rate limit exceeded for user %s", user_id)
        await cl.Message(
            content="⏳ **Too many requests.** Please wait a moment and try again."
        ).send()
        return

    # ── Greetings ──────────────────────────────────────────
    greetings = [
        "hello", "hi", "hey", "hola", "salam", "asalam", "assalam",
        "good morning", "good evening", "good afternoon", "sup", "yo",
        "howdy", "greetings", "how are you", "how r u", "kya haal",
    ]
    if any(msg_text.lower().startswith(g) for g in greetings):
        await cl.Message(
            content=(
                "Hey there! Welcome to **TranslateHub** 🌐\n\n"
                "I'm here to help you translate text into any of the 14 supported languages.\n\n"
                "Which language would you like to translate into today?"
            )
        ).send()
        return

    # ── /model command ─────────────────────────────────────
    if msg_text.lower().startswith("/model"):
        parts = msg_text.split(maxsplit=1)
        if len(parts) < 2:
            current = cl.user_session.get("provider", DEFAULT_PROVIDER)
            await cl.Message(
                content=f"**Current provider:** `{current}`\n\nUsage: `/model gemini` or `/model openrouter`"
            ).send()
            return

        chosen = parts[1].strip().lower()
        if chosen not in PROVIDERS:
            await cl.Message(
                content=f"❌ Unknown provider: `{chosen}`. Available: {', '.join(PROVIDERS.keys())}"
            ).send()
            return

        if not PROVIDERS[chosen]["api_key"]:
            await cl.Message(
                content=f"❌ `{chosen}` API key is not configured in `.env`."
            ).send()
            return

        cl.user_session.set("provider", chosen)
        cl.user_session.set("awaiting_language", True)
        cl.user_session.set("awaiting_text", False)
        cl.user_session.set("target_language", None)
        logger.info("Provider switched to %s", chosen)

        await cl.Message(
            content=(
                f"✅ Provider switched to **{chosen}** (`{PROVIDERS[chosen]['model']}`)\n\n"
                "🌍 **Which language would you like to get started with?**\n\n"
                f"**Examples:** {EXAMPLE_LANGUAGES}"
            )
        ).send()
        return

    # ── /change command ────────────────────────────────────
    if msg_text.lower() == "/change":
        cl.user_session.set("awaiting_language", True)
        cl.user_session.set("awaiting_text", False)
        cl.user_session.set("target_language", None)
        await cl.Message(
            content=(
                "🌍 **Which language would you like to translate into next?**\n\n"
                f"Examples:\n{EXAMPLE_LANGUAGES}"
            )
        ).send()
        return

    # ── /help command ──────────────────────────────────────
    if msg_text.lower() in ("/help", "!help"):
        await cl.Message(
            content=(
                "📖 **TranslateHub Commands**\n\n"
                "`/model gemini` — Switch to Gemini\n"
                "`/model openrouter` — Switch to OpenRouter\n"
                "`/change` — Change target language\n"
                "`/help` — Show this help\n\n"
                "**How to use:**\n"
                "1. Type a language name\n"
                "2. Enter text to translate\n"
                "3. Get instant translation"
            )
        ).send()
        return

    # ── STATE: Awaiting language ────────────────────────────
    if cl.user_session.get("awaiting_language", False):
        lang = validate_language(msg_text)

        if not lang:
            logger.info("Unsupported language requested: %s", msg_text)
            await cl.Message(
                content=(
                    f"⚠️ **Sorry, we don't support \"{sanitize_for_output(msg_text)}\" yet.**\n\n"
                    f"We're working hard to add more languages soon!\n\n"
                    f"**Currently supported:**\n"
                    f"• {EXAMPLE_LANGUAGES}\n\n"
                    f"Please choose one of the supported languages."
                )
            ).send()
            return

        cl.user_session.set("target_language", lang)
        cl.user_session.set("awaiting_language", False)
        cl.user_session.set("awaiting_text", True)
        logger.info("Language selected: %s", lang)

        await cl.Message(
            content=(
                f"✅ **Language selected: {lang}**\n\n"
                f"Now enter the text you want to translate into **{lang}**."
            )
        ).send()
        return

    # ── STATE: Awaiting text ───────────────────────────────
    if cl.user_session.get("awaiting_text", False):
        target_language = cl.user_session.get("target_language")

        if not target_language:
            await cl.Message(
                content=(
                    "⚠️ No language selected.\n\n"
                    "Please enter a language first.\n\n"
                    f"**Examples:** {EXAMPLE_LANGUAGES}"
                )
            ).send()
            return

        session_id: str = cl.user_session.get("session_id", "unknown")
        chat_history: list[dict[str, str]] = cl.user_session.get("chat_history") or []
        user_input = f"Translate this into {target_language}: {msg_text}"
        chat_history.append({"role": "user", "content": user_input})

        # Persist user message
        save_message(session_id, "user", user_input, {"target_language": target_language})

        provider = cl.user_session.get("provider", DEFAULT_PROVIDER)
        provider_config = PROVIDERS[provider]

        msg = cl.Message(content=f"🔄 Translating to **{target_language}** via **{provider}**...")
        await msg.send()

        try:
            response = completion(
                model=provider_config["model"],
                api_key=provider_config["api_key"],
                messages=chat_history,
            )

            translated_text = response.choices[0].message.content.strip()
            safe_translation = sanitize_for_output(translated_text)

            msg.content = (
                f"🌐 **Translated to {target_language}:**\n\n"
                f"{safe_translation}"
            )
            await msg.update()

            chat_history.append({"role": "assistant", "content": translated_text})
            cl.user_session.set("chat_history", chat_history)

            # Persist assistant message
            save_message(session_id, "assistant", translated_text, {
                "provider": provider,
                "target_language": target_language,
            })
            logger.info("Translation completed: %s -> %s", provider, target_language)

            # Reset — fresh start for next translation
            cl.user_session.set("awaiting_language", True)
            cl.user_session.set("awaiting_text", False)
            cl.user_session.set("target_language", None)

            await cl.Message(
                content=(
                    "🌍 **Translation completed.**\n\n"
                    "Which language would you like to translate into next?\n\n"
                    f"**Examples:**\n{EXAMPLE_LANGUAGES}"
                )
            ).send()

        except Exception as e:
            error_msg = str(e).lower()
            logger.error("Translation error [%s]: %s", provider, str(e)[:200])

            # API-related errors
            api_keywords = [
                "429", "rate limit", "quota", "limit exceeded",
                "401", "unauthorized", "invalid", "authentication",
                "403", "forbidden", "404", "not found",
                "500", "502", "503", "server error",
                "connection", "timeout", "network",
                "api key", "billing", "payment",
            ]

            if any(kw in error_msg for kw in api_keywords):
                other_providers = [
                    p for p in PROVIDERS if p != provider and PROVIDERS[p]["api_key"]
                ]
                switch_options = (
                    ", ".join(f"`/model {p}`" for p in other_providers)
                    if other_providers
                    else "No other providers available"
                )

                msg.content = (
                    f"⚠️ **We're unable to connect to {provider} at the moment.**\n\n"
                    f"This could be due to API limits or service issues.\n\n"
                    f"**Please switch to another model to continue:**\n"
                    f"{switch_options}"
                )
                await msg.update()
            else:
                msg.content = (
                    "❌ **Something went wrong.**\n\n"
                    "Please try again or switch models using `/model gemini` or `/model openrouter`."
                )
                await msg.update()


# ─── Chat End ─────────────────────────────────────────────
@cl.on_chat_end
async def on_chat_end() -> None:
    session_id: str = cl.user_session.get("session_id", "unknown")
    chat_history: list[dict[str, str]] = cl.user_session.get("chat_history") or []
    logger.info("Session %s ended — %d messages in history", session_id, len(chat_history))
