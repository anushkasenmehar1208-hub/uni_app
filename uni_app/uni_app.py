from dotenv import load_dotenv
load_dotenv()

import os
import threading
import hashlib
import asyncio
import hmac
import json
import base64
import re
import secrets
from urllib.parse import unquote, urlencode, urlparse
from fastapi import Request
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from typing import Any, Optional

import reflex as rx
import httpx
from sqlmodel import Field, select, Column, DateTime, Date, String, func
from sqlalchemy import or_
from fastapi.responses import PlainTextResponse, RedirectResponse
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import reflex_local_auth
from reflex_local_auth import routes as auth_routes
from reflex_local_auth.local_auth import AUTH_TOKEN_LOCAL_STORAGE_KEY
from reflex_local_auth.auth_session import LocalAuthSession
from reflex_local_auth.user import LocalUser
from starlette.routing import Route
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse as StarletteRedirect


# ----------------------------
# Groq setup
# ----------------------------
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

GEMINI_FAST_MODEL = "llama-3.3-70b-versatile"
GEMINI_PRO_MODEL  = "llama-3.3-70b-versatile"
GEMINI_MODEL      = GEMINI_FAST_MODEL

RATE_LIMIT_UI_MESSAGE = "I'm taking a short break. Please try again in a few minutes."
GENERIC_ERROR_UI_MESSAGE = "Alex had a small error. Please try again."
STUDY_PLAN_TOTAL_DAYS = 110
SEMESTER_PROGRESS_SEGMENTS = 16


def _is_rate_limit_text(text: str) -> bool:
    low = (text or "").lower()
    if not low:
        return False
    markers = (
        "[stream error]",
        "error code: 429",
        "rate_limit_exceeded",
        "rate limit reached for model",
        "tokens per day (tpd)",
        "console.groq.com/settings/billing",
    )
    if any(marker in low for marker in markers):
        return True
    return "rate limit" in low and ("429" in low or "tpd" in low or "requested" in low)


def sanitize_for_ui(text: str) -> str:
    if _is_rate_limit_text(text):
        return RATE_LIMIT_UI_MESSAGE
    return text


def _normalize_person_name(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", (name or "").strip().lower())
    if not cleaned:
        return ""
    return re.sub(r"(^|[\s'-])([a-z])", lambda m: m.group(1) + m.group(2).upper(), cleaned)


def _extract_person_name(*texts: str) -> str:
    patterns = (
        r"\b(?:student name|name)\s*[:=-]\s*([A-Za-z][A-Za-z'-]*(?:\s+[A-Za-z][A-Za-z'-]*){0,2})\b",
        r"\b(?:hi|hello|hey)\s*,?\s*([A-Za-z][A-Za-z'-]*)\b(?=[,.!?]|$)",
        r"let'?s get started,\s*([A-Za-z][A-Za-z'-]*)\b(?=[,.!?]|$)",
        r"\bcall(?:ing)?\s+(?:the student\s+)?([A-Za-z][A-Za-z'-]*(?:\s+[A-Za-z][A-Za-z'-]*){0,2})\b(?=[,.!?]|$)",
    )
    for text in texts:
        raw = (text or "").strip()
        if not raw:
            continue
        normalized = _normalize_person_name(raw)
        if normalized and " " not in normalized and normalized.lower() not in {"student", "user"}:
            return normalized
        for pattern in patterns:
            match = re.search(pattern, raw, re.IGNORECASE)
            if not match:
                continue
            candidate = _normalize_person_name(match.group(1))
            if candidate and candidate.lower() not in {"student", "user"}:
                return candidate
    return ""


def friendly_groq_error(e: Exception) -> str:
    s = str(e)
    if _is_rate_limit_text(s) or " 429" in s.lower():
        return RATE_LIMIT_UI_MESSAGE
    return GENERIC_ERROR_UI_MESSAGE


def _groq_generate(model: str, contents: str, max_tokens: int = 2048) -> Any:
    """Drop-in replacement for Gemini generate_content using Groq."""
    class _R:
        def __init__(self):
            self.text = ""

    if client is None:
        r = _R()
        r.text = "API not ready"
        return r

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": contents}],
            max_tokens=max_tokens,
        )
        r = _R()
        r.text = resp.choices[0].message.content or ""
        return r
    except Exception as e:
        r = _R()
        r.text = friendly_groq_error(e)
        return r

async def _groq_stream_async(model: str, messages: list[dict], max_tokens: int = 2048):
    try:
        if client is None:
            yield "API not ready"
            return

        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()
        DONE = object()

        def worker():
            try:
                stream = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    if not delta:
                        continue
                    loop.call_soon_threadsafe(q.put_nowait, delta)

                loop.call_soon_threadsafe(q.put_nowait, DONE)

            except Exception as e:
                loop.call_soon_threadsafe(q.put_nowait, friendly_groq_error(e))
                loop.call_soon_threadsafe(q.put_nowait, DONE)

        threading.Thread(target=worker, daemon=True).start()

        while True:
            item = await q.get()
            if item is DONE:
                break
            if not isinstance(item, str):
                continue
            if _is_rate_limit_text(item):
                yield RATE_LIMIT_UI_MESSAGE
                break

            yield item

    except Exception as e:
        yield friendly_groq_error(e)

FREE_DAILY_LIMIT = 5
TRIAL_DAYS       = 3
ADAPTIVE_PROFILE_SCOPE = "__adaptive_profile__"
PLAN_GENERATION_STATUS_IDLE = "idle"
PLAN_GENERATION_STATUS_RUNNING = "running"
PLAN_GENERATION_STATUS_FAILED = "failed"
PLAN_GENERATION_STALE_AFTER = timedelta(minutes=10)
PLAN_GENERATION_FAILURE_TEXT = "Could not generate the study plan. Tap retry."
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{3,32}$")
PASSWORD_MIN_LEN = 8
ONBOARDING_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s'-]*$")
LOGIN_MAX_ATTEMPTS = max(10, int(os.getenv("LOGIN_MAX_ATTEMPTS", "10")))
LOGIN_LOCK_MINUTES = int(os.getenv("LOGIN_LOCK_MINUTES", "10"))
ENFORCE_HTTPS = os.getenv("ENFORCE_HTTPS", "true").lower() == "true"
FAVICON_ICO = "/brand-favicon-20260306.ico"
FAVICON_32 = "/brand-favicon-32-20260306.png"
FAVICON_16 = "/brand-favicon-16-20260306.png"
APPLE_TOUCH_ICON = "/brand-apple-touch-20260306.png"

APP_ROOT_DIR = Path(__file__).resolve().parent.parent
TRAINING_DATA_PATH = APP_ROOT_DIR / ".states" / "training_data.jsonl"
TRAINING_LOG_ENABLED = os.getenv("TRAINING_LOG_ENABLED", "false").lower() == "true"
TRAINING_MAX_BYTES = int(os.getenv("TRAINING_MAX_BYTES", "5242880"))


def _redact_training_text(text: str) -> str:
    t = text or ""
    # Remove likely emails and long number sequences before logging.
    t = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[email]", t)
    t = re.sub(r"\b\d{7,}\b", "[number]", t)
    return t


import fcntl

def _append_training_example(uid: int, scope: str, user_msg: str, assistant_msg: str) -> None:
    """Store anonymized chat examples for optional offline model tuning later."""
    if not TRAINING_LOG_ENABLED:
        return

    user_text = (user_msg or "").strip()
    assistant_text = (assistant_msg or "").strip()
    if not user_text or not assistant_text:
        return
    if assistant_text in (RATE_LIMIT_UI_MESSAGE, GENERIC_ERROR_UI_MESSAGE):
        return

    try:
        TRAINING_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        if TRAINING_DATA_PATH.exists() and TRAINING_DATA_PATH.stat().st_size >= TRAINING_MAX_BYTES:
            return
        anon_uid = hashlib.sha256(str(uid).encode()).hexdigest()[:16]
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "uid": anon_uid,
            "scope": (scope or "home")[:64],
            "user": _redact_training_text(user_text)[:1200],
            "assistant": _redact_training_text(assistant_text)[:2800],
        }
        with TRAINING_DATA_PATH.open("a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(json.dumps(row, ensure_ascii=True) + "\n")
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except Exception as e:
        print(f"ERROR training log append: {e}")

# ----------------------------
# PayHere configuration
# ----------------------------
PAYHERE_MERCHANT_ID     = os.getenv("PAYHERE_MERCHANT_ID", "").strip()
PAYHERE_MERCHANT_SECRET = os.getenv("PAYHERE_MERCHANT_SECRET", "").strip()
PAYHERE_SANDBOX         = os.getenv("PAYHERE_SANDBOX", "true").lower() == "true"
APP_BASE_URL            = os.getenv("APP_BASE_URL", "http://localhost:3000").rstrip("/")
API_BASE_URL            = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
GOOGLE_CLIENT_ID        = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET    = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_REDIRECT_URI     = os.getenv("GOOGLE_REDIRECT_URI", "").strip()
GOOGLE_OAUTH_ENABLED    = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
AUTH_SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 90
GOOGLE_COMPLETE_TOKEN_MAX_AGE_SECONDS = max(
    60, int(os.getenv("GOOGLE_COMPLETE_TOKEN_MAX_AGE_SECONDS", "600"))
)
APP_DASHBOARD_ROUTE = "/app"
BUSINESS_NAME = "Alex AI"
SUPPORT_EMAIL = "support.alexstudies@gmail.com"
SUPPORT_PHONE = "+94 767104776"
SUPPORT_PHONE_LINK = "tel:+94767104776"
BUSINESS_LOCATION = "Colombo, Sri Lanka"
CURRENT_COPYRIGHT_YEAR = str(date.today().year)
SESSION_SECRET          = os.getenv("SESSION_SECRET", "change-me-in-production").strip() or "change-me-in-production"
_IS_PRODUCTION = os.getenv("RAILWAY_ENVIRONMENT", "") or os.getenv("PRODUCTION", "")
if SESSION_SECRET == "change-me-in-production":
    if _IS_PRODUCTION:
        raise RuntimeError("SESSION_SECRET must be set in production! Set a real secret via environment variable.")
    print("WARNING: SESSION_SECRET is set to the default value. Set a real secret in production!")
GOOGLE_AUTH_URL         = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL        = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL     = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_STATE_MAX_AGE_SECONDS = 600
GOOGLE_STRICT_STATE     = os.getenv("GOOGLE_STRICT_STATE", "false").lower() == "true"
_google_state_serializer = URLSafeTimedSerializer(SESSION_SECRET, salt="google-oauth-state")

PAYHERE_CHECKOUT_URL = (
    "https://sandbox.payhere.lk/pay/checkout"
    if PAYHERE_SANDBOX
    else "https://www.payhere.lk/pay/checkout"
)

PLANS = {
    1: {
        "name":   "Alex AI — Premium",
        "amount": 200.00,
        "label":  "⚡ Premium",
        "model":  GEMINI_FAST_MODEL,
    },
}


def _request_is_https(request: Request) -> bool:
    proto = (request.headers.get("x-forwarded-proto") or request.url.scheme or "").split(",")[0].strip().lower()
    return proto == "https"


def _is_local_host(host: str) -> bool:
    h = (host or "").split(":")[0].strip().lower()
    return h in {"localhost", "127.0.0.1", "0.0.0.0"} or h.endswith(".local")


def _google_callback_url(request: Request) -> str:
    configured = (GOOGLE_REDIRECT_URI or "").strip()
    if configured:
        configured_host = (urlparse(configured).hostname or "").lower()
        request_host = (
            (request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc)
            .split(",")[0]
            .strip()
            .lower()
        )
        # Ignore localhost callback URIs when request host is deployed.
        if not (_is_local_host(configured_host) and request_host and not _is_local_host(request_host)):
            return configured
    proto = (request.headers.get("x-forwarded-proto") or request.url.scheme or "http").split(",")[0].strip().lower()
    host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc).split(",")[0].strip()
    return f"{proto}://{host}/auth/google/callback"


def _frontend_base_url(request: Request) -> str:
    """Resolve frontend origin safely for local + deployed environments."""
    configured = (APP_BASE_URL or "").strip().rstrip("/")
    proto = (request.headers.get("x-forwarded-proto") or request.url.scheme or "http").split(",")[0].strip().lower()
    host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc).split(",")[0].strip()
    host_only = (host.split(":")[0] if host else "").lower()
    host_is_local = _is_local_host(host_only)

    configured_host = (urlparse(configured).hostname or "").lower() if configured else ""
    config_is_local = (not configured_host) or _is_local_host(configured_host)
    if configured and not config_is_local:
        # Keep browser on the same deployed host during auth flows to avoid cross-domain token storage.
        if host and (not host_is_local) and host_only != configured_host:
            return f"{proto}://{host}"
        return configured

    if host and (not host_is_local):
        return f"{proto}://{host}"
    return configured or "http://localhost:3001"


def _google_username_from_sub(sub: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "", sub or "")
    if not cleaned:
        cleaned = secrets.token_hex(8)
    return f"google_{cleaned}"[:255]


def _google_make_state() -> str:
    return _google_state_serializer.dumps({"n": secrets.token_urlsafe(12)})


def _google_state_is_valid(state: str) -> bool:
    if not state:
        return False
    try:
        _google_state_serializer.loads(state, max_age=GOOGLE_STATE_MAX_AGE_SECONDS)
        return True
    except (BadSignature, SignatureExpired):
        return False


def _normalized_origin(origin: str) -> str:
    parsed = urlparse((origin or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def _decode_urlsafe_b64_text(value: str) -> str:
    encoded = (value or "").strip()
    if not encoded:
        return ""
    try:
        pad = "=" * (-len(encoded) % 4)
        return base64.urlsafe_b64decode(encoded + pad).decode("utf-8")
    except Exception:
        return ""


def _id_token_payload(id_token: str) -> dict[str, Any]:
    parts = (id_token or "").split(".")
    if len(parts) < 2:
        return {}
    payload_b64 = parts[1]
    pad = "=" * (-len(payload_b64) % 4)
    try:
        raw = base64.urlsafe_b64decode(payload_b64 + pad)
        parsed = json.loads(raw.decode("utf-8"))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


# ----------------------------
# PayHere hash helpers
# ----------------------------
def _ph_secret_hash() -> str:
    return hashlib.md5(PAYHERE_MERCHANT_SECRET.encode()).hexdigest().upper()


def _generate_ph_hash(order_id: str, amount: float, currency: str = "LKR") -> str:
    secret_hash = _ph_secret_hash()
    amount_str  = f"{amount:.2f}"
    raw         = f"{PAYHERE_MERCHANT_ID}{order_id}{amount_str}{currency}{secret_hash}"
    return hashlib.md5(raw.encode()).hexdigest().upper()


def _verify_ph_notify(
    merchant_id: str, order_id: str, amount: str,
    currency: str, status_code: str, md5sig: str
) -> bool:
    secret_hash = _ph_secret_hash()
    raw = f"{merchant_id}{order_id}{amount}{currency}{status_code}{secret_hash}"
    expected = hashlib.md5(raw.encode()).hexdigest().upper()
    return hmac.compare_digest(expected, md5sig.upper())


# ----------------------------
# Curriculum
# ----------------------------
FULL_CURRICULUM = {
    "Year 1": {
        "Semester 1": [
            "SENG:Fundamentals of Computing",
            "SENG:Programming Concepts",
            "SENG:Engineering Foundation",
            "SENG:Statistics",
            "PMAT:Discrete Mathematics for Computing I"
        ],
        "Semester 2": [
            "SENG:Data Structures and Algorithms",
            "SENG:Database Design and Development",
            "SENG:Object-Oriented Programming",
            "SENG:Management for Software Engineering I",
            "PMAT:Discrete Mathematics for Computing II",
        ],
    },
    "Year 2": {
        "Semester 3": [
            "SENG:Computer Architecture and Operating Systems",
            "SENG:Software Construction",
            "SENG:Requirement Engineering",
            "SENG:Software Modeling",
            "SENG:Web Application Development",
            "SENG:Interactive Application Development",
            "SENG:Management for Software Engineering II"
        ],
        "Semester 4": [
            "SENG:Computer Networks",
            "SENG:Software Architecture and Design",
            "SENG:Human-Computer Interaction",
            "SENG:Software Verification and Validation",
            "SENG:Mobile Application Development",
            "SENG:Embedded Systems Development",
            "PMAT:Mathematical Methods",
        ],
    },
}

SEMESTER_NAVIGATION = {
    "Year 1": ["Semester 1", "Semester 2"],
    "Year 2": ["Semester 3", "Semester 4"],
    "Year 3": ["Semester 5", "Semester 6"],
    "Year 4": ["Semester 7", "Semester 8"],
}

# ── Route-based scope mapping ──
# Each scope gets its own URL so navigation = full page reload = no stale state.
SCOPE_ROUTE_MAP: dict[str, dict[str, str]] = {}
for _yr_label, _semesters in SEMESTER_NAVIGATION.items():
    _yr_num = _yr_label.replace("Year ", "").strip()
    for _sem_label in _semesters:
        _sem_num = _sem_label.replace("Semester ", "").strip()
        _scope_key = f"y{_yr_num}s{_sem_num}"
        SCOPE_ROUTE_MAP[_scope_key] = {
            "route": f"/s/{_scope_key}",
            "year": _yr_label,
            "semester": _sem_label,
            "view_mode": "semester",
        }
SCOPE_ROUTE_MAP["home"] = {
    "route": "/s/home",
    "year": "",
    "semester": "",
    "view_mode": "home",
}


def scope_to_route(scope_key: str) -> str:
    """Convert a scope key like 'y1s2' to its page route like '/s/y1s2'."""
    entry = SCOPE_ROUTE_MAP.get(scope_key or "home")
    return entry["route"] if entry else "/s/home"


def semester_scope_key(year: str, semester: str) -> str:
    y = year.lower().replace("year", "").strip()
    s = semester.lower().replace("semester", "").strip()
    if y.isdigit() and s.isdigit():
        return f"y{y}s{s}"
    return f"{year}|{semester}"


def _hard_navigate(route: str):
    """Force a full browser navigation — guarantees fresh WebSocket + state."""
    return rx.call_script(f"window.location.href = {json.dumps(route)}")

ONBOARDING_FINAL_STEP = 5


# ----------------------------
# Database models
# ----------------------------
class ChatMessage(rx.Model, table=True):  # type: ignore
    user_id: int = Field(index=True, nullable=False)
    role: str = Field(nullable=False)
    content: str = Field(nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )


class ChatSession(rx.Model, table=True):  # type: ignore
    user_id: int = Field(index=True, nullable=False)
    scope: str = Field(index=True, default="default", nullable=False)
    title: str = Field(default="New chat", nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )


class ChatMessage2(rx.Model, table=True):  # type: ignore
    user_id: int = Field(index=True, nullable=False)
    session_id: int = Field(index=True, nullable=False)
    role: str = Field(nullable=False)
    content: str = Field(nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )


class StudyProgress(rx.Model, table=True):  # type: ignore
    user_id: int = Field(index=True, nullable=False)
    year: str = Field(index=True, nullable=False)
    semester: str = Field(nullable=False)
    course: str = Field(nullable=False)
    order_index: int = Field(nullable=False, default=0)
    status: str = Field(nullable=False, default="not_started")
    last_done_at: Optional[datetime] = Field(default=None, nullable=True)
    notes: str = Field(default="", nullable=False)
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )


class UserMemory(rx.Model, table=True):  # type: ignore
    user_id: int = Field(index=True, unique=True, nullable=False)
    step: int = 0
    name: str = ""
    degree: str = ""
    is_started: bool = False
    selected_year: str = ""
    selected_semester: str = ""
    summary: str = ""
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )


class ScopeMemory(rx.Model, table=True):  # type: ignore
    user_id: int = Field(index=True, nullable=False)
    scope: str = Field(index=True, nullable=False)
    summary: str = Field(default="", nullable=False)
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )


class SemesterStudyPlan(rx.Model, table=True):  # type: ignore
    user_id: int = Field(index=True, nullable=False)
    scope: str = Field(index=True, nullable=False)
    plan_json: str = Field(default="", nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )


class SemesterPlanGenerationState(rx.Model, table=True):  # type: ignore
    user_id: int = Field(index=True, nullable=False)
    scope: str = Field(index=True, nullable=False)
    status: str = Field(default=PLAN_GENERATION_STATUS_IDLE, nullable=False)
    error_message: str = Field(default="", nullable=False)
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )


class DayProgress(rx.Model, table=True):  # type: ignore
    user_id: int = Field(index=True, nullable=False)
    scope: str = Field(index=True, nullable=False)
    current_day: int = Field(default=1, nullable=False)
    current_topic_index: int = Field(default=0, nullable=False)
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )


class UserProfile(rx.Model, table=True):  # type: ignore
    user_id: int = Field(index=True, unique=True, nullable=False)
    is_onboarded: bool = False
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    is_premium_1: bool = Field(default=False, nullable=False)
    is_premium_2: bool = Field(default=False, nullable=False)
    daily_message_count: int = Field(default=0, nullable=False)
    last_message_date: Optional[date] = Field(
        default=None,
        sa_column=Column(Date, nullable=True),
    )


class AuthThrottle(rx.Model, table=True):  # type: ignore
    key: str = Field(
        unique=True,
        nullable=False,
        index=True,
        sa_type=String(255),  # pyright: ignore[reportArgumentType]
    )
    failed_attempts: int = Field(default=0, nullable=False)
    locked_until: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    last_failed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )


class PaymentOrder(rx.Model, table=True):  # type: ignore
    user_id: int = Field(index=True, nullable=False)
    order_id: str = Field(unique=True, nullable=False, index=True)
    plan: int = Field(nullable=False)
    amount: float = Field(nullable=False)
    currency: str = Field(default="LKR", nullable=False)
    status: str = Field(default="pending", nullable=False)
    payhere_payment_id: str = Field(default="", nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )


# ----------------------------
# PayHere notify webhook
# ----------------------------
async def payhere_notify(request: Request) -> PlainTextResponse:
    try:
        form = await request.form()

        merchant_id    = str(form.get("merchant_id", ""))
        order_id       = str(form.get("order_id", ""))
        payhere_amount = str(form.get("payhere_amount", ""))
        currency       = str(form.get("payhere_currency", "LKR"))
        status_code    = str(form.get("status_code", ""))
        md5sig         = str(form.get("md5sig", ""))

        if not _verify_ph_notify(merchant_id, order_id, payhere_amount, currency, status_code, md5sig):
            print(f"[PayHere] ❌ Invalid signature for order {order_id}")
            return PlainTextResponse("invalid signature", status_code=400)

        with rx.session() as session:
            order = session.exec(
                select(PaymentOrder).where(PaymentOrder.order_id == order_id)
            ).one_or_none()

            if order is None:
                print(f"[PayHere] ❌ Unknown order_id: {order_id}")
                return PlainTextResponse("order not found", status_code=404)

            payment_id = str(form.get("payment_id", ""))

            if status_code == "2":
                order.status = "completed"
                order.payhere_payment_id = payment_id
                session.add(order)

                profile = session.exec(
                    select(UserProfile).where(UserProfile.user_id == order.user_id)
                ).one_or_none()

                if profile:
                    if order.plan in PLANS or order.plan == 2:
                        profile.is_premium_1 = True
                        profile.is_premium_2 = False
                        print(f"[PayHere] ✅ Activated Premium for user {order.user_id}")
                    session.add(profile)

                session.commit()

            elif status_code in ("-1", "-2", "-3"):
                order.status = "failed"
                order.payhere_payment_id = payment_id
                session.add(order)
                session.commit()
                print(f"[PayHere] ❌ Payment failed/cancelled for order {order_id} (code {status_code})")

            else:
                print(f"[PayHere] ℹ️ Status {status_code} for order {order_id}")

        return PlainTextResponse("OK", status_code=200)

    except Exception as e:
        print(f"[PayHere] 🔥 notify error: {e}")
        return PlainTextResponse("server error", status_code=500)
    
async def health_check(request):
    try:
        with rx.session() as session:
            session.exec(select(UserProfile).limit(1))
        return PlainTextResponse("OK")
    except Exception as e:
        return PlainTextResponse(f"error: {e}", status_code=500)


# ============================
# App State
# ============================
class AppState(reflex_local_auth.LocalAuthState):
    app_auth_token: str = rx.LocalStorage(name=AUTH_TOKEN_LOCAL_STORAGE_KEY)
    auth_csrf_token: str = rx.SessionStorage(name="auth_csrf_token")
    post_login_redirect: str = ""
    root_public_ready: bool = False
    plan_generation_error: str = ""
    login_error: str = ""
    register_error: str = ""
    register_success: bool = False
    reset_error: str = ""
    reset_success: bool = False

    options: list[str] = ["Software Engineering"]
    step: int = 0
    name: str = ""
    degree: str = ""
    is_started: bool = False

    streak: int = 1
    selected_year: str = ""
    selected_semester: str = ""
    view_mode: str = "semester"
    active_scope: str = ""

    status_text: str = ""
    onboarding_message: str = ""
    show_semester_sidebar: bool = False

    sessions: list[dict] = []
    current_session_id: str = ""
    current_session_choice: str = ""

    today_plan: str = ""
    memory_summary: str = ""
    adaptive_profile: str = ""

    chat_history: list[dict] = []
    chat_input: str = ""
    is_processing: bool = False

    is_generating_plan: bool = False
    scope_hydrating: bool = False
    current_day: int = 1
    current_topic_index: int = 0

    profile_created_at: str = ""
    is_premium_1: bool = False
    is_premium_2: bool = False
    daily_message_count: int = 0
    last_message_date: str = ""

    show_pricing_modal: bool = False
    payment_processing: bool = False
    payment_error: str = ""

    _cached_uid: int = -1

    @rx.var
    def is_authenticated_now(self) -> bool:
        return self._cached_uid >= 0

    @rx.var
    def has_selected_environment(self) -> bool:
        return bool(self.selected_year and self.selected_semester)

    @rx.var
    def is_home_scope_active(self) -> bool:
        return self.active_scope == "home" and self.view_mode == "home"

    @staticmethod
    def is_semester_scope_active(year: str, semester: str):
        return (AppState.view_mode == "semester") & (AppState.active_scope == semester_scope_key(year, semester))

    # ----------------------------------------------------------------
    # NEW: is_empty_chat — True when no real conversation has started
    # Only assistant welcome messages = still "empty" state
    # ----------------------------------------------------------------
    @rx.var
    def is_empty_chat(self) -> bool:
        if len(self.chat_history) == 0:
            return True
        # Check if all messages are assistant-only (no user message yet)
        for msg in self.chat_history:
            if msg.get("role") == "user":
                return False
        return True

    @rx.var
    def days_since_registration(self) -> int:
        if not self.profile_created_at:
            return 999
        try:
            created = datetime.fromisoformat(self.profile_created_at)
            now = datetime.now(timezone.utc)
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            return (now - created).days
        except Exception:
            return 999

    @rx.var
    def has_premium_access(self) -> bool:
        return self.is_premium_1 or self.is_premium_2

    @rx.var
    def is_in_trial(self) -> bool:
        return self.days_since_registration < TRIAL_DAYS

    @rx.var
    def trial_days_left(self) -> int:
        return max(0, TRIAL_DAYS - self.days_since_registration)

    @rx.var
    def can_send_message(self) -> bool:
        if self.has_premium_access:
            return True
        if self.is_in_trial:
            return True
        return self.daily_message_count < FREE_DAILY_LIMIT

    @rx.var
    def messages_left_today(self) -> int:
        if self.has_premium_access or self.is_in_trial:
            return 999  # Unlimited
        return max(0, FREE_DAILY_LIMIT - self.daily_message_count)

    @rx.var
    def active_model_name(self) -> str:
        return GEMINI_FAST_MODEL

    @rx.var
    def tier_label(self) -> str:
        if self.has_premium_access:
            return "⚡ Premium"
        if self.is_in_trial:
            return f"Trial ({self.trial_days_left}d left)"
        return "🔒 Free"
    
    @rx.var
    def semester_short_label(self) -> str:
        y = self.selected_year.replace("Year ", "").strip()
        s = self.selected_semester.replace("Semester ", "").strip()
        return f"{y}:{s}"

    @rx.var
    def semester_status_label(self) -> str:
        parts = [p for p in [self.selected_year, self.selected_semester] if p]
        return " • ".join(parts)

    @rx.var
    def semester_progress_label(self) -> str:
        day = max(1, min(self.current_day, STUDY_PLAN_TOTAL_DAYS))
        return f"Day {day} / {STUDY_PLAN_TOTAL_DAYS}"

    @rx.var
    def semester_progress_filled_segments(self) -> int:
        day = max(0, min(self.current_day, STUDY_PLAN_TOTAL_DAYS))
        if day <= 0:
            return 0
        filled = (day * SEMESTER_PROGRESS_SEGMENTS + STUDY_PLAN_TOTAL_DAYS - 1) // STUDY_PLAN_TOTAL_DAYS
        return min(SEMESTER_PROGRESS_SEGMENTS, max(1, filled))

    @rx.var
    def semester_progress_bar_filled(self) -> str:
        return "█" * self.semester_progress_filled_segments

    @rx.var
    def semester_progress_bar_empty(self) -> str:
        return "░" * max(0, SEMESTER_PROGRESS_SEGMENTS - self.semester_progress_filled_segments)

    @rx.var
    def account_display_name(self) -> str:
        return _normalize_person_name(getattr(self.authenticated_user, "username", ""))

    @rx.var
    def inferred_name(self) -> str:
        recent_messages = [
            str(msg.get("content", ""))
            for msg in list(self.chat_history or [])[-6:]
        ]
        return _extract_person_name(
            self.name,
            self.account_display_name,
            self.memory_summary,
            self.adaptive_profile,
            *recent_messages,
        )

    @rx.var
    def display_name(self) -> str:
        return self.inferred_name

    @rx.var
    def greeting_text(self) -> str:
        return "Hi, " + self.display_name if self.display_name else "Hi"

    def _load_profile(self, uid: int) -> None:
        if uid < 0:
            return
        with rx.session() as session:
            profile = session.exec(
                select(UserProfile).where(UserProfile.user_id == uid)
            ).one_or_none()
            if profile is None:
                profile = UserProfile(user_id=uid)  # type: ignore
                session.add(profile)
                session.commit()
                session.refresh(profile)

            self.profile_created_at  = profile.created_at.isoformat()
            self.is_premium_1         = bool(profile.is_premium_1)
            self.is_premium_2         = bool(profile.is_premium_2)
            self.daily_message_count  = profile.daily_message_count or 0
            self.last_message_date    = (
                profile.last_message_date.isoformat()
                if profile.last_message_date else ""
            )

            memory = session.exec(
                select(UserMemory).where(UserMemory.user_id == uid)
            ).one_or_none()
            if memory is not None:
                self.step = int(memory.step or 0)
                self.name = _normalize_person_name(memory.name)
                self.degree = memory.degree or ""
                self.is_started = bool(memory.is_started)
                self.selected_year = memory.selected_year or ""
                self.selected_semester = memory.selected_semester or ""
                self.memory_summary = memory.summary or ""
            if not (self.name or "").strip():
                account = session.exec(
                    select(LocalUser).where(LocalUser.id == uid)
                ).one_or_none()
                if account is not None:
                    self.name = _normalize_person_name(account.username)

    def _check_and_reset_daily_count(self, uid: int) -> None:
        today_str = datetime.now(timezone.utc).date().isoformat()
        if self.last_message_date != today_str:
            self.daily_message_count = 0
            self.last_message_date   = today_str
            with rx.session() as session:
                profile = session.exec(
                    select(UserProfile).where(UserProfile.user_id == uid)
                ).one_or_none()
                if profile:
                    profile.daily_message_count = 0
                    profile.last_message_date   = datetime.now(timezone.utc).date()
                    session.add(profile)
                    session.commit()

    def _increment_daily_count(self, uid: int) -> None:
        today = datetime.now(timezone.utc).date()
        self.last_message_date = today.isoformat()
        with rx.session() as session:
            profile = session.exec(
                select(UserProfile).where(UserProfile.user_id == uid)
            ).one_or_none()
            if profile:
                # Use the DB value as source of truth to avoid race conditions
                profile.daily_message_count = (profile.daily_message_count or 0) + 1
                profile.last_message_date = today
                session.add(profile)
                session.commit()
                self.daily_message_count = profile.daily_message_count
            else:
                self.daily_message_count += 1

    def _normalize_username(self, username: str) -> str:
        return (username or "").strip().lower()

    def _is_valid_username(self, username: str) -> bool:
        return bool(USERNAME_PATTERN.fullmatch(username or ""))

    def _is_valid_password(self, password: str) -> bool:
        p = password or ""
        if len(p) < PASSWORD_MIN_LEN:
            return False
        return any(c.islower() for c in p) and any(c.isupper() for c in p) and any(c.isdigit() for c in p)

    def _auth_guard_keys(self, normalized_username: str) -> list[str]:
        keys = [f"user:{normalized_username}"]
        ip = (self.router.session.client_ip or "").strip()
        if ip:
            keys.append(f"ip:{ip}")
        return keys

    def _is_login_locked(self, normalized_username: str) -> bool:
        now = datetime.now(timezone.utc)
        keys = self._auth_guard_keys(normalized_username)
        try:
            with rx.session() as session:
                rows = session.exec(select(AuthThrottle).where(AuthThrottle.key.in_(keys))).all()
            for row in rows:
                locked_until = row.locked_until
                if locked_until and locked_until.tzinfo is None:
                    locked_until = locked_until.replace(tzinfo=timezone.utc)
                if locked_until and locked_until > now:
                    return True
        except Exception as e:
            print(f"ERROR login lock check: {e}")
        return False

    def _record_login_failure(self, normalized_username: str) -> None:
        now = datetime.now(timezone.utc)
        lock_until = now + timedelta(minutes=LOGIN_LOCK_MINUTES)
        try:
            with rx.session() as session:
                for key in self._auth_guard_keys(normalized_username):
                    row = session.exec(select(AuthThrottle).where(AuthThrottle.key == key)).one_or_none()
                    if row is None:
                        row = AuthThrottle(key=key)  # type: ignore

                    row_locked_until = row.locked_until
                    if row_locked_until and row_locked_until.tzinfo is None:
                        row_locked_until = row_locked_until.replace(tzinfo=timezone.utc)
                    if row_locked_until and row_locked_until > now:
                        session.add(row)
                        continue

                    row.failed_attempts = (row.failed_attempts or 0) + 1
                    row.last_failed_at = now
                    if row.failed_attempts >= LOGIN_MAX_ATTEMPTS:
                        row.failed_attempts = 0
                        row.locked_until = lock_until
                    session.add(row)
                session.commit()
        except Exception as e:
            print(f"ERROR login failure record: {e}")

    def _clear_login_failures(self, normalized_username: str) -> None:
        keys = self._auth_guard_keys(normalized_username)
        try:
            with rx.session() as session:
                rows = session.exec(select(AuthThrottle).where(AuthThrottle.key.in_(keys))).all()
                for row in rows:
                    row.failed_attempts = 0
                    row.locked_until = None
                    session.add(row)
                session.commit()
        except Exception as e:
            print(f"ERROR login failure clear: {e}")

    def _ensure_auth_csrf(self) -> None:
        if not self.auth_csrf_token:
            self.auth_csrf_token = secrets.token_urlsafe(24)

    def _csrf_ok(self, form_data: dict[str, Any]) -> bool:
        token = str(form_data.get("csrf_token", "") or "")
        expected = self.auth_csrf_token or ""
        if not token or not expected:
            return False
        return hmac.compare_digest(token, expected)
    
    @rx.event
    def init_auth_forms(self):
        self._ensure_auth_csrf()
        self.login_error = ""
        self.register_error = ""
        self.reset_error = ""

    @rx.event
    def auth_redir(self):
        if not self.is_hydrated:
            return AppState.auth_redir()  # type: ignore
        current_route = self.router.url.path
        is_authed = self._uid() >= 0
        if not is_authed and current_route != auth_routes.LOGIN_ROUTE:
            self.post_login_redirect = current_route
            return rx.redirect(auth_routes.LOGIN_ROUTE)
        if is_authed and current_route in (
            auth_routes.LOGIN_ROUTE,
            auth_routes.REGISTER_ROUTE,
            "/reset-password",
        ):
            return rx.redirect(self.post_login_redirect or APP_DASHBOARD_ROUTE)

    def _authenticated_landing_route(self) -> str:
        if self.selected_year and self.selected_semester:
            target_scope = self._scope_key(self.selected_year, self.selected_semester)
            if target_scope in SCOPE_ROUTE_MAP:
                return scope_to_route(target_scope)
        if self.is_started:
            return scope_to_route("home")
        return APP_DASHBOARD_ROUTE

    def _preload_root_workspace_target(self, uid: int) -> str:
        if uid < 0:
            return APP_DASHBOARD_ROUTE
        try:
            with rx.session() as session:
                memory = session.exec(
                    select(UserMemory).where(UserMemory.user_id == uid)
                ).one_or_none()
        except Exception as e:
            print(f"[ROOT] preload memory error: {e}")
            return APP_DASHBOARD_ROUTE

        if memory is not None:
            self.step = int(memory.step or 0)
            self.degree = memory.degree or self.degree
            self.is_started = bool(memory.is_started)
            self.selected_year = memory.selected_year or ""
            self.selected_semester = memory.selected_semester or ""

        target_route = self._authenticated_landing_route()
        if target_route == scope_to_route("home"):
            self.view_mode = "home"
            self.active_scope = "home"
        elif target_route.startswith("/s/") and self.selected_year and self.selected_semester:
            self.view_mode = "semester"
            self.active_scope = self._scope_key(self.selected_year, self.selected_semester)
        return target_route

    @rx.event
    async def on_load_public_landing(self):
        self.root_public_ready = False
        if not self.is_hydrated:
            yield AppState.on_load_public_landing()  # type: ignore
            return

        uid = self._uid()
        self._cached_uid = uid
        if uid < 0:
            self.root_public_ready = True
            return

        try:
            target_route = self._preload_root_workspace_target(uid)
        except Exception as e:
            print(f"[ROOT] landing redirect load error: {e}")
            target_route = APP_DASHBOARD_ROUTE
        yield rx.redirect(target_route)

    @rx.event
    def handle_login(self, form_data: dict[str, Any]):
        self._ensure_auth_csrf()
        self.login_error = ""
        generic_error = "Login failed. Check credentials and try again."

        if not self._csrf_ok(form_data):
            self.login_error = "Session expired. Refresh and try again."
            return

        username = self._normalize_username(str(form_data.get("username", "")))
        password = str(form_data.get("password", ""))
        if not username or not password or not self._is_valid_username(username):
            self.login_error = generic_error
            return [rx.set_value("password", ""), rx.set_focus("username")]

        if self._is_login_locked(username):
            self.login_error = "Too many failed attempts. Please wait and try again."
            return [rx.set_value("password", "")]

        with rx.session() as session:
            user = session.exec(
                select(LocalUser).where(func.lower(LocalUser.username) == username)
            ).one_or_none()

        if (
            user is None
            or user.id is None
            or (not user.enabled)
            or (not password)
            or (not user.verify(password))
        ):
            self._record_login_failure(username)
            self.login_error = generic_error
            return [rx.set_value("password", ""), rx.set_focus("password")]

        self._clear_login_failures(username)
        self._login(int(user.id))
        self._cached_uid = int(user.id)
        self.app_auth_token = self.auth_token
        self.login_error = ""
        self.auth_csrf_token = secrets.token_urlsafe(24)
        return AppState.auth_redir()  # type: ignore

    def _router_origin(self) -> str:
        origin_header = ""
        try:
            origin_header = str((self.router.headers or {}).get("origin", "") or "").strip()
        except Exception:
            origin_header = ""
        normalized = _normalized_origin(origin_header)
        if normalized:
            return normalized

        host = ""
        try:
            host = str(getattr(self.router.page, "host", "") or "").strip()
        except Exception:
            host = ""
        if host:
            host_only = host.split(":")[0].strip().lower()
            proto = "http" if _is_local_host(host_only) else "https"
            return f"{proto}://{host}"

        fallback = _normalized_origin(APP_BASE_URL)
        return fallback or "http://localhost:3001"

    @rx.event
    def start_google_oauth(self):
        self._ensure_auth_csrf()
        if not GOOGLE_OAUTH_ENABLED:
            return rx.redirect(auth_routes.LOGIN_ROUTE)
        origin = self._router_origin().rstrip("/")
        callback_url = f"{origin}/auth/google/callback"
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": "openid email profile",
            "state": _google_make_state(),
            "prompt": "select_account",
        }
        auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
        return rx.call_script(f"window.location.assign({json.dumps(auth_url)});")

    @rx.event
    async def handle_google_oauth_callback(self):
        code = unquote(str(self.router.page.params.get("code", "") or "")).strip()
        state = unquote(str(self.router.page.params.get("state", "") or "")).strip()
        origin_b64 = str(self.router.page.params.get("origin_b64", "") or "").strip()

        if not code or not _google_state_is_valid(state):
            yield rx.redirect(f"{auth_routes.LOGIN_ROUTE}?oauth_error=1")
            return

        origin = _normalized_origin(_decode_urlsafe_b64_text(origin_b64)) or self._router_origin()
        redirect_uri = f"{origin.rstrip('/')}/auth/google/callback"

        try:
            async with httpx.AsyncClient(timeout=20.0) as client_http:
                token_resp = await client_http.post(
                    GOOGLE_TOKEN_URL,
                    data={
                        "code": code,
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    headers={"Accept": "application/json"},
                )
                token_resp.raise_for_status()
                token_payload = token_resp.json() or {}

                access_token = str(token_payload.get("access_token", "") or "")
                id_token_val = str(token_payload.get("id_token", "") or "")
                userinfo: dict[str, Any] = {}

                if access_token:
                    try:
                        userinfo_resp = await client_http.get(
                            GOOGLE_USERINFO_URL,
                            headers={"Authorization": f"Bearer {access_token}"},
                        )
                        userinfo_resp.raise_for_status()
                        userinfo_raw = userinfo_resp.json() or {}
                        if isinstance(userinfo_raw, dict):
                            userinfo = userinfo_raw
                    except Exception:
                        userinfo = _id_token_payload(id_token_val)
                else:
                    userinfo = _id_token_payload(id_token_val)

            subject = str((userinfo or {}).get("sub", "")).strip()
            if not subject:
                raise ValueError("Google userinfo missing subject.")

            username = _google_username_from_sub(subject)
            with rx.session() as session:
                user = session.exec(
                    select(LocalUser).where(func.lower(LocalUser.username) == username.lower())
                ).one_or_none()

                if user is None:
                    user = LocalUser(
                        username=username,
                        password_hash=LocalUser.hash_password(secrets.token_urlsafe(40)),
                        enabled=True,
                    )
                    session.add(user)
                    session.commit()
                    session.refresh(user)

                if user.id is None:
                    raise ValueError("Unable to create a valid local user for Google login.")

                resolved_uid = int(user.id)
        except Exception as e:
            print(f"[Google OAuth Frontend] ERROR: {e}")
            yield rx.redirect(f"{auth_routes.LOGIN_ROUTE}?oauth_error=1")
            return

        self._login(resolved_uid)
        self._cached_uid = resolved_uid
        self.app_auth_token = self.auth_token
        self.login_error = ""
        self.auth_csrf_token = secrets.token_urlsafe(24)
        new_token = self.auth_token

        yield rx.call_script(
            f"""
        (function() {{
            try {{
                localStorage.setItem({json.dumps(AUTH_TOKEN_LOCAL_STORAGE_KEY)}, {json.dumps(new_token)});
            }} catch(e) {{}}
            setTimeout(function() {{ window.location.replace('/'); }}, 60);
        }})();
        """
        )
    
    @rx.event
    async def handle_google_complete(self):
        token = self.router.page.params.get("token", "")
        print(f"[Google Complete] token present: {bool(token)}")

        if not token:
            yield rx.redirect(auth_routes.LOGIN_ROUTE)
            return

        resolved_uid: int | None = None
        try:
            with rx.session() as db:
                auth_sess = db.exec(
                    select(LocalAuthSession).where(
                        LocalAuthSession.session_id == token,
                        LocalAuthSession.expiration >= datetime.now(timezone.utc)
                    )
                ).one_or_none()
                if auth_sess and auth_sess.user_id is not None:
                    resolved_uid = int(auth_sess.user_id)
        except Exception as e:
            print(f"[Google Complete] DB error: {e}")
            yield rx.redirect(auth_routes.LOGIN_ROUTE)
            return

        if resolved_uid is None:
            print("[Google Complete] session not found in DB")
            yield rx.redirect(auth_routes.LOGIN_ROUTE)
            return

        print(f"[Google Complete] found session uid={resolved_uid}, logging in...")
        self._login(resolved_uid)
        self._cached_uid = resolved_uid
        self.app_auth_token = self.auth_token
        new_token = self.auth_token

        # One-time use token: consume AFTER successful login to allow retry on failure.
        try:
            with rx.session() as db:
                auth_sess = db.exec(
                    select(LocalAuthSession).where(
                        LocalAuthSession.session_id == token,
                    )
                ).one_or_none()
                if auth_sess:
                    db.delete(auth_sess)
                    db.commit()
        except Exception as e:
            print(f"[Google Complete] token cleanup error: {e}")

        print("[Google Complete] login done, navigating home...")

    # Set localStorage directly via JS THEN navigate — avoids async race condition
        yield rx.call_script(f"""
    (function() {{
        try {{
            localStorage.setItem({json.dumps(AUTH_TOKEN_LOCAL_STORAGE_KEY)}, {json.dumps(new_token)});
        }} catch(e) {{}}
        setTimeout(function() {{ window.location.replace('/'); }}, 150);
    }})();
    """)
    @rx.event
    def handle_registration(self, form_data: dict[str, Any]):
        self._ensure_auth_csrf()
        self.register_error = ""
        self.register_success = False

        if not self._csrf_ok(form_data):
            self.register_error = "Session expired. Refresh and try again."
            return

        username = self._normalize_username(str(form_data.get("username", "")))
        password = str(form_data.get("password", ""))
        confirm_password = str(form_data.get("confirm_password", ""))

        if not self._is_valid_username(username):
            self.register_error = "Username must be 3-32 chars (letters, numbers, dot, dash, underscore)."
            return [rx.set_focus("username")]
        if not self._is_valid_password(password):
            self.register_error = "Password must be at least 8 chars with upper, lower, and number."
            return [rx.set_value("password", ""), rx.set_value("confirm_password", ""), rx.set_focus("password")]
        if password != confirm_password:
            self.register_error = "Passwords do not match."
            return [rx.set_value("confirm_password", ""), rx.set_focus("confirm_password")]

        with rx.session() as session:
            existing_user = session.exec(
                select(LocalUser).where(func.lower(LocalUser.username) == username)
            ).one_or_none()
            if existing_user is not None:
                self.register_error = "Username is already registered."
                return [rx.set_value("username", ""), rx.set_focus("username")]

            new_user = LocalUser(
                username=username,
                password_hash=LocalUser.hash_password(password),
                enabled=True,
            )
            session.add(new_user)
            session.commit()

        self.register_success = True
        self.auth_csrf_token = secrets.token_urlsafe(24)
        return [rx.redirect(auth_routes.LOGIN_ROUTE)]

    @rx.event
    def handle_password_reset(self, form_data: dict[str, Any]):
        self._ensure_auth_csrf()
        self.reset_error = ""
        self.reset_success = False
        generic_error = "Unable to reset password. Check your details and try again."

        if not self._csrf_ok(form_data):
            self.reset_error = "Session expired. Refresh and try again."
            return

        username = self._normalize_username(str(form_data.get("username", "")))
        current_password = str(form_data.get("current_password", ""))
        new_password = str(form_data.get("new_password", ""))
        confirm_new_password = str(form_data.get("confirm_new_password", ""))

        if not self._is_valid_username(username):
            self.reset_error = generic_error
            return [rx.set_focus("username")]
        if not current_password:
            self.reset_error = generic_error
            return [rx.set_focus("current_password")]
        if not self._is_valid_password(new_password):
            self.reset_error = "New password must be at least 8 chars with upper, lower, and number."
            return [rx.set_value("new_password", ""), rx.set_value("confirm_new_password", ""), rx.set_focus("new_password")]
        if new_password != confirm_new_password:
            self.reset_error = "New passwords do not match."
            return [rx.set_value("confirm_new_password", ""), rx.set_focus("confirm_new_password")]

        with rx.session() as session:
            user = session.exec(
                select(LocalUser).where(func.lower(LocalUser.username) == username)
            ).one_or_none()
            if user is None or user.id is None or (not user.enabled) or (not user.verify(current_password)):
                self._record_login_failure(username)
                self.reset_error = generic_error
                return [rx.set_value("current_password", ""), rx.set_focus("current_password")]

            user.password_hash = LocalUser.hash_password(new_password)
            session.add(user)
            session.commit()

        self._clear_login_failures(username)
        self.reset_success = True
        self.auth_csrf_token = secrets.token_urlsafe(24)
        return [
            rx.set_value("current_password", ""),
            rx.set_value("new_password", ""),
            rx.set_value("confirm_new_password", ""),
            rx.redirect(auth_routes.LOGIN_ROUTE),
        ]

    @rx.event
    def open_pricing_modal(self):
        self.show_pricing_modal = True
        self.payment_error = ""

    @rx.event
    def close_pricing_modal(self):
        self.show_pricing_modal = False
        self.payment_error = ""

    @rx.event
    async def initiate_payment(self, plan: int):
        uid = self._uid()
        if uid < 0:
            self.payment_error = "Not authenticated. Please log in."
            return

        if plan not in PLANS:
            self.payment_error = "Invalid plan selected."
            return

        if not PAYHERE_MERCHANT_ID or not PAYHERE_MERCHANT_SECRET:
            self.payment_error = "Payment gateway not configured. Contact support."
            return

        self.payment_processing = True
        self.payment_error = ""
        yield

        try:
            plan_cfg   = PLANS[plan]
            amount     = plan_cfg["amount"]
            currency   = "LKR"
            ts         = int(datetime.now(timezone.utc).timestamp() * 1000)
            order_id   = f"ALEXAI-{uid}-P{plan}-{ts}"

            with rx.session() as session:
                order = PaymentOrder(  # type: ignore
                    user_id  = uid,
                    order_id = order_id,
                    plan     = plan,
                    amount   = amount,
                    currency = currency,
                    status   = "pending",
                )
                session.add(order)
                session.commit()

            ph_hash = _generate_ph_hash(order_id, amount, currency)

            normalized_name = _normalize_person_name(self.name) or "Student User"
            first_name = normalized_name.split()[0]
            last_name  = " ".join(normalized_name.split()[1:]) or "User"

            return_url = f"{APP_BASE_URL}/payment/success"
            cancel_url = f"{APP_BASE_URL}/payment/cancel"
            notify_url = f"{API_BASE_URL}/api/payhere/notify"

            js = f"""
(function() {{
  var fields = {{
    merchant_id: {json.dumps(PAYHERE_MERCHANT_ID)},
    return_url:  {json.dumps(return_url)},
    cancel_url:  {json.dumps(cancel_url)},
    notify_url:  {json.dumps(notify_url)},
    order_id:    {json.dumps(order_id)},
    items:       {json.dumps(plan_cfg['name'])},
    currency:    {json.dumps(currency)},
    amount:      {json.dumps(f"{amount:.2f}")},
    first_name:  {json.dumps(first_name)},
    last_name:   {json.dumps(last_name)},
    email:       {json.dumps(f"user{uid}@alexai.lk")},
    phone:       "0771234567",
    address:     "Colombo",
    city:        "Colombo",
    country:     "Sri Lanka",
    hash:        {json.dumps(ph_hash)}
  }};
  var f = document.createElement('form');
  f.method = 'POST';
  f.action = {json.dumps(PAYHERE_CHECKOUT_URL)};
  for (var k in fields) {{
    var inp = document.createElement('input');
    inp.type  = 'hidden';
    inp.name  = k;
    inp.value = fields[k];
    f.appendChild(inp);
  }}
  document.body.appendChild(f);
  f.submit();
}})();
"""
            self.payment_processing = False
            self.show_pricing_modal = False
            yield rx.call_script(js)

        except Exception as e:
            print(f"[Payment] initiate error: {e}")
            self.payment_error = "Something went wrong. Please try again."
            self.payment_processing = False

    @rx.event
    def set_name(self, value: str):
        self.name = _normalize_person_name(value)
        self.onboarding_message = ""
        uid = self._uid()
        self._save_memory(uid)

    @rx.var
    def available_semesters(self) -> list[str]:
        if not self.selected_year:
            return []
        return SEMESTER_NAVIGATION.get(self.selected_year, [])

    def _uid(self) -> int:
        tokens: list[str] = []
        for raw in (self.auth_token, self.app_auth_token):
            token = (raw or "").strip()
            if token and token not in tokens:
                tokens.append(token)
        if not tokens:
            return -1
        try:
            with rx.session() as session:
                for token in tokens:
                    auth_sess = session.exec(
                        select(LocalAuthSession).where(
                            LocalAuthSession.session_id == token,
                            LocalAuthSession.expiration >= datetime.now(timezone.utc),
                        )
                    ).one_or_none()
                    if auth_sess and auth_sess.user_id is not None:
                        return int(auth_sess.user_id)
        except Exception as e:
            print(f"ERROR uid lookup: {e}")
        return -1

    def _safe_role(self, role: str) -> str:
        return "assistant" if role == "bot" else role

    def _scope_key(self, year: str, semester: str) -> str:
        return semester_scope_key(year, semester)

    def _normalize_course_label(self, value: str) -> str:
        text = (value or "").strip().lower()
        if ":" in text:
            text = text.split(":", 1)[1]
        text = re.sub(r"[^a-z0-9]+", " ", text)
        return " ".join(text.split())

    def _semester_courses(self, year: str, semester: str) -> list[str]:
        return FULL_CURRICULUM.get(year, {}).get(semester, [])

    def _has_curriculum_for_semester(self, year: str, semester: str) -> bool:
        return bool(self._semester_courses(year, semester))

    def _plan_matches_semester(self, plan: list, year: str, semester: str) -> bool:
        if not plan:
            return True

        expected = {
            self._normalize_course_label(course)
            for course in self._semester_courses(year, semester)
            if self._normalize_course_label(course)
        }
        if not expected:
            return True

        subjects: list[str] = []
        for entry in plan[:20]:
            subject = self._normalize_course_label(str(entry.get("subject", "")))
            if subject and subject not in subjects:
                subjects.append(subject)

        if not subjects:
            return False

        # Lenient matching: check word overlap between plan subjects and expected courses
        expected_words = set()
        for course in expected:
            for w in course.split():
                if len(w) >= 4:
                    expected_words.add(w)

        for subject in subjects:
            # Direct or substring match
            for course in expected:
                if subject == course or subject in course or course in subject:
                    return True
            # Word overlap: if 2+ significant words match, accept it
            subj_words = {w for w in subject.split() if len(w) >= 4}
            if len(subj_words & expected_words) >= 2:
                return True

        return False

    def _current_courses_for_scope(self) -> list[str]:
        if self.view_mode != "semester" or not self.selected_year or not self.selected_semester:
            return []
        return self._semester_courses(self.selected_year, self.selected_semester)

    def _set_default_semester_workspace(self, uid: int, year: str, semester: str, *, load_scope: bool = True) -> str:
        if uid < 0 or not year or not semester:
            return ""
        scope = self._scope_key(year, semester)
        self.selected_year = year
        self.selected_semester = semester
        self.view_mode = "semester"
        self.active_scope = scope
        self.show_semester_sidebar = False
        self._save_memory(uid)
        if load_scope:
            self._switch_scope(uid, scope)
        return scope

    def _ensure_scope_memory(self, uid: int, scope: str) -> None:
        if uid < 0:
            return
        with rx.session() as session:
            row = session.exec(
                select(ScopeMemory).where(ScopeMemory.user_id == uid).where(ScopeMemory.scope == scope)
            ).one_or_none()
            if row is None:
                session.add(ScopeMemory(user_id=uid, scope=scope, summary=""))  # type: ignore
                session.commit()

    def _get_scope_summary(self, uid: int, scope: str) -> str:
        if uid < 0:
            return ""
        with rx.session() as session:
            row = session.exec(
                select(ScopeMemory).where(ScopeMemory.user_id == uid).where(ScopeMemory.scope == scope)
            ).one_or_none()
        return (row.summary if row else "") or ""

    def _set_scope_summary(self, uid: int, scope: str, text: str) -> None:
        if uid < 0:
            return
        with rx.session() as session:
            row = session.exec(
                select(ScopeMemory).where(ScopeMemory.user_id == uid).where(ScopeMemory.scope == scope)
            ).one_or_none()
            if row is None:
                row = ScopeMemory(user_id=uid, scope=scope, summary="")  # type: ignore
            row.summary = (text or "")[:4000]
            session.add(row)
            session.commit()

    def _get_all_scope_summaries_text(self, uid: int) -> str:
        if uid < 0:
            return ""
        with rx.session() as session:
            rows = session.exec(
                select(ScopeMemory).where(ScopeMemory.user_id == uid).order_by(ScopeMemory.scope)
            ).all()
        return "\n\n".join(
            f"{r.scope}\n{r.summary}".strip()
            for r in rows
            if r.scope not in ("home", ADAPTIVE_PROFILE_SCOPE) and (r.summary or "").strip()
        )

    @rx.event
    def delete_session(self, session_id: str):
        uid = self._uid()
        if uid < 0 or not session_id:
            return
        try:
            sid = int(session_id)
            if not self._session_in_scope(uid, sid, self.active_scope):
                return
            with rx.session() as session:
                for m in session.exec(select(ChatMessage2).where(ChatMessage2.session_id == sid)).all():
                    session.delete(m)
                sess = session.exec(select(ChatSession).where(ChatSession.id == sid)).one_or_none()
                if sess:
                    session.delete(sess)
                session.commit()
            if self.current_session_id == session_id:
                self.current_session_id = ""
                self.current_session_choice = ""
                self._ensure_session(uid, self.active_scope)
                self._load_messages(uid)
            self._load_sessions(uid, self.active_scope)
        except Exception as e:
            print(f"ERROR delete_session: {e}")

    def _ensure_session(self, uid: int, scope: str) -> None:
        with rx.session() as session:
            sess = session.exec(
                select(ChatSession)
                .where(ChatSession.user_id == uid)
                .where(ChatSession.scope == scope)
                .order_by(ChatSession.updated_at.desc())
            ).first()
            if sess is None:
                sess = ChatSession(user_id=uid, scope=scope)  # type: ignore
                session.add(sess)
                session.commit()
                session.refresh(sess)
            self.current_session_id = str(sess.id)
            self.current_session_choice = f"{sess.id}::{sess.title}"

    def _session_in_scope(self, uid: int, sid: int, scope: str) -> bool:
        if uid < 0 or sid <= 0:
            return False
        with rx.session() as session:
            sess = session.exec(
                select(ChatSession)
                .where(ChatSession.id == sid)
                .where(ChatSession.user_id == uid)
            ).one_or_none()
        return bool(sess and sess.scope == scope)

    def _reset_scope_workspace(self, uid: int, scope: str) -> None:
        if uid < 0 or not scope:
            return
        with rx.session() as session:
            sessions = session.exec(
                select(ChatSession)
                .where(ChatSession.user_id == uid)
                .where(ChatSession.scope == scope)
            ).all()
            for sess in sessions:
                messages = session.exec(
                    select(ChatMessage2).where(ChatMessage2.session_id == int(sess.id))
                ).all()
                for msg in messages:
                    session.delete(msg)
                session.delete(sess)

            plan = session.exec(
                select(SemesterStudyPlan)
                .where(SemesterStudyPlan.user_id == uid)
                .where(SemesterStudyPlan.scope == scope)
            ).one_or_none()
            if plan is not None:
                session.delete(plan)

            progress = session.exec(
                select(DayProgress)
                .where(DayProgress.user_id == uid)
                .where(DayProgress.scope == scope)
            ).one_or_none()
            if progress is not None:
                session.delete(progress)

            scope_memory = session.exec(
                select(ScopeMemory)
                .where(ScopeMemory.user_id == uid)
                .where(ScopeMemory.scope == scope)
            ).one_or_none()
            if scope_memory is not None:
                scope_memory.summary = ""
                session.add(scope_memory)

            session.commit()

    def _load_sessions(self, uid: int, scope: str) -> None:
        with rx.session() as session:
            rows = session.exec(
                select(ChatSession)
                .where(ChatSession.user_id == uid)
                .where(ChatSession.scope == scope)
                .order_by(ChatSession.updated_at.desc())
            ).all()
        self.sessions = [{"id": str(r.id), "title": r.title} for r in rows]
        if not self.current_session_id and rows:
            first = rows[0]
            self.current_session_id = str(first.id)
            self.current_session_choice = f"{first.id}::{first.title}"

    def _migrate_legacy_messages_once(self, uid: int) -> None:
        with rx.session() as session:
            if session.exec(select(ChatMessage2).where(ChatMessage2.user_id == uid).limit(1)).first():
                return
            legacy = session.exec(select(ChatMessage).where(ChatMessage.user_id == uid).order_by(ChatMessage.id)).all()
            if not legacy:
                return
            sess = ChatSession(user_id=uid, scope="home", title="Imported chat")  # type: ignore
            session.add(sess)
            session.commit()
            session.refresh(sess)
            for m in legacy:
                session.add(ChatMessage2(user_id=uid, session_id=int(sess.id), role=self._safe_role(m.role), content=m.content))
            session.commit()

    def _load_messages(self, uid: int, scope: str = "", *, _trusted: bool = False) -> None:
        effective_scope = scope or self.active_scope
        if not self.current_session_id:
            self.chat_history = []
            return
        sid = int(self.current_session_id)
        if not _trusted and not self._session_in_scope(uid, sid, effective_scope):
            self.current_session_id = ""
            self.current_session_choice = ""
            self.chat_history = []
            return
        with rx.session() as session:
            msgs = session.exec(
                select(ChatMessage2).where(ChatMessage2.user_id == uid).where(ChatMessage2.session_id == sid).order_by(ChatMessage2.id)
            ).all()

        self.chat_history = [
            {
                "role": m.role,
                "content": sanitize_for_ui(m.content) if m.role == "assistant" else m.content,
            }
            for m in msgs
        ]

    def _save_message(self, uid: int, role: str, content: str, scope: str = "", trusted: bool = False) -> None:
        effective_scope = scope or self.active_scope
        if uid < 0 or not self.current_session_id:
            return
        if not trusted and not self._session_in_scope(uid, int(self.current_session_id), effective_scope):
            return
        safe_content = sanitize_for_ui(content) if role == "assistant" else content
        with rx.session() as session:
            session.add(ChatMessage2(user_id=uid, session_id=int(self.current_session_id), role=role, content=safe_content))
            session.commit()

    def _save_memory(self, uid: int) -> None:
        if uid < 0:
            return
        normalized_name = _normalize_person_name(self.name)
        if self.name != normalized_name:
            self.name = normalized_name
        with rx.session() as session:
            mem = session.exec(select(UserMemory).where(UserMemory.user_id == uid)).one_or_none()
            if mem is None:
                mem = UserMemory(user_id=uid)  # type: ignore
            mem.step = self.step; mem.name = normalized_name; mem.degree = self.degree
            mem.is_started = self.is_started; mem.selected_year = self.selected_year; mem.selected_semester = self.selected_semester
            mem.summary = self.memory_summary
            session.add(mem)
            session.commit()

    def _ensure_progress_for_year(self, uid: int, year: str) -> None:
        if uid < 0 or year not in FULL_CURRICULUM:
            return
        items, idx = [], 0
        for semester, courses in FULL_CURRICULUM[year].items():
            for course in courses:
                items.append((semester, course, idx)); idx += 1
        with rx.session() as session:
            existing_set = set(session.exec(
                select(StudyProgress.course).where(StudyProgress.user_id == uid).where(StudyProgress.year == year)
            ).all())
            for semester, course, order_index in items:
                if course not in existing_set:
                    session.add(StudyProgress(user_id=uid, year=year, semester=semester, course=course, order_index=order_index))
            session.commit()

    def _get_next_courses(self, uid: int, year: str, n: int = 3) -> list[str]:
        if uid < 0 or not year:
            return []
        with rx.session() as session:
            rows = session.exec(
                select(StudyProgress).where(StudyProgress.user_id == uid).where(StudyProgress.year == year).where(StudyProgress.status != "done").order_by(StudyProgress.order_index)
            ).all()
        return [r.course for r in rows[:n]]

    def _refresh_today_plan(self, uid: int) -> None:
        if uid < 0 or not self.selected_year:
            self.today_plan = ""; return
        nxt = self._get_next_courses(uid, self.selected_year, 2)
        self.today_plan = "all done for this year" if not nxt else "\n".join([f"today focus {c}" for c in nxt])

    def _extract_json(self, text: str) -> dict:
        try: return json.loads(text)
        except Exception: pass
        try:
            a, b = text.find("{"), text.rfind("}")
            if a != -1 and b != -1 and b > a: return json.loads(text[a:b+1])
        except Exception: return {}
        return {}

    def _extract_json_list(self, text: str) -> list:
        # Strip markdown code fences
        cleaned = (text or "").strip()
        if cleaned.startswith("```"):
            # Remove opening fence (```json or ```)
            first_nl = cleaned.find("\n")
            if first_nl != -1:
                cleaned = cleaned[first_nl + 1:]
            # Remove closing fence
            if cleaned.rstrip().endswith("```"):
                cleaned = cleaned.rstrip()[:-3].rstrip()

        # Try direct parse
        try:
            result = json.loads(cleaned)
            if isinstance(result, list):
                return result
        except Exception:
            pass

        # Extract outermost [ ... ]
        a = cleaned.find("[")
        if a == -1:
            return []
        b = cleaned.rfind("]")
        if b != -1 and b > a:
            try:
                return json.loads(cleaned[a:b + 1])
            except Exception:
                pass

        # Truncated array: find last complete object and close the array
        fragment = cleaned[a:]
        # Find last complete "}" and truncate there
        last_brace = fragment.rfind("}")
        if last_brace > 0:
            truncated = fragment[:last_brace + 1] + "]"
            try:
                result = json.loads(truncated)
                if isinstance(result, list):
                    print(f"[PLAN-GEN] Recovered {len(result)} items from truncated JSON", flush=True)
                    return result
            except Exception:
                pass

        return []
        # ----------------------------
    # memory tuning
    # ----------------------------
    SCOPE_SUMMARY_TRIGGER_NEW_MSGS = 12
    GLOBAL_MEMORY_TRIGGER_NEW_MSGS = 24
    ADAPTIVE_PROFILE_TRIGGER_NEW_MSGS = 4
    PAST_HITS_LIMIT = 8
    PAST_HITS_MAX_CHARS = 220

    def _kw(self, text: str) -> list[str]:
        stop = {
            "this","that","with","have","what","when","your","from","they","them","then",
            "just","like","about","into","need","tell","give","does","done","only","more",
            "less","been","were","will","would","could","should","because","also","there",
            "here","want","make","please","help"
        }
        words = []
        for raw in (text or "").split():
            w = raw.strip(".,!?;:()[]{}'\"").lower()
            if len(w) < 4:
                continue
            if w.isdigit():
                continue
            if w in stop:
                continue
            if w not in words:
                words.append(w)
            if len(words) >= 6:
                break
        return words

    def _scope_session_ids(self, uid: int, scope: str) -> list[int]:
        if uid < 0:
            return []
        with rx.session() as session:
            rows = session.exec(
                select(ChatSession.id)
                .where(ChatSession.user_id == uid)
                .where(ChatSession.scope == scope)
            ).all()
        out: list[int] = []
        for r in rows:
            try:
                out.append(int(r))
            except Exception:
                try:
                    out.append(int(r[0]))
                except Exception:
                    pass
        return out

    def _memory_search_session_ids(self, uid: int, scope: str) -> list[int]:
        if scope != "home":
            return self._scope_session_ids(uid, scope)
        if uid < 0:
            return []
        with rx.session() as session:
            rows = session.exec(
                select(ChatSession.id)
                .where(ChatSession.user_id == uid)
            ).all()
        out: list[int] = []
        for r in rows:
            try:
                out.append(int(r))
            except Exception:
                try:
                    out.append(int(r[0]))
                except Exception:
                    pass
        return out

    def _recent_msgs_for_session(self, uid: int, sid: int, n: int = 18) -> list[dict]:
        with rx.session() as session:
            rows = session.exec(
                select(ChatMessage2)
                .where(ChatMessage2.user_id == uid)
                .where(ChatMessage2.session_id == sid)
                .order_by(ChatMessage2.id.desc())
                .limit(n)
            ).all()
        rows = list(reversed(rows))
        return [{"role": m.role, "content": m.content} for m in rows]

    def _recent_msgs_for_user(self, uid: int, n: int = 26) -> list[dict]:
        with rx.session() as session:
            rows = session.exec(
                select(ChatMessage2)
                .where(ChatMessage2.user_id == uid)
                .order_by(ChatMessage2.id.desc())
                .limit(n)
            ).all()
        rows = list(reversed(rows))
        return [{"role": m.role, "content": m.content} for m in rows]

    def _past_hits_text(self, uid: int, scope: str, user_msg: str) -> str:
        kws = self._kw(user_msg)
        if not kws:
            return ""

        sids = self._memory_search_session_ids(uid, scope)
        if not sids:
            return ""

        # Escape SQL LIKE wildcards to prevent injection
        def _escape_like(s: str) -> str:
            return s.replace("%", r"\%").replace("_", r"\_")

        conds = [func.lower(ChatMessage2.content).like(f"%{_escape_like(k)}%") for k in kws]

        with rx.session() as session:
            rows = session.exec(
                select(ChatMessage2)
                .where(ChatMessage2.user_id == uid)
                .where(ChatMessage2.session_id.in_(sids))
                .where(or_(*conds))
                .order_by(ChatMessage2.id.desc())
                .limit(self.PAST_HITS_LIMIT)
            ).all()

        if not rows:
            return ""

        lines = []
        for m in rows:
            c = (m.content or "").replace("\n", " ").strip()
            if len(c) > self.PAST_HITS_MAX_CHARS:
                c = c[: self.PAST_HITS_MAX_CHARS] + "..."
            lines.append(f"- {m.role}: {c}")
        return "\n".join(lines)

    def _scope_updated_at(self, uid: int, scope: str):
        with rx.session() as session:
            row = session.exec(
                select(ScopeMemory)
                .where(ScopeMemory.user_id == uid)
                .where(ScopeMemory.scope == scope)
            ).one_or_none()
        return row.updated_at if row else None

    def _user_memory_updated_at(self, uid: int):
        with rx.session() as session:
            row = session.exec(select(UserMemory).where(UserMemory.user_id == uid)).one_or_none()
        return row.updated_at if row else None

    def _get_adaptive_profile(self, uid: int) -> str:
        self._ensure_scope_memory(uid, ADAPTIVE_PROFILE_SCOPE)
        return self._get_scope_summary(uid, ADAPTIVE_PROFILE_SCOPE)

    def _set_adaptive_profile(self, uid: int, text: str) -> None:
        cleaned = (text or "").strip()[:4000]
        self._set_scope_summary(uid, ADAPTIVE_PROFILE_SCOPE, cleaned)
        self.adaptive_profile = cleaned

    def _adaptive_profile_updated_at(self, uid: int):
        return self._scope_updated_at(uid, ADAPTIVE_PROFILE_SCOPE)

    def _count_new_msgs_since(self, uid: int, sids: list[int], since_dt) -> int:
        if not since_dt or not sids:
            return 999999
        with rx.session() as session:
            cnt = session.exec(
                select(func.count())
                .select_from(ChatMessage2)
                .where(ChatMessage2.user_id == uid)
                .where(ChatMessage2.session_id.in_(sids))
                .where(ChatMessage2.created_at > since_dt)
            ).one()
        try:
            return int(cnt)
        except Exception:
            try:
                return int(cnt[0])
            except Exception:
                return 0

    def _count_user_new_msgs_since(self, uid: int, since_dt) -> int:
        if not since_dt:
            return 999999
        with rx.session() as session:
            cnt = session.exec(
                select(func.count())
                .select_from(ChatMessage2)
                .where(ChatMessage2.user_id == uid)
                .where(ChatMessage2.created_at > since_dt)
            ).one()
        try:
            return int(cnt)
        except Exception:
            try:
                return int(cnt[0])
            except Exception:
                return 0

    async def _maybe_auto_update_scope_summary(self, uid: int, scope: str) -> None:
        if uid < 0 or client is None:
            return

        self._ensure_scope_memory(uid, scope)
        since_dt = self._scope_updated_at(uid, scope)
        sids = self._scope_session_ids(uid, scope)

        new_cnt = self._count_new_msgs_since(uid, sids, since_dt)
        if new_cnt < self.SCOPE_SUMMARY_TRIGGER_NEW_MSGS:
            return

        current = self._get_scope_summary(uid, scope)

        if self.current_session_id:
            recent_msgs = self._recent_msgs_for_session(uid, int(self.current_session_id), 22)
        else:
            recent_msgs = self._recent_msgs_for_user(uid, 28)

        recent_text = "\n".join([f'{m["role"]}: {m["content"]}' for m in recent_msgs])

        try:
            resp = await asyncio.to_thread(
                _groq_generate,
                GEMINI_FAST_MODEL,
                f"Update scope memory. Keep short facts only.\nScope: {scope}\nCurrent: {current}\nNew: {recent_text}\nReturn only updated summary."
            )
            new_sum = (getattr(resp, "text", "") or "").strip()
            if new_sum:
                self._set_scope_summary(uid, scope, new_sum)
        except Exception as e:
            print(f"ERROR auto scope summary: {e}")

    async def _maybe_auto_update_global_memory(self, uid: int) -> None:
        if uid < 0 or client is None:
            return

        since_dt = self._user_memory_updated_at(uid)
        new_cnt = self._count_user_new_msgs_since(uid, since_dt)
        if new_cnt < self.GLOBAL_MEMORY_TRIGGER_NEW_MSGS:
            return

        recent_msgs = self._recent_msgs_for_user(uid, 30)
        recent_text = "\n".join([f'{m["role"]}: {m["content"]}' for m in recent_msgs])

        try:
            resp = await asyncio.to_thread(
                _groq_generate,
                GEMINI_FAST_MODEL,
                f"Update long term memory summary. Keep short stable facts only.\nCurrent: {self.memory_summary}\nNew: {recent_text}\nReturn only updated memory text."
            )
            new_sum = (getattr(resp, "text", "") or "").strip()
            if new_sum:
                self.memory_summary = new_sum[:4000]
                self._save_memory(uid)
        except Exception as e:
            print(f"ERROR auto global memory: {e}")

    async def _maybe_auto_update_adaptive_profile(self, uid: int) -> None:
        if uid < 0 or client is None:
            return

        since_dt = self._adaptive_profile_updated_at(uid)
        new_cnt = self._count_user_new_msgs_since(uid, since_dt)
        if new_cnt < self.ADAPTIVE_PROFILE_TRIGGER_NEW_MSGS:
            return

        current = self._get_adaptive_profile(uid)
        recent_msgs = self._recent_msgs_for_user(uid, 40)
        recent_text = "\n".join([f'{m["role"]}: {m["content"]}' for m in recent_msgs])

        prompt = f"""Build an adaptive tutoring profile from the user's recent study conversations.
Return ONLY short bullet points.
Maximum 12 bullets.
Focus on stable tutoring preferences and learning patterns, not temporary chat details.

Use these labels when supported by evidence:
- Preferred explanation depth
- Preferred format
- Pace and tone
- Topics user struggles with
- Topics user handles well
- Common confusion triggers
- Revision needs
- Practice difficulty level
- Best response patterns for this user

Current saved profile:
{current}

Recent study conversations:
{recent_text}

Update the saved profile instead of overwriting randomly. Keep only durable tutoring insights."""

        try:
            resp = await asyncio.to_thread(_groq_generate, GEMINI_FAST_MODEL, prompt)
            new_profile = (getattr(resp, "text", "") or "").strip()
            if new_profile:
                self._set_adaptive_profile(uid, new_profile)
        except Exception as e:
            print(f"ERROR auto adaptive profile: {e}")

    def _switch_scope(self, uid: int, scope: str) -> None:
        # CRITICAL: clear display state FIRST so if anything below fails,
        # the user sees an empty chat — not another scope's messages.
        old_scope = self.active_scope
        old_session = self.current_session_id
        self.active_scope = scope
        self.current_session_id = ""
        self.current_session_choice = ""
        self.chat_history = []
        self.sessions = []

        try:
            self._ensure_scope_memory(uid, scope)
            self._ensure_session(uid, scope)
            self._load_sessions(uid, scope)
            self._load_messages(uid, scope)
            print(f"[_switch_scope] {old_scope}(sid={old_session}) → {scope}(sid={self.current_session_id}), loaded {len(self.chat_history)} msgs")
        except Exception as e:
            print(f"ERROR _switch_scope({scope}): {e}")
            # State is already cleared above, so UI shows empty — not stale data

    def _get_study_plan(self, uid: int, scope: str) -> list:
        if uid < 0: return []
        with rx.session() as session:
            row = session.exec(select(SemesterStudyPlan).where(SemesterStudyPlan.user_id == uid).where(SemesterStudyPlan.scope == scope)).one_or_none()
        if row is None or not row.plan_json: return []
        try: return json.loads(row.plan_json)
        except Exception: return []

    def _get_plan_generation_state(self, uid: int, scope: str) -> tuple[str, str, Optional[datetime]]:
        if uid < 0 or not scope:
            return (PLAN_GENERATION_STATUS_IDLE, "", None)
        with rx.session() as session:
            row = session.exec(
                select(SemesterPlanGenerationState)
                .where(SemesterPlanGenerationState.user_id == uid)
                .where(SemesterPlanGenerationState.scope == scope)
                .order_by(SemesterPlanGenerationState.updated_at.desc())
            ).first()
        if row is None:
            return (PLAN_GENERATION_STATUS_IDLE, "", None)
        return (row.status or PLAN_GENERATION_STATUS_IDLE, row.error_message or "", row.updated_at)

    def _set_plan_generation_state(self, uid: int, scope: str, status: str, error_message: str = "") -> None:
        if uid < 0 or not scope:
            return
        with rx.session() as session:
            row = session.exec(
                select(SemesterPlanGenerationState)
                .where(SemesterPlanGenerationState.user_id == uid)
                .where(SemesterPlanGenerationState.scope == scope)
                .order_by(SemesterPlanGenerationState.updated_at.desc())
            ).first()
            if row is None:
                row = SemesterPlanGenerationState(user_id=uid, scope=scope)  # type: ignore
            row.status = status or PLAN_GENERATION_STATUS_IDLE
            row.error_message = (error_message or "")[:300]
            session.add(row)
            session.commit()

    def _plan_generation_is_stale(self, updated_at: Optional[datetime]) -> bool:
        if updated_at is None:
            return False
        stamp = updated_at if updated_at.tzinfo is not None else updated_at.replace(tzinfo=timezone.utc)
        return stamp < (datetime.now(timezone.utc) - PLAN_GENERATION_STALE_AFTER)

    def _save_study_plan(self, uid: int, scope: str, plan: list) -> None:
        if uid < 0: return
        with rx.session() as session:
            row = session.exec(select(SemesterStudyPlan).where(SemesterStudyPlan.user_id == uid).where(SemesterStudyPlan.scope == scope)).one_or_none()
            if row is None:
                row = SemesterStudyPlan(user_id=uid, scope=scope, plan_json="")  # type: ignore
            row.plan_json = json.dumps(plan)
            session.add(row); session.commit()

    def _get_day_progress(self, uid: int, scope: str) -> tuple[int, int]:
        if uid < 0: return (1, 0)
        with rx.session() as session:
            row = session.exec(select(DayProgress).where(DayProgress.user_id == uid).where(DayProgress.scope == scope)).one_or_none()
        return (row.current_day, row.current_topic_index) if row else (1, 0)

    def _save_day_progress(self, uid: int, scope: str, day: int, topic_index: int) -> None:
        if uid < 0: return
        with rx.session() as session:
            row = session.exec(select(DayProgress).where(DayProgress.user_id == uid).where(DayProgress.scope == scope)).one_or_none()
            if row is None:
                row = DayProgress(user_id=uid, scope=scope, current_day=day, current_topic_index=topic_index)  # type: ignore
            else:
                row.current_day = day; row.current_topic_index = topic_index
            session.add(row); session.commit()

    def _get_today_entry(self, plan: list, day: int) -> dict:
        for entry in plan:
            if entry.get("day") == day: return entry
        return {}

    def _build_today_message(self, plan: list, day: int, topic_index: int) -> str:
        entry = self._get_today_entry(plan, day)
        if not entry: return "You have completed all 110 days of the study plan"
        subject, unit, topics = entry.get("subject",""), entry.get("unit",""), entry.get("topics",[])
        if not topics: return f"Day {day}/110\nSubject {subject}\nUnit {unit}\n\nNo topics found for today"
        current_topic = topics[topic_index] if topic_index < len(topics) else topics[-1]
        remaining = topics[topic_index:]
        msg = f"Day {day}/110\nSubject {subject}\nUnit {unit}\n\nToday topic {current_topic}\n\n"
        if len(remaining) > 1: msg += f"Remaining today {', '.join(remaining[1:])}\n\n"
        return msg + "Ask me anything about this topic or say next to move"

    def _detect_next_topic_intent(self, text: str) -> bool:
        lower = text.lower().strip()
        return any(t in lower for t in ["next","i know this","i know it","skip","move on","next topic","got it","understood","done","i understand","move next","go next","next one","continue","proceed"])

    def _detect_show_full_plan_intent(self, text: str) -> bool:
        lower = text.lower().strip()
        return any(t in lower for t in ["full plan","show plan","all plan","see plan","show me the plan","complete plan","entire plan","whole plan","all days","show all days"])

    def _detect_edit_plan_intent(self, text: str) -> bool:
        lower = text.lower().strip()
        return any(t in lower for t in ["edit plan","change plan","modify plan","update plan","edit day","change day","swap day","reschedule"])

    def _current_focus_modules_label(self) -> str:
        return self.selected_semester or "current semester"

    def _alex_identity_reply(self) -> str:
        return "I am Alex, your Software Engineering Mentor. I'm here to ensure you crush your degree."

    def _alex_focus_redirect(self, student_name: str) -> str:
        return (
            f"I'm specialized in your Software Engineering journey, {student_name}. "
            f"Let's stay focused on mastering your {self._current_focus_modules_label()} modules."
        )

    def _is_identity_question(self, text: str) -> bool:
        lower = (text or "").lower().strip()
        identity_markers = (
            "who are you",
            "what are you",
            "are you ai",
            "are you an ai",
            "are you a chatbot",
            "what model are you",
            "which model are you",
            "what llm",
            "large language model",
            "groq",
            "llama",
            "meta ai",
        )
        return any(marker in lower for marker in identity_markers)

    def _is_off_topic_request(self, text: str) -> bool:
        lower = (text or "").lower().strip()
        if not lower:
            return False

        allowed_academic_terms = (
            "software",
            "engineering",
            "code",
            "coding",
            "programming",
            "algorithm",
            "data structure",
            "database",
            "web",
            "mobile",
            "network",
            "operating system",
            "debug",
            "bug",
            "semester",
            "module",
            "course",
            "assignment",
            "exam",
            "study",
            "career",
            "internship",
            "cv",
            "resume",
            "interview",
            "project",
            "github",
            "oop",
            "architecture",
            "requirement engineering",
            "software testing",
            "verification",
            "validation",
        )
        if any(term in lower for term in allowed_academic_terms):
            return False

        off_topic_terms = (
            "recipe",
            "cook",
            "cooking",
            "bake",
            "meal",
            "diet",
            "symptom",
            "doctor",
            "medicine",
            "medical advice",
            "diagnose",
            "diagnosis",
            "celebrity",
            "actor",
            "singer",
            "movie gossip",
            "horoscope",
            "astrology",
            "lottery",
            "betting",
            "football score",
            "cricket score",
            "politics",
            "election",
            "court case",
            "legal advice",
            "lawyer",
            "divorce",
            "visa lottery",
        )
        return any(term in lower for term in off_topic_terms)

    def _alex_guardrail_reply(self, text: str, student_name: str) -> str:
        if self._is_identity_question(text):
            return self._alex_identity_reply()
        if self._is_off_topic_request(text):
            return self._alex_focus_redirect(student_name)
        return ""

    def _alex_system_prompt(self, student_name: str) -> str:
        return f"""You are Alex, the Software Engineering Mentor inside Alex AI.

Critical operating rules:
1. Your knowledge is strictly locked to Software Engineering and Academic Success for this student's degree.
2. If the student asks about unrelated topics such as cooking, medical advice, celebrity news, astrology, politics, or general law, politely decline and redirect them back to their Software Engineering journey.
3. Never describe yourself as an AI, chatbot, large language model, or mention Groq, Meta, or Llama.
4. If the student asks who you are, your answer must stay aligned with: "{self._alex_identity_reply()}"
5. Use {student_name} naturally throughout the conversation so the support feels personal and consistent.
6. When you share code, always wrap it in fenced markdown code blocks with the correct language.
7. For complex technical questions, give a numbered step-by-step breakdown before the final answer or code.
8. For career advice or analogies, prefer grounded Sri Lankan Software Engineering context when helpful, such as WSO2, Sysco LABS, IFS, internships, or local graduate expectations.
9. Stay focused, structured, and mentor-like. Do not drift into generic chatbot behavior.
"""

    def _reset_plan_only(self, uid: int, scope: str) -> None:
        """Reset ONLY the study plan and day progress — preserve chat sessions and messages."""
        if uid < 0 or not scope:
            return
        with rx.session() as session:
            plan = session.exec(
                select(SemesterStudyPlan)
                .where(SemesterStudyPlan.user_id == uid)
                .where(SemesterStudyPlan.scope == scope)
            ).one_or_none()
            if plan is not None:
                session.delete(plan)

            progress = session.exec(
                select(DayProgress)
                .where(DayProgress.user_id == uid)
                .where(DayProgress.scope == scope)
            ).one_or_none()
            if progress is not None:
                session.delete(progress)

            session.commit()

    def _enter_semester_environment(self, uid: int, year: str, semester: str) -> bool:
        if uid < 0 or not year or not semester:
            return False
        self.status_text = ""
        self.selected_year = year
        self.selected_semester = semester
        self.view_mode = "semester"
        new_scope = self._scope_key(year, semester)

        # CRITICAL: clear display state IMMEDIATELY so stale data from previous
        # scope never persists if anything below fails.
        self.chat_history = []
        self.sessions = []
        self.active_scope = new_scope

        existing_plan = self._get_study_plan(uid, new_scope)
        if existing_plan and not self._plan_matches_semester(existing_plan, year, semester):
            # Only clear the plan + day progress — NEVER delete chat sessions/messages
            self._reset_plan_only(uid, new_scope)
            existing_plan = []
        self.show_semester_sidebar = False
        self._save_memory(uid)
        self._ensure_progress_for_year(uid, year)
        self._refresh_today_plan(uid)
        self._switch_scope(uid, new_scope)

        if existing_plan:
            day, topic_idx = self._get_day_progress(uid, self.active_scope)
            self.current_day = day
            self.current_topic_index = topic_idx
            today_msg = self._build_today_message(existing_plan, day, topic_idx)
            if not self.chat_history:
                self.chat_history.append({"role": "assistant", "content": today_msg})
                self._save_message(uid, "assistant", today_msg)
            self.is_generating_plan = False
            return False

        if not self._has_curriculum_for_semester(year, semester):
            self.current_day = 1
            self.current_topic_index = 0
            self.is_generating_plan = False
            empty_msg = (
                f"{semester} is now your main AI workspace.\n\n"
                "This semester does not have course data yet, so the guided study plan cannot be generated until the curriculum is added."
            )
            if not self.chat_history:
                self.chat_history.append({"role": "assistant", "content": empty_msg})
                self._save_message(uid, "assistant", empty_msg)
            return False

        self.current_day = 1
        self.current_topic_index = 0
        self.is_generating_plan = True
        return True

    @rx.event
    def toggle_semester_sidebar(self):
        self.show_semester_sidebar = not self.show_semester_sidebar

    @rx.event
    def close_semester_sidebar(self):
        self.show_semester_sidebar = False

    @rx.event
    async def on_load(self):
        if not self.is_hydrated:
            return
        uid = self._uid()
        self._cached_uid = uid
        if uid < 0:
            yield AppState.auth_redir()  # type: ignore
            return
        
        self._load_profile(uid)
        self.adaptive_profile = self._get_adaptive_profile(uid)
        self._migrate_legacy_messages_once(uid)
        if not (self.name or "").strip():
            inferred_name = _extract_person_name(
                self.account_display_name,
                self.memory_summary,
                self.adaptive_profile,
                *[str(msg.get("content", "")) for msg in self.chat_history[-6:]],
            )
            if inferred_name:
                self.name = inferred_name
                self._save_memory(uid)
        self.status_text = ""
        self.onboarding_message = ""

        if self.active_scope == "home" and self.view_mode == "home":
            target_scope = "home"
            target_view_mode = "home"
        elif self.selected_year and self.selected_semester:
            target_scope = self._scope_key(self.selected_year, self.selected_semester)
            target_view_mode = "semester"
        else:
            target_scope = "home"
            target_view_mode = "home"

        self.view_mode = target_view_mode
        self.active_scope = target_scope

        if self.is_started:
            self._switch_scope(uid, target_scope)
            yield _hard_navigate(scope_to_route(target_scope))
            return

        # Onboarding: user hasn't completed setup yet — stay on /app
        if not self.selected_year:
            self.step = max(self.step, 3)
        elif not self.selected_semester:
            self.step = max(self.step, 4)
        yield rx.call_script(SCROLL_TO_BOTTOM_JS)

    @rx.event
    async def on_load_scope_page(self):
        """Called when navigating to /s/[scope].
        Minimum work for first paint: auth check, profile (1 DB call), scope routing.
        All scope hydration is deferred to post_render_hydrate_scope (background).
        """
        uid = self._uid()
        self._cached_uid = uid
        if uid < 0:
            yield AppState.auth_redir()  # type: ignore
            return

        # ── Single DB call: profile + memory (needed for is_started, degree, name) ──
        try:
            self._load_profile(uid)
        except Exception as e:
            print(f"[ROUTE] profile load error: {e}")

        # ── Scope routing (no DB) ──
        raw_scope = str(self.router.page.params.get("scope", "home") or "home").strip()
        scope_info = SCOPE_ROUTE_MAP.get(raw_scope)
        if scope_info is None:
            yield _hard_navigate("/s/home")
            return

        if not self.is_started:
            yield rx.redirect(APP_DASHBOARD_ROUTE)
            return

        year = scope_info["year"]
        semester = scope_info["semester"]
        view_mode = scope_info["view_mode"]

        # ── Set shell state (no DB) ──
        self.view_mode = view_mode
        self.active_scope = raw_scope
        if view_mode == "semester":
            self.selected_year = year
            self.selected_semester = semester
        self.show_semester_sidebar = False
        self.chat_history = []
        self.sessions = []
        self.current_session_id = ""
        self.current_session_choice = ""
        self.is_generating_plan = False
        self.plan_generation_error = ""
        self.is_processing = False
        self.current_day = 1
        self.current_topic_index = 0
        self.scope_hydrating = True

        # ══ FIRST PAINT ══  shell is now visible
        yield
        yield rx.call_script(ENTER_TO_SEND_JS)

        # ── Defer all scope data loading to background ──
        yield AppState.post_render_hydrate_scope(raw_scope, year, semester, view_mode)

    @rx.event(background=True)
    async def post_render_hydrate_scope(self, raw_scope: str, year: str, semester: str, view_mode: str):
        """Background: loads sessions, chat history, progress, plan state.
        Runs after the semester shell is already visible and interactive.
        """
        async with self:
            uid = self._uid()
            if uid < 0:
                self.scope_hydrating = False
                return

            # ── Profile extras ──
            try:
                self.adaptive_profile = self._get_adaptive_profile(uid)
                self._migrate_legacy_messages_once(uid)
            except Exception as e:
                print(f"[HYDRATE] profile extras error: {e}")

            # Infer name if missing
            if not (self.name or "").strip():
                inferred_name = _extract_person_name(
                    self.account_display_name, self.memory_summary, self.adaptive_profile,
                )
                if inferred_name:
                    self.name = inferred_name
            self._save_memory(uid)

            # ── Load scope data (sessions, chat history) ──
            try:
                self._ensure_scope_memory(uid, raw_scope)
                self._ensure_session(uid, raw_scope)
                self._load_sessions(uid, raw_scope)
                self._load_messages(uid)
                print(f"[HYDRATE] Loaded {len(self.chat_history)} msgs for scope {raw_scope}")
            except Exception as e:
                print(f"[HYDRATE] ERROR loading scope {raw_scope}: {e}")

            # ── Semester: load progress + existing plan ──
            if view_mode == "semester" and year:
                try:
                    self._ensure_progress_for_year(uid, year)
                    self._refresh_today_plan(uid)
                    existing_plan = self._get_study_plan(uid, raw_scope)
                    if existing_plan and not self._plan_matches_semester(existing_plan, year, semester):
                        self._reset_plan_only(uid, raw_scope)
                        existing_plan = []
                    if existing_plan:
                        self._set_plan_generation_state(uid, raw_scope, PLAN_GENERATION_STATUS_IDLE)
                        day, topic_idx = self._get_day_progress(uid, raw_scope)
                        self.current_day = day
                        self.current_topic_index = topic_idx
                        today_msg = self._build_today_message(existing_plan, day, topic_idx)
                        if not self.chat_history:
                            self.chat_history.append({"role": "assistant", "content": today_msg})
                            self._save_message(uid, "assistant", today_msg)
                    else:
                        self.current_day = 1
                        self.current_topic_index = 0
                except Exception as e:
                    print(f"[HYDRATE] ERROR loading plan data for {raw_scope}: {e}")

            # ── Mark hydration complete ──
            self.scope_hydrating = False

        # ── Post-hydration JS (scroll, observer) ──
        yield rx.call_script(SCROLL_TO_BOTTOM_JS)
        yield rx.call_script(AUTO_SCROLL_OBSERVER_JS)

        # ── Defer plan generation check ──
        if view_mode == "semester" and year:
            yield AppState.post_render_check_plan(raw_scope, year, semester)

    @rx.event(background=True)
    async def post_render_check_plan(self, scope: str, year: str, semester: str):
        """Runs after hydration. Checks whether plan generation is needed."""
        async with self:
            uid = self._uid()
            if uid < 0 or not scope:
                return

            existing_plan = self._get_study_plan(uid, scope)
            if existing_plan:
                self.is_generating_plan = False
                self.plan_generation_error = ""
                return

            if not self._has_curriculum_for_semester(year, semester):
                self._set_plan_generation_state(uid, scope, PLAN_GENERATION_STATUS_IDLE)
                empty_msg = (
                    f"{semester} is now your main AI workspace.\n\n"
                    "This semester does not have course data yet, so the guided study plan "
                    "cannot be generated until the curriculum is added."
                )
                if not self.chat_history:
                    self.chat_history.append({"role": "assistant", "content": empty_msg})
                    self._save_message(uid, "assistant", empty_msg)
                return

            status, error_text, updated_at = self._get_plan_generation_state(uid, scope)

            if status == PLAN_GENERATION_STATUS_RUNNING and not self._plan_generation_is_stale(updated_at):
                self.is_generating_plan = True
                self.plan_generation_error = ""

        # Watch outside the lock so UI stays responsive
        if status == PLAN_GENERATION_STATUS_RUNNING and not self._plan_generation_is_stale(updated_at):
            yield AppState.watch_study_plan_generation(scope)
            return

        async with self:
            if status == PLAN_GENERATION_STATUS_FAILED or self._plan_generation_is_stale(updated_at):
                self._set_plan_generation_state(uid, scope, PLAN_GENERATION_STATUS_FAILED, error_text or PLAN_GENERATION_FAILURE_TEXT)
                self.is_generating_plan = False
                self.plan_generation_error = error_text or PLAN_GENERATION_FAILURE_TEXT
                return

            self._set_plan_generation_state(uid, scope, PLAN_GENERATION_STATUS_RUNNING)
            self.is_generating_plan = True
            self.plan_generation_error = ""

        yield AppState.generate_study_plan(scope, year, semester)

    @rx.event
    async def new_chat(self):
        uid = self._uid()
        if uid < 0: return
        try:
            with rx.session() as session:
                sess = ChatSession(user_id=uid, scope=self.active_scope, title="New chat")  # type: ignore
                session.add(sess); session.commit(); session.refresh(sess)
                self.current_session_id = str(sess.id)
                self.current_session_choice = f"{sess.id}::New chat"
            self._load_sessions(uid, self.active_scope)
            # NEW: reset to empty state (no welcome message stored)
            self.chat_history = []
        except Exception as e:
            print(f"ERROR new_chat: {e}")

    @rx.event
    async def switch_chat(self, session_id: str):
        uid = self._uid()
        if uid < 0: return
        try:
            if not self._session_in_scope(uid, int(session_id), self.active_scope):
                return
            self.current_session_id = session_id
            self._load_messages(uid)
        except Exception as e:
            print(f"ERROR switch_chat: {e}")
        yield rx.call_script(SCROLL_TO_BOTTOM_JS)

    @rx.event
    def set_chat_input(self, value: str):
        self.chat_input = value

    @rx.event
    def next_step(self):
        uid = self._uid()
        try:
            self.onboarding_message = ""
            self.step = min(self.step + 1, ONBOARDING_FINAL_STEP)
            self._save_memory(uid)
        except Exception as e:
            print(f"ERROR next_step: {e}")

    @rx.event
    def advance_from_degree(self):
        uid = self._uid()
        try:
            if self.degree not in self.options:
                self.step = 1
                self.onboarding_message = "Please choose your degree first so Alex can build the right study path for you."
                self._save_memory(uid)
                return
            self.onboarding_message = ""
            self.step = 2
            self._save_memory(uid)
        except Exception as e:
            print(f"ERROR advance_from_degree: {e}")

    @rx.event
    def advance_from_name(self):
        uid = self._uid()
        try:
            normalized_name = _normalize_person_name(self.name)
            condensed_name = re.sub(r"[\s'-]", "", normalized_name)

            if not normalized_name:
                self.step = 2
                self.onboarding_message = "Please enter your name so Alex knows how to address you professionally."
                self._save_memory(uid)
                return
            if any(ch.isdigit() for ch in normalized_name):
                self.step = 2
                self.onboarding_message = "Names should only contain letters, so please remove any numbers and try again."
                self._save_memory(uid)
                return
            if len(condensed_name) < 2:
                self.step = 2
                self.onboarding_message = "Please enter at least two letters so the name looks complete."
                self._save_memory(uid)
                return
            if not ONBOARDING_NAME_PATTERN.fullmatch(normalized_name):
                self.step = 2
                self.onboarding_message = "Please use letters, spaces, apostrophes, or hyphens only for your name."
                self._save_memory(uid)
                return

            self.name = normalized_name
            self.onboarding_message = ""
            self.step = 3
            self._save_memory(uid)
        except Exception as e:
            print(f"ERROR advance_from_name: {e}")

    @rx.event
    def advance_from_year(self):
        uid = self._uid()
        try:
            if not self.selected_year:
                self.step = 3
                self.onboarding_message = "Choose your current academic year to keep the plan matched to your progress."
                self._save_memory(uid)
                return
            self.onboarding_message = ""
            self.step = 4
            self._save_memory(uid)
        except Exception as e:
            print(f"ERROR advance_from_year: {e}")

    @rx.event
    def advance_from_semester(self):
        uid = self._uid()
        try:
            if not self.selected_year:
                self.step = 3
                self.onboarding_message = "Please select your year first, then we can open the correct semester."
                self._save_memory(uid)
                return
            if not self.selected_semester:
                self.step = 4
                self.onboarding_message = "Pick the semester you want Alex to open so we can continue."
                self._save_memory(uid)
                return
            self.onboarding_message = ""
            self.step = 5
            self._save_memory(uid)
        except Exception as e:
            print(f"ERROR advance_from_semester: {e}")

    @rx.event
    def set_degree(self, value: str):
        uid = self._uid()
        try:
            self.degree = value if value in self.options else ""
            self.onboarding_message = ""
            self._save_memory(uid)
        except Exception as e:
            print(f"ERROR set_degree: {e}")

    @rx.event
    def set_year(self, year: str):
        uid = self._uid()
        try:
            if year not in SEMESTER_NAVIGATION:
                self.selected_year = ""
                self.selected_semester = ""
                self.active_scope = ""
                self._save_memory(uid)
                return
            self.status_text = ""
            self.selected_year = year
            if self.selected_semester not in SEMESTER_NAVIGATION.get(year, []):
                self.selected_semester = ""
            if self.selected_semester and self.is_started:
                scope = self._set_default_semester_workspace(uid, year, self.selected_semester)
                return _hard_navigate(scope_to_route(scope))
            elif self.selected_semester:
                self._set_default_semester_workspace(uid, year, self.selected_semester)
            self._save_memory(uid)
            self._ensure_progress_for_year(uid, year)
            self._refresh_today_plan(uid)
        except Exception as e:
            print(f"ERROR set_year: {e}")

    @rx.event
    def choose_onboarding_year(self, year: str):
        uid = self._uid()
        try:
            if year not in SEMESTER_NAVIGATION:
                self.step = 3
                self.onboarding_message = "Please choose one of the listed academic years to continue."
                self._save_memory(uid)
                return
            self.status_text = ""
            self.onboarding_message = ""
            self.selected_year = year
            if self.selected_semester not in SEMESTER_NAVIGATION.get(year, []):
                self.selected_semester = ""
            self.step = 4
            self._save_memory(uid)
        except Exception as e:
            print(f"ERROR choose_onboarding_year: {e}")

    @rx.event
    def set_selected_semester(self, semester: str):
        uid = self._uid()
        try:
            if not self.selected_year:
                return
            if semester not in SEMESTER_NAVIGATION.get(self.selected_year, []):
                return
            scope = self._set_default_semester_workspace(uid, self.selected_year, semester)
            if self.is_started:
                return _hard_navigate(scope_to_route(scope))
        except Exception as e:
            print(f"ERROR set_selected_semester: {e}")

    @rx.event
    def choose_onboarding_semester(self, semester: str):
        uid = self._uid()
        try:
            if not self.selected_year:
                self.step = 3
                self.onboarding_message = "Please select your year first so the semester list stays accurate."
                self._save_memory(uid)
                return
            if semester not in SEMESTER_NAVIGATION.get(self.selected_year, []):
                self.step = 4
                self.onboarding_message = "That semester does not match your selected year, so please choose one from the list below."
                self._save_memory(uid)
                return
            self._set_default_semester_workspace(uid, self.selected_year, semester)
            self.onboarding_message = ""
            self.step = 5
            self._save_memory(uid)
        except Exception as e:
            print(f"ERROR choose_onboarding_semester: {e}")

    @rx.event
    def back_to_onboarding_year(self):
        uid = self._uid()
        try:
            self.step = 3
            self.selected_semester = ""
            self.onboarding_message = ""
            self._save_memory(uid)
        except Exception as e:
            print(f"ERROR back_to_onboarding_year: {e}")

    @rx.event
    def back_to_years(self):
        uid = self._uid()
        try:
            self.selected_year = ""
            self.selected_semester = ""
            self.active_scope = ""
            self.status_text = ""
            self.onboarding_message = ""
            self._save_memory(uid)
        except Exception as e:
            print(f"ERROR back_to_years: {e}")

    @rx.event
    async def start_app(self):
        uid = self._uid()
        try:
            self.is_started = True
            if not self.selected_year:
                self.step = max(self.step, 3)
                self.onboarding_message = "Please choose your year before Alex opens your study workspace."
                self._save_memory(uid)
                return
            if not self.selected_semester:
                self.step = max(self.step, 4)
                self.onboarding_message = "Please select a semester so Alex can open the correct study plan."
                self._save_memory(uid)
                return
            self.onboarding_message = ""
            scope = self._set_default_semester_workspace(uid, self.selected_year, self.selected_semester)
            yield _hard_navigate(scope_to_route(scope))
        except Exception as e:
            print(f"ERROR start_app: {e}")

    @rx.event
    async def open_semester(self, semester: str):
        uid = self._uid()
        if uid < 0 or not self.selected_year:
            return
        scope = self._set_default_semester_workspace(uid, self.selected_year, semester)
        yield _hard_navigate(scope_to_route(scope))

    @rx.event
    async def open_dashboard_semester(self, year: str, semester: str):
        uid = self._uid()
        if uid < 0:
            return
        scope = self._set_default_semester_workspace(uid, year, semester)
        yield _hard_navigate(scope_to_route(scope))

    @rx.event(background=True)
    async def generate_study_plan(self, scope: str = "", year: str = "", semester: str = ""):
        # ── Read state under lock ──
        async with self:
            uid = self._uid()
            target_scope = (scope or self.active_scope).strip()
            target_year = year or self.selected_year
            target_semester = semester or self.selected_semester
            active = self.active_scope
            degree = self.degree
            print(f"[PLAN-GEN] START uid={uid} scope={target_scope} year={target_year} sem={target_semester} client={'ok' if client else 'None'}", flush=True)
            if uid < 0 or client is None or not target_scope:
                print(f"[PLAN-GEN] BAIL: uid={uid} client={'ok' if client else 'None'} scope='{target_scope}'", flush=True)
                if target_scope == active:
                    self.is_generating_plan = False
                    self.plan_generation_error = PLAN_GENERATION_FAILURE_TEXT
                return
            if self._get_study_plan(uid, target_scope):
                print(f"[PLAN-GEN] BAIL: plan already exists for {target_scope}", flush=True)
                self._set_plan_generation_state(uid, target_scope, PLAN_GENERATION_STATUS_IDLE)
                if target_scope == active:
                    self.is_generating_plan = False
                    self.plan_generation_error = ""
                return
            courses_text = "\n".join(self._semester_courses(target_year, target_semester))
            if not target_year or not target_semester or not courses_text.strip():
                print(f"[PLAN-GEN] BAIL: no courses year='{target_year}' sem='{target_semester}'", flush=True)
                self._set_plan_generation_state(
                    uid, target_scope, PLAN_GENERATION_STATUS_FAILED,
                    "This semester is not ready for study plan generation yet.",
                )
                if target_scope == active:
                    self.is_generating_plan = False
                    self.plan_generation_error = "This semester is not ready for study plan generation yet."
                return

        # ── AI call outside lock — page stays fully interactive ──
        print(f"[PLAN-GEN] Calling Groq for {target_scope}...", flush=True)
        try:
            prompt = f"""You are a university curriculum expert for {degree} students
Generate a realistic detailed 110 day study plan for {target_year} {target_semester}.
Use only the following semester subjects and do not include modules from any other semester.
Return ONLY a valid JSON array with exactly 110 items
Each item: {{"day":<1-110>,"subject":"<n>","unit":"<unit>","topics":["<t1>","<t2>"]}}
Subjects:\n{courses_text}"""
            resp = await asyncio.to_thread(_groq_generate, GEMINI_FAST_MODEL, prompt, 8192)
            raw_text = (getattr(resp, "text", "") or "").strip()
            print(f"[PLAN-GEN] Groq response len={len(raw_text)} first100='{raw_text[:100]}'", flush=True)
        except Exception as e:
            print(f"[PLAN-GEN] ERROR AI call: {e}", flush=True)
            raw_text = ""

        # ── Process result under lock ──
        async with self:
            active = self.active_scope
            try:
                if not raw_text:
                    raise ValueError("Empty AI response")
                if raw_text in (RATE_LIMIT_UI_MESSAGE, GENERIC_ERROR_UI_MESSAGE) or _is_rate_limit_text(raw_text):
                    raise ValueError(f"API error response: {raw_text[:80]}")
                plan = self._extract_json_list(raw_text)
                print(f"[PLAN-GEN] Parsed plan: {len(plan)} entries", flush=True)
                if not plan or len(plan) < 10:
                    print(f"[PLAN-GEN] FAIL: plan too short ({len(plan)} items)", flush=True)
                    self._set_plan_generation_state(
                        uid, target_scope,
                        PLAN_GENERATION_STATUS_FAILED, PLAN_GENERATION_FAILURE_TEXT,
                    )
                    if target_scope == active:
                        self.is_generating_plan = False
                        self.plan_generation_error = PLAN_GENERATION_FAILURE_TEXT
                    return
                self._save_study_plan(uid, target_scope, plan)
                self._save_day_progress(uid, target_scope, 1, 0)
                self._set_plan_generation_state(uid, target_scope, PLAN_GENERATION_STATUS_IDLE)
                print(f"[PLAN-GEN] SUCCESS: saved {len(plan)} entries for {target_scope}", flush=True)
                if target_scope == active:
                    self.current_day = 1
                    self.current_topic_index = 0
                    self._refresh_today_plan(uid)
                    self.plan_generation_error = ""
                    msg = "Your personalized 110 day study plan is ready\n\n" + self._build_today_message(plan, 1, 0)
                    self.chat_history.append({"role": "assistant", "content": msg})
                    self._save_message(uid, "assistant", msg)
            except Exception as e:
                print(f"[PLAN-GEN] ERROR processing: {e}", flush=True)
                self._set_plan_generation_state(
                    uid, target_scope,
                    PLAN_GENERATION_STATUS_FAILED, PLAN_GENERATION_FAILURE_TEXT,
                )
                if target_scope == active:
                    self.plan_generation_error = PLAN_GENERATION_FAILURE_TEXT
            if target_scope == active:
                self.is_generating_plan = False


    @rx.event
    async def watch_study_plan_generation(self, scope: str = ""):
        uid = self._uid()
        target_scope = (scope or self.active_scope).strip()
        if uid < 0 or not target_scope or target_scope != self.active_scope:
            return

        plan = self._get_study_plan(uid, target_scope)
        if plan:
            self._set_plan_generation_state(uid, target_scope, PLAN_GENERATION_STATUS_IDLE)
            day, topic_idx = self._get_day_progress(uid, target_scope)
            self.current_day = day
            self.current_topic_index = topic_idx
            self._refresh_today_plan(uid)
            self._load_sessions(uid, target_scope)
            self._load_messages(uid, target_scope)
            if not self.chat_history:
                today_msg = self._build_today_message(plan, day, topic_idx)
                self.chat_history.append({"role": "assistant", "content": today_msg})
                self._save_message(uid, "assistant", today_msg, target_scope)
            self.is_generating_plan = False
            self.plan_generation_error = ""
            yield rx.call_script(SCROLL_TO_BOTTOM_JS)
            return

        status, error_text, updated_at = self._get_plan_generation_state(uid, target_scope)
        if status == PLAN_GENERATION_STATUS_RUNNING and not self._plan_generation_is_stale(updated_at):
            self.is_generating_plan = True
            self.plan_generation_error = ""
            await asyncio.sleep(3)
            if target_scope == self.active_scope:
                yield AppState.watch_study_plan_generation(target_scope)
            return

        if status == PLAN_GENERATION_STATUS_FAILED or self._plan_generation_is_stale(updated_at):
            error_message = error_text or PLAN_GENERATION_FAILURE_TEXT
            self._set_plan_generation_state(uid, target_scope, PLAN_GENERATION_STATUS_FAILED, error_message)
            self.is_generating_plan = False
            self.plan_generation_error = error_message
            return

        self.is_generating_plan = False
        self.plan_generation_error = ""

    @rx.event
    async def retry_study_plan_generation(self):
        uid = self._uid()
        print(f"[PLAN-RETRY] uid={uid} view_mode={self.view_mode} scope={self.active_scope} year={self.selected_year} sem={self.selected_semester}", flush=True)
        if uid < 0 or self.view_mode != "semester" or not self.active_scope:
            print(f"[PLAN-RETRY] BAIL: precondition failed", flush=True)
            return
        if self._get_study_plan(uid, self.active_scope):
            print(f"[PLAN-RETRY] BAIL: plan already exists", flush=True)
            self._set_plan_generation_state(uid, self.active_scope, PLAN_GENERATION_STATUS_IDLE)
            self.is_generating_plan = False
            self.plan_generation_error = ""
            return

        status, _, updated_at = self._get_plan_generation_state(uid, self.active_scope)
        print(f"[PLAN-RETRY] gen state: status={status} updated_at={updated_at}", flush=True)
        if status == PLAN_GENERATION_STATUS_RUNNING and not self._plan_generation_is_stale(updated_at):
            print(f"[PLAN-RETRY] BAIL: already running and not stale", flush=True)
            self.is_generating_plan = True
            self.plan_generation_error = ""
            return

        self._set_plan_generation_state(uid, self.active_scope, PLAN_GENERATION_STATUS_RUNNING)
        self.is_generating_plan = True
        self.plan_generation_error = ""
        print(f"[PLAN-RETRY] Dispatching generate_study_plan...", flush=True)
        yield
        yield AppState.generate_study_plan(
            self.active_scope,
            self.selected_year,
            self.selected_semester,
        )

    @rx.event
    async def go_home(self):
        uid = self._uid()
        if uid < 0: return
        self.active_scope = "home"
        self.view_mode = "home"
        self.show_semester_sidebar = False
        self._save_memory(uid)
        self._switch_scope(uid, "home")
        yield _hard_navigate("/s/home")

    @rx.event
    async def send_message(self):
        uid = self._uid()
        if uid < 0 or not self.chat_input.strip():
            return

        # Scope safety: ensure current session belongs to active scope.
        # If it doesn't (e.g. stale state after a failed scope switch), fix it now.
        if self.current_session_id and self.active_scope:
            try:
                if not self._session_in_scope(uid, int(self.current_session_id), self.active_scope):
                    print(f"[send_message] session {self.current_session_id} doesn't match scope {self.active_scope}, re-syncing")
                    self._ensure_session(uid, self.active_scope)
                    self._load_messages(uid)
            except Exception as e:
                print(f"[send_message] scope check error: {e}")

        self._check_and_reset_daily_count(uid)

        if not self.can_send_message:
            gate_msg = "🔒 You've used all 5 free messages for today.\n\nUpgrade to **Premium** to continue learning without limits."
            self.chat_history.append({"role": "assistant", "content": gate_msg})
            self._save_message(uid, "assistant", gate_msg)
            self.show_pricing_modal = True
            yield rx.call_script(SCROLL_TO_BOTTOM_JS)
            return

        if client is None:
            self.chat_history.append({"role": "assistant", "content": "API key missing — set GROQ_API_KEY in env."})
            return

        user_msg = self.chat_input.strip()
        self.chat_input = ""
        self.is_processing = True

        if (not self.has_premium_access) and (not self.is_in_trial):
            self._increment_daily_count(uid)

        model_to_use = self.active_model_name
        adaptive_profile = (self.adaptive_profile or "").strip() or self._get_adaptive_profile(uid)
        self.adaptive_profile = adaptive_profile
        if not (self.name or "").strip():
            inferred_name = _extract_person_name(
                self.account_display_name,
                self.memory_summary,
                adaptive_profile,
            )
            if inferred_name:
                self.name = inferred_name
        student_name = _normalize_person_name(self.name) or "Student"

        try:
            self.chat_history.append({"role": "user", "content": user_msg})
            self._save_message(uid, "user", user_msg)
            yield
            yield rx.call_script(SCROLL_TO_BOTTOM_JS)
            yield

            if self.current_session_id:
                sid = int(self.current_session_id)
                with rx.session() as db_sess:
                    sess_row = db_sess.exec(select(ChatSession).where(ChatSession.id == sid)).one_or_none()
                    needs_title = sess_row is not None and sess_row.title == "New chat"
                if needs_title:
                    try:
                        title_resp = await asyncio.to_thread(
                            _groq_generate,
                            GEMINI_FAST_MODEL,
                            f'Give a short 3-5 word title for: "{user_msg}". Reply with ONLY the title.',
                        )
                        new_title = (getattr(title_resp, "text", "") or "").strip()[:60]
                        if new_title:
                            with rx.session() as db_sess:
                                sr = db_sess.exec(select(ChatSession).where(ChatSession.id == sid)).one_or_none()
                                if sr:
                                    sr.title = new_title
                                    db_sess.add(sr)
                                    db_sess.commit()
                            self._load_sessions(uid, self.active_scope)
                    except Exception as te:
                        print(f"ERROR auto_title: {te}")

        except Exception as e:
            print(f"ERROR save user msg: {e}")

        yield rx.call_script(SCROLL_TO_BOTTOM_JS)

        guardrail_reply = self._alex_guardrail_reply(user_msg, student_name)
        if guardrail_reply:
            self.chat_history.append({"role": "assistant", "content": guardrail_reply})
            self._save_message(uid, "assistant", guardrail_reply)
            self.is_processing = False
            await self._maybe_auto_update_scope_summary(uid, self.active_scope)
            await self._maybe_auto_update_global_memory(uid)
            await self._maybe_auto_update_adaptive_profile(uid)
            yield rx.call_script(SCROLL_TO_BOTTOM_JS)
            return

        # ============================
        # SEMESTER MODE
        # ============================
        if self.view_mode == "semester" and self.active_scope != "home":
            scope = self.active_scope
            plan = self._get_study_plan(uid, scope)
            if plan:
                day, topic_idx = self.current_day, self.current_topic_index

                if self._detect_show_full_plan_intent(user_msg):
                    full_text = "Your Full 110 Day Study Plan\n\n"
                    cur_subj = ""
                    for entry in plan:
                        if entry.get("subject") != cur_subj:
                            cur_subj = entry.get("subject", "")
                            full_text += f"\n{cur_subj}\n"
                        d = entry.get("day")
                        full_text += f"Day {d} | {entry.get('unit','')} | {', '.join(entry.get('topics',[]))}{'  TODAY' if d==day else ''}\n"
                    self.chat_history.append({"role": "assistant", "content": full_text})
                    self._save_message(uid, "assistant", full_text)
                    self.is_processing = False
                    yield rx.call_script(SCROLL_TO_BOTTOM_JS)
                    return

                if self._detect_edit_plan_intent(user_msg):
                    try:
                        resp = await asyncio.to_thread(
                            _groq_generate,
                            model_to_use,
                            f"User wants to edit plan. Current (first 20): {json.dumps(plan[:20])}. Request: {user_msg}. Confirm what to edit.",
                        )
                        bot_text = (getattr(resp, "text", "") or "").strip()
                    except Exception:
                        bot_text = "Tell me which day or subject you want to change"
                    self.chat_history.append({"role": "assistant", "content": bot_text})
                    self._save_message(uid, "assistant", bot_text)
                    self.is_processing = False
                    yield rx.call_script(SCROLL_TO_BOTTOM_JS)
                    return

                if self._detect_next_topic_intent(user_msg):
                    entry = self._get_today_entry(plan, day)
                    topics = entry.get("topics", [])
                    if topic_idx + 1 < len(topics):
                        topic_idx += 1
                        self.current_topic_index = topic_idx
                        self._save_day_progress(uid, scope, day, topic_idx)
                        remaining = topics[topic_idx:]
                        msg = f"Moving to the next topic\n\nDay {day}/110 | {entry.get('subject','')} | {entry.get('unit','')}\n\nCurrent topic {topics[topic_idx]}\n"
                        if len(remaining) > 1:
                            msg += f"Still today {', '.join(remaining[1:])}\n"
                        msg += "\nAsk me anything about this topic"
                    else:
                        next_day = day + 1
                        if next_day > 110:
                            msg = "You have completed all 110 days"
                        else:
                            self.current_day = next_day
                            self.current_topic_index = 0
                            self._save_day_progress(uid, scope, next_day, 0)
                            msg = f"Day {day} complete\n\n" + self._build_today_message(plan, next_day, 0)

                    self.chat_history.append({"role": "assistant", "content": msg})
                    self._save_message(uid, "assistant", msg)
                    self.is_processing = False
                    yield rx.call_script(SCROLL_TO_BOTTOM_JS)
                    return

                entry = self._get_today_entry(plan, day)
                topics = entry.get("topics", [])
                current_topic = topics[topic_idx] if topic_idx < len(topics) else ""
                semester_courses = ", ".join(self._current_courses_for_scope())

                scope_summary = self._get_scope_summary(uid, scope)
                recent_text = "\n".join([f'{m["role"]}: {m["content"]}' for m in self.chat_history[-14:]])
                past_hits = self._past_hits_text(uid, scope, user_msg)

                teach_prompt = f"""You are Alex, a friendly and patient Software Engineering mentor helping a {self.degree} student.

Current context:
- Selected year: {self.selected_year}
- Selected semester: {self.selected_semester}
- Active semester workspace: {self.selected_year}, {self.selected_semester}
- Semester modules: {semester_courses}
- Current day: {day}/110
- Current subject: {entry.get("subject","")}
- Current unit: {entry.get("unit","")}
- Current topic: {current_topic}
- Semester scope summary: {scope_summary}
- Long-term student memory: {self.memory_summary}
- Adaptive profile from previous chats: {adaptive_profile}
- Recent conversation: {recent_text}
- Past relevant chat (db search): {past_hits}
- Student just said: {user_msg}

Your response style rules:
1. Stay warm, patient, mentor-like, and encouraging without sounding cheesy.
2. Answer directly first, then add depth only when it helps.
3. Stay strictly inside the active semester workspace above unless the student explicitly asks to compare another semester.
4. Adapt to the adaptive profile, semester scope summary, and long-term student memory before deciding tone, depth, examples, and formatting.
5. If the profile says the user prefers short answers, keep replies tighter and avoid extra theory.
6. If the profile says the user likes steps or bullets, use that format first before paragraphs.
7. If the profile says the user prefers examples, always include at least one concrete example.
8. If the profile says the user struggles with this topic or a related prerequisite, slow down, simplify, define terms clearly, and build up in smaller steps.
9. If the profile says revision is needed, briefly reconnect this explanation to that weaker concept before moving forward.
10. Match the practice checkpoint to the user's likely difficulty level from the adaptive profile.
11. Explain the concept simply first in 1-2 sentences, then go one level deeper.
12. Use short paragraphs or bullets and avoid walls of text.
13. Keep replies focused and usually around 120-200 words unless code or a careful step breakdown genuinely needs more.
14. End with one small practice question, quick check, or next step.
15. If the student seems confused, immediately simplify and use an analogy or concrete example.
16. If the student makes a mistake, correct gently with wording like "Almost. Try thinking of it this way..."
17. Use {student_name} naturally so the tutoring feels personal.
18. Acknowledge progress occasionally by connecting the explanation to Day {day}/110.
19. If code is needed, wrap it in fenced markdown code blocks with the correct language.
20. If the question is technically complex, give a numbered breakdown before the final explanation or code.
21. If you use a career example or analogy, prefer grounded Sri Lankan Software Engineering context when it fits naturally."""

                assistant_index = len(self.chat_history)
                self.chat_history.append({"role": "assistant", "content": ""})
                yield
                yield rx.call_script(SCROLL_TO_BOTTOM_JS)

                buf = ""
                last_scroll = 0
                final_text = ""
                groq_messages = [
                    {"role": "system", "content": self._alex_system_prompt(student_name)},
                    {"role": "user", "content": teach_prompt},
                ]

                try:
                    async for piece in _groq_stream_async(
                        model_to_use,
                        groq_messages,
                        max_tokens=2048,
                    ):
                        buf += piece

                        safe_live_text = sanitize_for_ui(buf)
                        if safe_live_text != buf:
                            final_text = safe_live_text
                            self.chat_history[assistant_index]["content"] = final_text
                            yield
                            yield rx.call_script(SCROLL_TO_BOTTOM_JS)
                            break

                        self.chat_history[assistant_index]["content"] = buf
                        yield

                        if len(buf) - last_scroll >= 220:
                            last_scroll = len(buf)
                            yield rx.call_script(SCROLL_TO_BOTTOM_JS)

                    if not final_text:
                        final_text = sanitize_for_ui(buf.strip() or "Empty reply please try again")
                        self.chat_history[assistant_index]["content"] = final_text

                except Exception as e:
                    print(f"ERROR stream: {e}")
                    final_text = friendly_groq_error(e)
                    self.chat_history[assistant_index]["content"] = final_text

                finally:
                    inferred_name = _extract_person_name(
                        self.name,
                        self.account_display_name,
                        final_text,
                        self.memory_summary,
                        adaptive_profile,
                    )
                    if inferred_name and inferred_name != self.name:
                        self.name = inferred_name
                        self._save_memory(uid)
                    self._save_message(uid, "assistant", final_text)
                    _append_training_example(uid, self.active_scope, user_msg, final_text)
                    self.is_processing = False
                    await self._maybe_auto_update_scope_summary(uid, self.active_scope)
                    await self._maybe_auto_update_global_memory(uid)
                    await self._maybe_auto_update_adaptive_profile(uid)
                    yield rx.call_script(SCROLL_TO_BOTTOM_JS)

                return

        # ============================
        # HOME MODE
        # ============================
        recent_text = "\n".join([f'{m["role"]}: {m["content"]}' for m in self.chat_history[-14:]])
        scope_summary = self._get_scope_summary(uid, self.active_scope)
        all_scopes = self._get_all_scope_summaries_text(uid) if self.active_scope == "home" else ""
        next_courses = self._get_next_courses(uid, self.selected_year, 3) if self.selected_year else []
        past_hits = self._past_hits_text(uid, self.active_scope, user_msg)

        prompt = f"""You are Alex AI, the central academic growth assistant inside the platform.
Your main job is to analyze the student's learning journey across semesters,
summarize progress,
identify weak and strong areas,
answer questions about growth, momentum, current direction, and academic status,
and guide the student to the right semester section when needed.

Student context:
- Degree: {self.degree}
- Saved current year: {self.selected_year}
- Saved current semester: {self.selected_semester}
- Long-term memory: {self.memory_summary}
- Adaptive profile: {adaptive_profile}
- Home scope summary: {scope_summary}
- All semester scope summaries: {all_scopes}
- Today's plan: {self.today_plan}
- Upcoming courses: {chr(10).join(next_courses)}
- Recent home chat: {recent_text}
- Relevant past chat memory: {past_hits}
- Student just said: {user_msg}

Behavior rules:
1. In home mode, focus on overview, analysis, redirection, and academic guidance. Do not pretend to be the daily semester tutor.
2. If the user asks about growth or progress, summarize from all available semester scope summaries, long-term memory, adaptive profile, and relevant past chat.
3. For growth or progress questions, structure the answer as:
   - Current snapshot
   - Strengths
   - Weak areas
   - Best next move
4. If the user asks what semester they are currently on, answer from the real saved current state above.
5. For semester-navigation questions, structure the answer as:
   - Current year/semester
   - Why
   - Best place to continue
6. If the user asks about strengths, identify them from memory, adaptive profile, and semester summaries. If evidence is missing, say so clearly.
7. If the user asks about weaknesses, identify them from memory, adaptive profile, and semester summaries. If evidence is missing, say so clearly.
8. If semester data is missing, say that clearly instead of inventing progress.
9. If the user asks a general academic question, answer normally, but keep the reply short and direct.
10. If the user asks a very specific semester-topic teaching question, answer briefly and also say exactly: "This is better handled in your semester section for deeper guided teaching."
11. If a semester is clearly the right place to continue, mention the matching year and semester directly.
12. Keep responses short, clean, and direct.
13. Use bullets first when they improve clarity. Avoid walls of text.
14. Use {student_name} naturally so the support feels personal.
15. Adapt to the adaptive profile for brevity, formatting, pace, and tone.
16. If code is needed, wrap it in fenced markdown code blocks with the correct language.
17. If the question is technically complex, give a short numbered breakdown before the final answer.
18. Stay honest about what the stored memory does and does not show."""

        assistant_index = len(self.chat_history)
        self.chat_history.append({"role": "assistant", "content": ""})
        yield
        yield rx.call_script(SCROLL_TO_BOTTOM_JS)

        buf = ""
        last_scroll = 0
        final_text = ""

        try:
            async for piece in _groq_stream_async(
                model_to_use,
                [
                    {"role": "system", "content": self._alex_system_prompt(student_name)},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2048,
            ):
                buf += piece

                safe_live_text = sanitize_for_ui(buf)
                if safe_live_text != buf:
                    final_text = safe_live_text
                    self.chat_history[assistant_index]["content"] = final_text
                    yield
                    yield rx.call_script(SCROLL_TO_BOTTOM_JS)
                    break

                self.chat_history[assistant_index]["content"] = buf
                yield

                if len(buf) - last_scroll >= 220:
                    last_scroll = len(buf)
                    yield rx.call_script(SCROLL_TO_BOTTOM_JS)

            if not final_text:
                final_text = sanitize_for_ui(buf.strip() or "Empty reply please try again")
                self.chat_history[assistant_index]["content"] = final_text

        except Exception as e:
            print(f"ERROR stream: {e}")
            final_text = friendly_groq_error(e)
            self.chat_history[assistant_index]["content"] = final_text

        finally:
            inferred_name = _extract_person_name(
                self.name,
                self.account_display_name,
                final_text,
                self.memory_summary,
                adaptive_profile,
            )
            if inferred_name and inferred_name != self.name:
                self.name = inferred_name
                self._save_memory(uid)
            self._save_message(uid, "assistant", final_text)
            _append_training_example(uid, self.active_scope, user_msg, final_text)
            self.is_processing = False
            await self._maybe_auto_update_scope_summary(uid, self.active_scope)
            await self._maybe_auto_update_global_memory(uid)
            await self._maybe_auto_update_adaptive_profile(uid)
            yield rx.call_script(SCROLL_TO_BOTTOM_JS)

        return

    
                
    @rx.event
    async def update_scope_summary(self):
        uid = self._uid()
        if uid < 0 or client is None: return
        try:
            scope = self.active_scope; self._ensure_scope_memory(uid, scope)
            recent_text = "\n".join([f'{m["role"]}: {m["content"]}' for m in self.chat_history[-20:]])
            current = self._get_scope_summary(uid, scope)
            resp = await asyncio.to_thread(_groq_generate, GEMINI_FAST_MODEL,
                contents=f"Update scope memory. Keep short facts only.\nScope: {scope}\nCurrent: {current}\nNew: {recent_text}\nReturn only updated summary.")
            new_sum = (getattr(resp,"text","") or "").strip()
            if new_sum: self._set_scope_summary(uid, scope, new_sum)
        except Exception as e: print(f"ERROR update_scope_summary: {e}")

    @rx.event
    async def update_memory_summary(self):
        uid = self._uid()
        if uid < 0 or client is None: return
        try:
            recent_text = "\n".join([f'{m["role"]}: {m["content"]}' for m in self.chat_history[-20:]])
            resp = await asyncio.to_thread(_groq_generate, GEMINI_FAST_MODEL,
                contents=f"Update long term memory summary. Keep short stable facts only.\nCurrent: {self.memory_summary}\nNew: {recent_text}\nReturn only updated memory text.")
            new_sum = (getattr(resp,"text","") or "").strip()
            if new_sum: self.memory_summary = new_sum[:4000]; self._save_memory(uid)
        except Exception as e: print(f"ERROR update_memory_summary: {e}")

    @rx.event
    def logout(self):
        self.app_auth_token = ""
        self._cached_uid = -1
        self.active_scope = ""
        return [reflex_local_auth.LocalAuthState.do_logout, rx.redirect(reflex_local_auth.routes.LOGIN_ROUTE)]


SCROLL_TO_BOTTOM_JS = """
(function(){
  const boxId = "chat_scroll";
  const anchorId = "chat_bottom_anchor";

  let tries = 0;
  let lastH = -1;
  let stable = 0;

  function tick(){
    const box = document.getElementById(boxId);
    const a = document.getElementById(anchorId);

    if (box) box.scrollTop = box.scrollHeight;
    if (a) try { a.scrollIntoView({ block: "end" }); } catch(e) {}

    if (box) {
      const h = box.scrollHeight;
      if (h === lastH) stable += 1;
      else { stable = 0; lastH = h; }
      if (stable >= 6) return;
    }

    tries += 1;
    if (tries < 180) requestAnimationFrame(tick);
  }
  tick();
})();
"""
ENTER_TO_SEND_JS = """
(function(){
  function attach(){
    var wrapper = document.getElementById("chat_input");
    if(!wrapper) return false;
    var ta = wrapper.tagName === "TEXTAREA" ? wrapper : wrapper.querySelector("textarea");
    if(!ta) return false;
    if(ta.dataset.enterSendAttached) return true;

    ta.dataset.enterSendAttached = "1";

    ta.addEventListener("keydown", function(e){
      if(e.key === "Enter" && !e.shiftKey){
        e.preventDefault();
        var btn = document.getElementById("chat_send_btn");
        if(btn && !btn.disabled){
          btn.click();
        }
        setTimeout(function(){ try{ ta.focus(); }catch(err){} }, 0);
      }
    });

    return true;
  }

  attach();
  var t = 0;
  var iv = setInterval(function(){
    if(attach() || ++t > 60) clearInterval(iv);
  }, 300);

  try{
    new MutationObserver(attach).observe(document.body,{childList:true,subtree:true});
  }catch(e){}
})();
"""

AUTO_SCROLL_OBSERVER_JS = """
(function(){
  function attach(){
    const box = document.getElementById("chat_scroll");
    if(!box || box.__autoScrollAttached) return true;
    box.__autoScrollAttached = true;

    let userLocked = false;
    const atBottom = () => (box.scrollHeight - box.scrollTop - box.clientHeight) < 80;

    box.addEventListener("scroll", () => {
      userLocked = !atBottom();
    }, { passive: true });

    const obs = new MutationObserver(() => {
      if (!userLocked) box.scrollTop = box.scrollHeight;
    });
    obs.observe(box, { childList: true, subtree: true, characterData: true });

    box.scrollTop = box.scrollHeight;
    return true;
  }

  let t = 0;
  const iv = setInterval(() => { if(attach() || ++t > 80) clearInterval(iv); }, 40);
})();
"""

# ═══════════════════════════════════════════════════════
# UI FIXES - Replace these functions in your alexai.py
# ═══════════════════════════════════════════════════════

# FIX 1: subject_button — crisper border, tighter look
def subject_button(label: str, on_click=None, is_active=False):
    return rx.button(
        label,
        width="100%",
        height="52px",
        variant="outline",
        color_scheme="green",
        on_click=on_click,
        style={
            "border": rx.cond(
                is_active,
                "1px solid rgba(52,211,153,0.78)",
                "1px solid rgba(0,255,136,0.35)",
            ),
            "background": rx.cond(
                is_active,
                "linear-gradient(135deg, rgba(7,34,22,0.98) 0%, rgba(12,82,50,0.94) 100%)",
                "rgba(0,255,136,0.04)",
            ),
            "text_transform": "uppercase",
            "font_weight": "600",
            "font_size": "0.82rem",
            "letter_spacing": "2px",
            "color": rx.cond(is_active, "#ecfff6", "rgba(255,255,255,0.88)"),
            "border_radius": "10px",
            "transition": "all 0.2s ease",
            "box_shadow": rx.cond(
                is_active,
                "0 10px 24px rgba(0,0,0,0.28), 0 0 0 1px rgba(52,211,153,0.18)",
                "none",
            ),
            "_hover": {
                "background": rx.cond(
                    is_active,
                    "linear-gradient(135deg, rgba(9,40,26,0.98) 0%, rgba(14,90,56,0.96) 100%)",
                    "rgba(0,255,136,0.1)",
                ),
                "border": rx.cond(
                    is_active,
                    "1px solid rgba(110,231,183,0.9)",
                    "1px solid rgba(0,255,136,0.7)",
                ),
                "color": rx.cond(is_active, "#f4fff9", "#00ff88"),
                "transform": "translateX(6px)",
            },
        },
    )
PASSWORD_EYE_JS = """(function(){function a(){return'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00ff88" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';}function b(){return'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00ff88" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';}function c(){try{if(!document.body)return;document.querySelectorAll('input[type="password"]:not([data-eye-attached])').forEach(function(inp){try{inp.setAttribute('data-eye-attached','1');var w=document.createElement('div');w.style.cssText='position:relative;display:block;width:100%;';inp.parentNode.insertBefore(w,inp);w.appendChild(inp);var btn=document.createElement('button');btn.type='button';btn.style.cssText='position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:none;padding:0;cursor:pointer;color:#00ff88;z-index:99999;display:flex;align-items:center;';btn.innerHTML=a();btn.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();inp.type=inp.type==='password'?(btn.innerHTML=b(),'text'):(btn.innerHTML=a(),'password');});w.appendChild(btn);inp.style.paddingRight='40px';}catch(e){}});}catch(e){}}c();var t=0,iv=setInterval(function(){c();if(++t>60)clearInterval(iv);},300);try{new MutationObserver(c).observe(document.body,{childList:true,subtree:true});}catch(e){}})();"""

def password_eye_script() -> rx.Component:
    return rx.script(PASSWORD_EYE_JS)


AUTH_TOKEN_BOOTSTRAP_JS = f"""
(function(){{
  try {{
    var u = new URL(window.location.href);
    var token = u.searchParams.get("auth_token");
    if(!token) return;
    try {{
      localStorage.setItem("{AUTH_TOKEN_LOCAL_STORAGE_KEY}", token);
    }} catch(e) {{}}
    u.searchParams.delete("auth_token");
    window.location.replace("{APP_DASHBOARD_ROUTE}");
  }} catch(e) {{}}
}})();
"""

def auth_token_bootstrap_script() -> rx.Component:
    return rx.script(AUTH_TOKEN_BOOTSTRAP_JS)


# ══════════════════════════════════════════════════════════════
# PRICING MODAL
# ══════════════════════════════════════════════════════════════
def plan_card(
    plan_num: int,
    icon: str,
    title: str,
    price: str,
    period: str,
    model_name: str,
    features: list[str],
    gradient: str,
    glow: str,
    is_recommended: bool = False,
    is_current: bool = False,
) -> rx.Component:
    return rx.box(
        rx.cond(
            is_current,
            rx.box(
                rx.text("✓ YOUR PLAN", font_size="0.65rem", font_weight="800", letter_spacing="2px", color="white"),
                position="absolute", top="-14px", left="50%", transform="translateX(-50%)",
                background="linear-gradient(90deg,#065f46,#10b981)",
                padding="4px 16px", border_radius="20px", white_space="nowrap",
            ),
            rx.cond(
                is_recommended,
                rx.box(
                    rx.text("✨ MOST POPULAR", font_size="0.65rem", font_weight="800", letter_spacing="2px", color="white"),
                    position="absolute", top="-14px", left="50%", transform="translateX(-50%)",
                    background="linear-gradient(90deg,#7c3aed,#a855f7)",
                    padding="4px 16px", border_radius="20px", white_space="nowrap",
                ),
                rx.fragment(),
            ),
        ),
        rx.vstack(
            rx.text(icon, font_size="2.2rem"),
            rx.text(title, font_size="1.1rem", font_weight="700", color="white", letter_spacing="0.5px"),
            rx.hstack(
                rx.text(price, font_size="2.5rem", font_weight="900", color="white"),
                rx.vstack(
                    rx.text("LKR", font_size="0.75rem", color="rgba(255,255,255,0.6)", font_weight="600"),
                    rx.text(period, font_size="0.7rem", color="rgba(255,255,255,0.45)"),
                    spacing="0", align_items="flex-start", padding_top="8px",
                ),
                align="end", spacing="1",
            ),
            rx.box(
                rx.text(f"🤖 {model_name}", font_size="0.72rem", color="rgba(255,255,255,0.6)", font_family="monospace"),
                background="rgba(255,255,255,0.06)", border_radius="8px", padding="6px 12px", width="100%", text_align="center",
            ),
            rx.divider(border_color="rgba(255,255,255,0.1)", width="100%"),
            rx.vstack(
                *[
                    rx.hstack(
                        rx.text("✓", color="#00ff88", font_weight="700", font_size="0.85rem"),
                        rx.text(f, font_size="0.82rem", color="rgba(255,255,255,0.8)"),
                        spacing="2", align="center",
                    )
                    for f in features
                ],
                spacing="2", align_items="flex-start", width="100%",
            ),
            rx.cond(
                is_current,
                rx.box(
                    rx.text("✓ Active Plan", color="rgba(255,255,255,0.5)", font_weight="700", font_size="0.9rem", text_align="center", width="100%"),
                    width="100%", height="48px", border_radius="12px", display="flex", align_items="center", justify_content="center",
                    style={"background": "rgba(16,185,129,0.12)", "border": "1px solid rgba(16,185,129,0.35)"},
                ),
                rx.button(
                    rx.cond(
                        AppState.payment_processing,
                        rx.hstack(rx.spinner(size="1", color="white"), rx.text("Redirecting..."), spacing="2"),
                        rx.text(f"Get {title}  →"),
                    ),
                    on_click=AppState.initiate_payment(plan_num),
                    width="100%", height="48px", border_radius="12px",
                    is_disabled=AppState.payment_processing,
                    style={
                        "background": gradient, "border": "none", "color": "white",
                        "font_weight": "700", "font_size": "0.9rem", "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "_hover": {"filter": "brightness(1.12)", "transform": "translateY(-1px)", "box_shadow": glow},
                        "_active": {"transform": "translateY(0)"},
                    },
                ),
            ),
            spacing="4", align_items="flex-start", width="100%", padding="1.5em",
        ),
        position="relative", background="rgba(18,18,24,0.92)",
        border=rx.cond(is_current, "1.5px solid rgba(16,185,129,0.5)", rx.cond(is_recommended, "1.5px solid rgba(168,85,247,0.6)", "1px solid rgba(255,255,255,0.1)")),
        border_radius="20px", width="280px", flex_shrink="0",
        style={
            "box_shadow": rx.cond(is_current, "0 0 24px rgba(16,185,129,0.25)", rx.cond(is_recommended, glow, "0 4px 24px rgba(0,0,0,0.4)")),
            "transition": "transform 0.2s ease",
            "_hover": {"transform": "translateY(-4px)"},
        },
        margin_top=rx.cond(is_recommended | is_current, "14px", "0"),
    )


def pricing_modal() -> rx.Component:
    return rx.cond(
        AppState.show_pricing_modal,
        rx.box(
            rx.box(
                rx.button(
                    "✕", on_click=AppState.close_pricing_modal,
                    position="absolute", top="16px", right="16px",
                    background="rgba(255,255,255,0.08)", border="none", color="rgba(255,255,255,0.6)",
                    font_size="1.1rem", border_radius="8px", width="36px", height="36px", cursor="pointer",
                    style={"_hover": {"background": "rgba(255,255,255,0.15)", "color": "white"}},
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text("Alex AI Premium", font_size="1.1rem", font_weight="700", color="white"),
                        rx.text("USD 3.20", font_size="2.1rem", font_weight="800", color="white"),
                        rx.text("per month", color="rgba(255,255,255,0.55)", font_size="0.85rem"),
                        rx.box(height="8px"),
                        rx.text("• Unlimited daily messages", color="rgba(255,255,255,0.82)", font_size="0.9rem"),
                        rx.text("• Same Groq model, no daily cap", color="rgba(255,255,255,0.82)", font_size="0.9rem"),
                        rx.text("• Full semester access", color="rgba(255,255,255,0.82)", font_size="0.9rem"),
                        rx.text("• Chat history saved", color="rgba(255,255,255,0.82)", font_size="0.9rem"),
                        spacing="2",
                        align="start",
                        width="48%",
                        min_width="280px",
                    ),
                    rx.vstack(
                        rx.box(
                            rx.box(
                                width="300px",
                                height="170px",
                                position="absolute",
                                top="50%",
                                left="50%",
                                transform="translate(-50%, -50%)",
                                border_radius="999px",
                                background="radial-gradient(ellipse at center, rgba(34,197,94,0.18) 0%, rgba(34,197,94,0.05) 55%, transparent 100%)",
                                style={"filter": "blur(16px)"},
                            ),
                            rx.box(
                                width="220px",
                                height="220px",
                                position="absolute",
                                top="50%",
                                left="50%",
                                transform="translate(-50%, -52%)",
                                border_radius="999px",
                                background="radial-gradient(circle at center, rgba(34,197,94,0.26) 0%, rgba(34,197,94,0.08) 42%, transparent 100%)",
                                style={"filter": "blur(8px)"},
                            ),
                            rx.image(
                                src="/a_logo.png",
                                width="128px",
                                height="128px",
                                object_fit="contain",
                                opacity="0.88",
                                style={"filter": "drop-shadow(0 0 18px rgba(34,197,94,0.42)) drop-shadow(0 0 36px rgba(34,197,94,0.28))"},
                            ),
                            width="100%",
                            height="170px",
                            position="relative",
                            overflow="visible",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                            style={"background": "transparent"},
                        ),
                        rx.text("Upgrade Alex AI", font_size="1.55rem", font_weight="800", color="white"),
                        rx.text(
                            "New users get 3 days trial with unlimited messages. After trial, free mode is 5 messages/day.",
                            color="rgba(255,255,255,0.6)",
                            font_size="0.88rem",
                            text_align="center",
                        ),
                        rx.cond(
                            AppState.is_in_trial & ~AppState.has_premium_access,
                            rx.text(
                                "Trial active: " + AppState.trial_days_left.to_string() + " day(s) left",
                                color="#86efac",
                                font_size="0.82rem",
                            ),
                            rx.fragment(),
                        ),
                        rx.cond(
                            AppState.has_premium_access,
                            rx.box(
                                rx.text("✓ Premium is already active", color="#86efac", font_weight="700", text_align="center"),
                                width="100%",
                                padding="12px",
                                border_radius="12px",
                                border="1px solid rgba(134,239,172,0.45)",
                                background="rgba(22,101,52,0.2)",
                            ),
                            rx.button(
                                "Continue to Secure Checkout",
                                on_click=rx.redirect("https://alexstudies.lemonsqueezy.com/checkout/buy/54b3aa5e-c5f8-4a71-8fff-7efd75983e31", is_external=True),
                                width="100%",
                                height="52px",
                                border_radius="12px",
                                style={
                                    "background": "linear-gradient(135deg,#16a34a,#22c55e)",
                                    "border": "none",
                                    "color": "white",
                                    "font_weight": "700",
                                    "cursor": "pointer",
                                    "_hover": {"filter": "brightness(1.08)"},
                                },
                            ),
                        ),
                        rx.text(
                            "Secure checkout via Lemon Squeezy",
                            color="rgba(255,255,255,0.35)",
                            font_size="0.75rem",
                        ),
                        spacing="3",
                        align="center",
                        width="48%",
                        min_width="280px",
                    ),
                    width="100%",
                    align="stretch",
                    spacing="4",
                    justify="between",
                    flex_wrap="wrap",
                ),
                rx.cond(
                    AppState.payment_error != "",
                    rx.box(
                        rx.text("⚠️  " + AppState.payment_error, color="#fca5a5", font_size="0.82rem", text_align="center"),
                        background="rgba(239,68,68,0.1)", border="1px solid rgba(239,68,68,0.3)",
                        border_radius="10px", padding="10px 20px", margin_top="1em", width="100%",
                    ),
                    rx.fragment(),
                ),
                position="relative", background="rgba(10,10,14,0.97)",
                border="1px solid rgba(255,255,255,0.08)", border_radius="24px", padding="2.5em 2em",
                display="flex", flex_direction="column", align_items="center", width="100%", max_width="820px",
                style={"box_shadow": "0 32px 80px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.04)", "backdrop_filter": "blur(20px)"},
            ),
            position="fixed", top="0", left="0", width="100vw", height="100vh", z_index="1000",
            display="flex", align_items="center", justify_content="center",
            background="rgba(0,0,0,0.75)", style={"backdrop_filter": "blur(6px)"}, padding="1em",
        ),
        rx.fragment(),
    )


# ──────────────────────────────────────────────────────────────
# Tier status bar & input components
# ──────────────────────────────────────────────────────────────
def tier_status_bar() -> rx.Component:
    return rx.hstack(
        rx.badge(
            AppState.tier_label,
            variant="solid",
            style={
                "background": rx.cond(AppState.has_premium_access, "linear-gradient(90deg,#b45309,#f59e0b)",
                        rx.cond(AppState.is_in_trial, "linear-gradient(90deg,#065f46,#10b981)", "rgba(255,255,255,0.08)")),
                "color": "white", "font_size": "0.7rem", "padding": "2px 10px", "border_radius": "20px",
            },
        ),
        rx.cond(
            ~AppState.has_premium_access & ~AppState.is_in_trial,
            rx.text(AppState.messages_left_today.to_string() + f" / {FREE_DAILY_LIMIT} messages left today",
                    color="rgba(255,255,255,0.4)", font_size="0.72rem"),
            rx.fragment(),
        ),
        rx.spacer(),
        rx.text("⚡ " + AppState.active_model_name, color="rgba(255,255,255,0.3)", font_size="0.68rem", font_family="monospace"),
        width="100%", max_width="860px", margin_x="auto", padding_x="1em", padding_y="4px", align="center",
    )


def upgrade_button() -> rx.Component:
    return rx.box(
        rx.button(
            rx.hstack(
                rx.hstack(
                    rx.box(
                        rx.text("✦", color="#dcfce7", font_size="0.9rem", font_weight="800"),
                        width="28px",
                        height="28px",
                        border_radius="999px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        background="rgba(220,252,231,0.1)",
                        border="1px solid rgba(220,252,231,0.14)",
                        flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text(
                            "Unlock Unlimited Access",
                            font_weight="800",
                            font_size="1rem",
                            color="white",
                            style={"text_shadow": "0 1px 4px rgba(0,0,0,0.45)"},
                        ),
                        rx.text(
                            "Unlimited chats, saved history, full semester access",
                            color="rgba(220,252,231,0.72)",
                            font_size="0.72rem",
                            font_weight="500",
                        ),
                        spacing="0",
                        align_items="flex-start",
                    ),
                    spacing="3",
                    align="center",
                ),
                rx.spacer(),
                rx.box(
                    rx.text("→", color="white", font_size="1.15rem", font_weight="700"),
                    width="34px",
                    height="34px",
                    border_radius="10px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    background="rgba(255,255,255,0.07)",
                    border="1px solid rgba(255,255,255,0.08)",
                    flex_shrink="0",
                ),
                align="center", spacing="3", width="100%",
            ),
            on_click=AppState.open_pricing_modal,
            width="100%", min_height="74px", border_radius="16px",
            style={
                "background": "linear-gradient(135deg, rgba(12,34,21,0.98) 0%, rgba(18,90,58,0.92) 42%, rgba(6,8,7,0.99) 100%)",
                "border": "1px solid rgba(110,231,183,0.24)",
                "cursor": "pointer",
                "box_shadow": "0 14px 34px rgba(0,0,0,0.42), 0 0 24px rgba(22,163,74,0.08), inset 0 1px 0 rgba(255,255,255,0.05)",
                "transition": "all 0.25s ease",
                "padding": "16px 24px",
                "_hover": {
                    "box_shadow": "0 18px 40px rgba(0,0,0,0.5), 0 0 28px rgba(34,197,94,0.16), inset 0 1px 0 rgba(255,255,255,0.06)",
                    "transform": "translateY(-2px)",
                    "filter": "brightness(1.05)",
                    "border": "1px solid rgba(134,239,172,0.34)",
                },
                "_active": {"transform": "translateY(0)"},
            },
        ),
        rx.text("🔒 You've reached your 5 free messages for today. Resets at midnight.",
                color="rgba(255,255,255,0.35)", font_size="0.7rem", text_align="center", margin_top="8px"),
        width="100%", max_width="860px", margin_x="auto", padding="1em",
    )


# ═══════════════════════════════════════════════════════
# INPUT + BUTTON FIX — Replace chat_input_field() only
# ═══════════════════════════════════════════════════════
#
# What changed:
#   1. Unified container — input + button share ONE border/background
#      so they read as a single component, not two floating elements
#   2. Button color — dropped from #00ff88 neon to a calm white/frost tone
#      It still stands out but doesn't scream over the dark theme
#   3. Glow removed — no more box-shadow bloom on the button
#      Hover just brightens slightly — restrained and clean
#   4. Button is now INSIDE the box, right edge, vertically centered
#      Gap between textarea and button is gone

# ═══════════════════════════════════════════════════════
# INPUT BOX FINAL FIX — kills the double-box issue
# Replace chat_input_field() with this
# ═══════════════════════════════════════════════════════
#
# Root cause: rx.text_area renders a <textarea> with its own
# Radix/browser background + border that sits ON TOP of the shell.
# Fix: inject a <style> tag that nukes all default textarea styling
# so the shell is the ONLY visible box.

def chat_input_field() -> rx.Component:
    return rx.box(
        # Kill ALL default textarea appearance globally for this component
        rx.html("""
        <style>
          #chat_input,
          #chat_input textarea,
          [id="chat_input"] {
            background: transparent !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            -webkit-appearance: none !important;
            resize: none !important;
          }
        </style>
        """),

        rx.hstack(
            rx.text_area(
                id="chat_input",
                placeholder=rx.cond(
                    AppState.name != "",
                    "Ask Alex AI anything " + AppState.name + "...",
                    "Ask Alex AI anything...",
                ),
                value=AppState.chat_input,
                on_change=AppState.set_chat_input,
                color="rgba(255,255,255,0.88)",
                flex="1",
                min_height="48px",
                max_height="130px",
                padding="14px 4px 14px 16px",
                font_size="0.93rem",
                line_height="1.55",
                style={
                    "background": "transparent",
                    "border": "none",
                    "outline": "none",
                    "box_shadow": "none",
                    "resize": "none",
                    "_placeholder": {"color": "rgba(255,255,255,0.22)"},
                    "_focus": {
                        "background": "transparent",
                        "border": "none",
                        "outline": "none",
                        "box_shadow": "none",
                    },
                    "scrollbar_width": "none",
                    "&::-webkit-scrollbar": {"display": "none"},
                },
            ),

            rx.button(
                rx.cond(
                    AppState.is_processing,
                    rx.spinner(size="1", color="rgba(255,255,255,0.5)"),
                    rx.icon(tag="arrow_up", size=16, color="rgba(255,255,255,0.85)"),
                ),
                id="chat_send_btn",
                on_click=AppState.send_message,
                is_disabled=AppState.is_processing,
                width="36px",
                height="36px",
                border_radius="8px",
                flex_shrink="0",
                align_self="flex-end",
                margin_bottom="7px",
                margin_right="7px",
                style={
                    "background": rx.cond(
                        AppState.is_processing,
                        "rgba(255,255,255,0.04)",
                        "rgba(0,180,90,0.16)",
                    ),
                    "border": "1px solid rgba(0,255,136,0.20)",
                    "cursor": "pointer",
                    "transition": "all 0.18s ease",
                    "_hover": {
                        "background": "rgba(0,180,90,0.28)",
                        "border": "1px solid rgba(0,255,136,0.40)",
                        "transform": "translateY(-1px)",
                    },
                    "_active": {"transform": "translateY(0)"},
                    "_disabled": {
                        "opacity": "0.3",
                        "cursor": "not-allowed",
                        "transform": "none",
                    },
                },
            ),

            align="end",
            spacing="0",
            width="100%",
        ),

        rx.script(ENTER_TO_SEND_JS),

        # ── The ONE visible box ─────────────────────────────
        width="100%",
        border_radius="14px",
        background="rgba(7, 11, 9, 0.94)",
        border="1px solid rgba(82, 120, 99, 0.18)",
        style={
            "transition": "border-color 0.2s ease, box-shadow 0.2s ease",
            "&:focus-within": {
                "border": "1px solid rgba(108, 155, 127, 0.34)",
                "box_shadow": "0 0 0 1px rgba(68, 102, 83, 0.24), 0 0 22px rgba(8, 18, 14, 0.32)",
            },
        },
    )
# NEW: Empty chat state — centered like ChatGPT home
# ──────────────────────────────────────────────────────────────


def empty_chat_panel() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.spacer(),

            # Single, clean logo
            rx.box(
                rx.image(
                    src="/a_logo.png",
                    width="72px",
                    height="72px",
                    object_fit="contain",
                    style={
                        "filter": "drop-shadow(0 0 16px rgba(0,255,136,0.25))",
                        "opacity": "0.9",
                    },
                ),
                margin_bottom="8px",
            ),

            rx.text(
                "What do you want to learn today?",
                color="rgba(255,255,255,0.38)",
                font_size="0.95rem",
                font_weight="400",
                letter_spacing="0.3px",
            ),

            rx.spacer(),

            # Input bar
            rx.box(
                rx.cond(
                    AppState.can_send_message,
                    chat_input_field(),
                    upgrade_button(),
                ),
                width="100%",
                max_width="680px",
            ),

            # Tier bar
            tier_status_bar(),

            rx.box(height="80px"),  # bottom breathing room

            spacing="4",
            align="center",
            width="100%",
            height="100%",
        ),
        pricing_modal(),
        width="100%",
        height="100%",
        display="flex",
        flex_direction="column",
        align_items="center",
        justify_content="center",
        padding="2em",
    )

# ── FIX 2: active_chat_panel ─────────────────────────
# Before: user bubble had `padding="10px 16px"` — a little tight
#         assistant text had no horizontal padding — text touched the edges
# After:  user bubble → `padding="12px 20px"`, max-width tightened to 62%
#         assistant → `padding="4px 4px 4px 8px"` left indent so it reads like a reply
#         overall message vstack gets `padding_x="2.5em"` — more generous side margins

def active_chat_panel() -> rx.Component:
    return rx.box(
        # Scrollable messages area
        rx.box(
            rx.vstack(
                rx.foreach(
                    AppState.chat_history,
                    lambda msg: rx.box(
                        rx.cond(
                            msg["role"] == "user",

                            # ── User bubble ──────────────────
                            rx.box(
                                rx.text(
                                    msg["content"],
                                    color="rgba(255,255,255,0.92)",
                                    font_size="0.93rem",
                                    line_height="1.6",
                                ),
                                background="linear-gradient(180deg, rgba(255,255,255,0.105) 0%, rgba(255,255,255,0.082) 100%)",
                                border="1px solid rgba(255,255,255,0.12)",
                                border_radius="18px 18px 4px 18px",
                                padding="12px 20px",           # more breathing room
                                max_width="62%",               # slightly tighter — feels more like a message
                                margin_left="auto",
                                margin_right="0",
                                style={
                                    "box_shadow": "0 10px 24px rgba(0,0,0,0.16), inset 0 1px 0 rgba(255,255,255,0.03)",
                                    "backdrop_filter": "blur(6px)",
                                },
                            ),

                            # ── Assistant reply ──────────────
                            rx.box(
                                rx.markdown(msg["content"]),
                                color="rgba(255,255,255,0.88)",
                                font_size="0.93rem",
                                line_height="1.7",             # slightly more open leading
                                max_width="86%",
                                padding_left="10px",           # subtle left indent — reads like a reply
                                margin_left="0",
                                style={
                                    # tighten up markdown's default tight spacing
                                    "& p": {"margin_bottom": "0.6em"},
                                    "& p + ul, & p + ol": {"margin_top": "0.22em"},
                                    "& ul, & ol": {"padding_left": "1.78em", "margin_bottom": "0.55em"},
                                    "& li": {"margin_bottom": "0.3em", "padding_left": "0.14em"},
                                    "& li::marker": {"color": "rgba(74,222,128,0.9)"},
                                    "& strong": {"color": "rgba(220,252,231,0.96)"},
                                    "& code": {
                                        "background": "rgba(0,255,136,0.08)",
                                        "border": "1px solid rgba(0,255,136,0.15)",
                                        "border_radius": "4px",
                                        "padding": "1px 6px",
                                        "font_size": "0.85em",
                                    },
                                },
                            ),
                        ),
                        width="100%",
                        margin_bottom="20px",                  # more space between turns
                        display="flex",
                        flex_direction="column",
                    ),
                ),
                # ...existing code...
                rx.cond(
                    AppState.is_processing,
                    rx.html("""
                        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                            <div style="width:24px;height:24px;position:relative;flex-shrink:0;">
                                <style>
                                    @keyframes alexorbit { from { transform: rotate(0deg) translateX(10px); } to { transform: rotate(360deg) translateX(10px); } }
                                </style>
                                <div style="width:4px;height:4px;background:#00ff88;border-radius:50%;position:absolute;top:50%;left:50%;margin-top:-2px;margin-left:-2px;animation:alexorbit 0.3s linear infinite;box-shadow:0 0 4px rgba(0,255,136,0.9);"></div>
                            </div>
                            <span style="color:rgba(255,255,255,0.3);font-size:0.8rem;font-weight:300;letter-spacing:0.5px;">Alex is thinking...</span>
                        </div>
                    """),
                ),
                # ...existing code...
                rx.box(id="chat_bottom_anchor", height="1px"),
                width="100%",
                max_width="760px",
                margin_x="auto",
                padding_x="2.5em",       # generous side margins — text doesn't touch the edge
                padding_top="1.5em",
                padding_bottom="1em",
                style={
                    "padding_bottom": "80px",
                    "min_height": "100%",
                }
            ),
            id="chat_scroll",
            flex="1",
            min_height="0",
            overflow_y="auto",
            padding="0",
            width="100%",
            style={
                # hide scrollbar on webkit but keep it functional
                "&::-webkit-scrollbar": {"width": "4px"},
                "&::-webkit-scrollbar-track": {"background": "transparent"},
                "&::-webkit-scrollbar-thumb": {
                    "background": "rgba(255,255,255,0.1)",
                    "border_radius": "4px",
                },
            },
        ),
        rx.script(AUTO_SCROLL_OBSERVER_JS),
        tier_status_bar(),
        rx.cond(
            AppState.can_send_message,
            rx.box(
                chat_input_field(),
                width="100%",
                max_width="860px",
                margin_x="auto",
                padding="0 1.5em 1.2em 1.5em",   # slightly more bottom padding
            ),
            upgrade_button(),
        ),
        pricing_modal(),
        width="100%",
        height="100%",
        display="flex",
        flex_direction="column",
        overflow="hidden",
        background="transparent",
        position="relative",
    )
# ──────────────────────────────────────────────────────────────
# Main chat panel — switches between empty and active
# ──────────────────────────────────────────────────────────────
def chat_panel():
    return rx.cond(
        AppState.is_empty_chat,
        empty_chat_panel(),
        active_chat_panel(),
    )


@rx.page(route="/auth/google/start", image=FAVICON_32, on_load=AppState.start_google_oauth)
def google_start_page():
    return rx.center(
        rx.text("Redirecting to Google...", color="white"),
        height="100vh",
        background="#050505",
    )


@rx.page(route="/auth/google/callback", image=FAVICON_32)
def google_callback_bridge_page():
    callback_bridge_js = """
    (function() {
      try {
        var u = new URL(window.location.href);
        var err = u.searchParams.get("error");
        var code = u.searchParams.get("code");
        var state = u.searchParams.get("state");
        if (err || !code || !state) {
          window.location.replace("/login?oauth_error=1");
          return;
        }
        var origin = window.location.origin || "";
        var originB64 = btoa(origin).replace(/\\+/g, "-").replace(/\\//g, "_").replace(/=+$/g, "");
        var target = "/auth/google/complete/"
          + encodeURIComponent(code) + "/"
          + encodeURIComponent(state) + "/"
          + originB64;
        window.location.replace(target);
      } catch (e) {
        window.location.replace("/login?oauth_error=1");
      }
    })();
    """
    return rx.center(
        rx.vstack(
            rx.spinner(size="2", color="white"),
            rx.text("Completing Google sign-in...", color="white"),
            spacing="3",
            align="center",
        ),
        rx.script(callback_bridge_js),
        height="100vh",
        background="#050505",
    )


@rx.page(
    route="/auth/google/complete/[code]/[state]/[origin_b64]",
    image=FAVICON_32,
    on_load=AppState.handle_google_oauth_callback,
)
def google_oauth_complete_page():
    return rx.center(
        rx.text("Signing you in...", color="white"),
        height="100vh",
        background="#050505",
    )


@rx.page(route="/auth/complete/[token]", image=FAVICON_32, on_load=AppState.handle_google_complete)
def google_complete_page():
    return rx.center(
        rx.text("Signing you in...", color="white"),
        height="100vh",
        background="#050505",
    )


# ──────────────────────────────────────────────────────────────
# Payment pages
# ──────────────────────────────────────────────────────────────
def _marketing_button(label: str, href: str, variant: str = "solid") -> rx.Component:
    base_props = {
        "on_click": rx.redirect(href),
        "size": "3",
        "height": "48px",
        "padding": "0 22px",
        "border_radius": "9999px",
        "font_weight": "700",
        "letter_spacing": "0.01em",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
    }
    if variant == "solid":
        return rx.button(
            label,
            background="linear-gradient(135deg,var(--landing-accent) 0%, var(--landing-accent-2) 100%)",
            color="#04111d",
            border="none",
            box_shadow="0 18px 44px rgba(16,185,129,0.24)",
            _hover={
                "transform": "translateY(-1px)",
                "box_shadow": "0 22px 52px rgba(56,189,248,0.24)",
            },
            _active={"transform": "translateY(0px)"},
            **base_props,
        )
    return rx.button(
        label,
        background="rgba(3,8,20,0.36)",
        color="white",
        border="1px solid var(--landing-border-strong)",
        backdrop_filter="blur(14px)",
        box_shadow="0 10px 36px rgba(2,6,23,0.24)",
        _hover={
            "background": "rgba(15,23,42,0.56)",
            "border_color": "rgba(148,163,184,0.38)",
            "transform": "translateY(-1px)",
        },
        _active={"transform": "translateY(0px)"},
        **base_props,
    )


def _marketing_badge(text: str) -> rx.Component:
    return rx.box(
        rx.text(
            text,
            font_size="0.76rem",
            font_weight="700",
            letter_spacing="0.16em",
            text_transform="uppercase",
            color="rgba(226,232,240,0.82)",
        ),
        display="inline-flex",
        align_items="center",
        width="fit-content",
        padding="9px 14px",
        border_radius="9999px",
        border="1px solid rgba(148,163,184,0.18)",
        background="rgba(8,15,30,0.58)",
        backdrop_filter="blur(16px)",
    )


def _marketing_card(title: str, body: str, kicker: str = "") -> rx.Component:
    content = []
    if kicker:
        content.append(
            rx.text(
                kicker,
                color="var(--landing-accent-2)",
                font_size="0.78rem",
                font_weight="700",
                letter_spacing="0.12em",
                text_transform="uppercase",
            )
        )
    content.extend(
        [
            rx.heading(
                title,
                size="5",
                color="white",
                font_family="var(--landing-display-font)",
            ),
            rx.text(
                body,
                color="rgba(226,232,240,0.76)",
                line_height="1.7",
            ),
        ]
    )
    return rx.box(
        rx.vstack(
            *content,
            spacing="3",
            align_items="flex-start",
            width="100%",
        ),
        padding="24px",
        border_radius="22px",
        border="1px solid var(--landing-border)",
        background="linear-gradient(180deg,rgba(7,12,24,0.82),rgba(5,8,17,0.62))",
        box_shadow="0 20px 70px rgba(2,6,23,0.32)",
        backdrop_filter="blur(16px)",
        width="100%",
        height="100%",
    )


def _legal_section_body(body: str) -> rx.Component:
    rows: list[rx.Component] = []
    for raw_line in (body or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("- "):
            rows.append(
                rx.hstack(
                    rx.text("•", color="var(--landing-accent-2)", margin_top="2px"),
                    rx.text(
                        line[2:].strip(),
                        color="rgba(226,232,240,0.76)",
                        line_height="1.7",
                        flex="1",
                    ),
                    align="start",
                    spacing="3",
                    width="100%",
                )
            )
            continue

        if ":" in line:
            label, value = line.split(":", 1)
            if label.strip() and value.strip():
                rows.append(
                    rx.hstack(
                        rx.text(
                            label.strip() + ":",
                            color="rgba(226,232,240,0.92)",
                            font_weight="600",
                            width="88px",
                            flex_shrink="0",
                        ),
                        rx.text(
                            value.strip(),
                            color="rgba(226,232,240,0.76)",
                            line_height="1.7",
                            flex="1",
                        ),
                        align="start",
                        spacing="3",
                        width="100%",
                    )
                )
                continue

        rows.append(
            rx.text(
                line,
                color="rgba(226,232,240,0.76)",
                line_height="1.7",
                width="100%",
            )
        )

    return rx.vstack(
        *rows,
        spacing="2",
        align_items="flex-start",
        width="100%",
    )


def _marketing_step_card(step: str, title: str, body: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.box(
                step,
                width="48px",
                height="48px",
                border_radius="16px",
                display="flex",
                align_items="center",
                justify_content="center",
                background="linear-gradient(135deg,rgba(56,189,248,0.24),rgba(16,185,129,0.26))",
                border="1px solid rgba(125,211,252,0.22)",
                color="white",
                font_weight="800",
                font_family="var(--landing-display-font)",
                font_size="1rem",
            ),
            rx.heading(
                title,
                size="5",
                color="white",
                font_family="var(--landing-display-font)",
            ),
            rx.text(body, color="rgba(226,232,240,0.76)", line_height="1.7"),
            spacing="3",
            align_items="flex-start",
            width="100%",
        ),
        padding="24px",
        border_radius="22px",
        border="1px solid var(--landing-border)",
        background="linear-gradient(180deg,rgba(8,14,28,0.84),rgba(5,8,18,0.62))",
        box_shadow="0 20px 70px rgba(2,6,23,0.3)",
        width="100%",
        height="100%",
    )


def _public_nav() -> rx.Component:
    nav_link_style = {
        "color": "rgba(226,232,240,0.76)",
        "font_weight": "600",
        "text_decoration": "none",
        "_hover": {"color": "white"},
    }
    return rx.box(
        rx.hstack(
            rx.link(
                rx.hstack(
                    rx.box(
                        rx.image(
                            src="/a_logo.png",
                            width="100%",
                            height="100%",
                            object_fit="cover",
                        ),
                        width="44px",
                        height="44px",
                        border_radius="14px",
                        overflow="hidden",
                        border="1px solid rgba(148,163,184,0.18)",
                        background="rgba(4,10,24,0.8)",
                        box_shadow="0 18px 44px rgba(16,185,129,0.18)",
                        flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text(
                            BUSINESS_NAME,
                            color="white",
                            font_weight="700",
                            font_family="var(--landing-display-font)",
                            font_size="1.02rem",
                            line_height="1.1",
                        ),
                        rx.text(
                            "AI-powered study platform for degree students",
                            color="rgba(148,163,184,0.82)",
                            font_size="0.8rem",
                            line_height="1.2",
                        ),
                        spacing="1",
                        align_items="flex-start",
                    ),
                    spacing="3",
                    align="center",
                ),
                href="/",
                text_decoration="none",
            ),
            rx.spacer(),
            rx.hstack(
                rx.link("Support", href="/support", **nav_link_style),
                _marketing_button("Student Login", auth_routes.LOGIN_ROUTE, "secondary"),
                spacing="3",
                align="center",
                flex_wrap="wrap",
                justify="end",
            ),
            width="100%",
            align="center",
            gap="16px",
            flex_wrap="wrap",
        ),
        padding="16px 18px",
        border_radius="24px",
        border="1px solid var(--landing-border)",
        background="rgba(5,10,22,0.58)",
        backdrop_filter="blur(18px)",
        box_shadow="0 20px 80px rgba(2,6,23,0.34)",
        width="100%",
    )


def _public_footer() -> rx.Component:
    footer_link_style = {
        "color": "rgba(226,232,240,0.76)",
        "text_decoration": "none",
        "font_weight": "600",
        "_hover": {"color": "white", "text_decoration": "underline"},
    }
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(
                    BUSINESS_NAME,
                    color="white",
                    font_weight="700",
                    font_family="var(--landing-display-font)",
                    font_size="1.15rem",
                ),
                rx.text(
                    "AI-powered education platform for semester-wise guidance and daily structured study support.",
                    color="rgba(226,232,240,0.72)",
                    max_width="420px",
                    line_height="1.7",
                ),
                rx.link(SUPPORT_EMAIL, href=f"mailto:{SUPPORT_EMAIL}", **footer_link_style),
                rx.link(SUPPORT_PHONE, href=SUPPORT_PHONE_LINK, **footer_link_style),
                rx.text(BUSINESS_LOCATION, color="rgba(148,163,184,0.82)"),
                rx.text(
                    f"© {CURRENT_COPYRIGHT_YEAR} {BUSINESS_NAME}. All rights reserved.",
                    color="rgba(100,116,139,0.88)",
                    font_size="0.82rem",
                ),
                spacing="2",
                align_items="flex-start",
            ),
            rx.vstack(
                rx.text(
                    "Public Links",
                    color="white",
                    font_weight="700",
                    font_family="var(--landing-display-font)",
                ),
                rx.hstack(
                    rx.link("Return Policy", href="/return-policy", **footer_link_style),
                    rx.link("Privacy Policy", href="/privacy-policy", **footer_link_style),
                    rx.link("Terms", href="/terms", **footer_link_style),
                    rx.link("Support", href="/support", **footer_link_style),
                    flex_wrap="wrap",
                    gap="14px",
                    width="100%",
                ),
                rx.text(
                    "Students can review support, policies, and business contact details before logging in.",
                    color="rgba(148,163,184,0.82)",
                    line_height="1.7",
                    max_width="360px",
                ),
                spacing="3",
                align_items="flex-start",
                width="100%",
            ),
            width="100%",
            justify="between",
            align="start",
            gap="28px",
            flex_wrap="wrap",
        ),
        padding="30px",
        border_radius="28px",
        border="1px solid var(--landing-border)",
        background="linear-gradient(180deg,rgba(7,12,24,0.82),rgba(5,8,17,0.62))",
        box_shadow="0 24px 80px rgba(2,6,23,0.36)",
        backdrop_filter="blur(18px)",
        width="100%",
    )


def _public_page_frame(main_content: rx.Component) -> rx.Component:
    return rx.box(
        rx.box(
            position="absolute",
            top="-120px",
            right="-120px",
            width="420px",
            height="420px",
            border_radius="9999px",
            background="radial-gradient(circle, rgba(16,185,129,0.28) 0%, rgba(16,185,129,0) 70%)",
            filter="blur(10px)",
        ),
        rx.box(
            position="absolute",
            top="18%",
            left="-140px",
            width="420px",
            height="420px",
            border_radius="9999px",
            background="radial-gradient(circle, rgba(56,189,248,0.22) 0%, rgba(56,189,248,0) 70%)",
            filter="blur(18px)",
        ),
        rx.box(
            _public_nav(),
            main_content,
            _public_footer(),
            width="min(1180px, calc(100vw - 32px))",
            margin="0 auto",
            padding_top="20px",
            padding_bottom="40px",
            display="flex",
            flex_direction="column",
            gap="28px",
            position="relative",
            z_index="1",
        ),
        style={
            "--landing-accent": "#34d399",
            "--landing-accent-2": "#38bdf8",
            "--landing-border": "rgba(148,163,184,0.18)",
            "--landing-border-strong": "rgba(148,163,184,0.28)",
            "--landing-display-font": "'Space Grotesk', 'Plus Jakarta Sans', sans-serif",
            "--landing-body-font": "'Plus Jakarta Sans', 'Inter', sans-serif",
        },
        background=(
            "radial-gradient(circle at top left, rgba(56,189,248,0.12) 0%, transparent 28%),"
            "radial-gradient(circle at top right, rgba(16,185,129,0.14) 0%, transparent 24%),"
            "linear-gradient(180deg, #020617 0%, #030712 40%, #02030a 100%)"
        ),
        color="white",
        min_height="100vh",
        width="100%",
        overflow="hidden",
        font_family="var(--landing-body-font)",
        position="relative",
    )


def _marketing_section(
    eyebrow: str,
    title: str,
    description: str,
    body: rx.Component,
    section_id: str = "",
) -> rx.Component:
    return rx.box(
        rx.vstack(
            _marketing_badge(eyebrow),
            rx.heading(
                title,
                color="white",
                font_size="clamp(1.8rem, 3.5vw, 3rem)",
                line_height="1.08",
                letter_spacing="-0.03em",
                font_family="var(--landing-display-font)",
                max_width="760px",
            ),
            rx.text(
                description,
                color="rgba(226,232,240,0.76)",
                font_size="1.02rem",
                line_height="1.8",
                max_width="760px",
            ),
            body,
            spacing="5",
            align_items="flex-start",
            width="100%",
        ),
        id=section_id,
        padding="clamp(24px, 4vw, 40px)",
        border_radius="30px",
        border="1px solid var(--landing-border)",
        background="linear-gradient(180deg,rgba(7,12,24,0.8),rgba(5,8,17,0.6))",
        box_shadow="0 24px 80px rgba(2,6,23,0.38)",
        backdrop_filter="blur(18px)",
        width="100%",
    )


@rx.page(route="/payment/success", title="Payment Successful", image=FAVICON_32)
def payment_success_page():
    return rx.box(
        rx.center(
            rx.vstack(
                rx.text("✅", font_size="4rem"),
                rx.heading("Payment Successful!", size="7", color="white"),
                rx.text("Your premium plan is now active. Enjoy unlimited learning!", color="rgba(255,255,255,0.7)", text_align="center", max_width="400px"),
                rx.box(
                    rx.text("⚡ Note: If your premium access isn't reflected yet, please wait a few seconds and refresh.", color="rgba(255,215,0,0.8)", font_size="0.82rem", text_align="center"),
                    background="rgba(255,215,0,0.08)", border="1px solid rgba(255,215,0,0.2)", border_radius="12px", padding="12px 20px", max_width="420px",
                ),
                rx.button("Go to Dashboard →", on_click=rx.redirect(APP_DASHBOARD_ROUTE), color_scheme="green", size="3",
                    style={"background":"linear-gradient(90deg,#065f46,#10b981)","border":"none","color":"white","font_weight":"700","cursor":"pointer"}),
                spacing="5", align="center",
            ),
            height="100vh",
        ),
        background="radial-gradient(circle at center, #001a0f 0%, #050505 100%)", min_height="100vh",
    )


@rx.page(route="/payment/cancel", title="Payment Cancelled", image=FAVICON_32)
def payment_cancel_page():
    return rx.box(
        rx.center(
            rx.vstack(
                rx.text("❌", font_size="4rem"),
                rx.heading("Payment Cancelled", size="7", color="white"),
                rx.text("No charges were made. You can try again anytime.", color="rgba(255,255,255,0.7)", text_align="center"),
                rx.button("Back to Dashboard", on_click=rx.redirect(APP_DASHBOARD_ROUTE), variant="outline", color_scheme="green", size="3"),
                spacing="5", align="center",
            ),
            height="100vh",
        ),
        background="radial-gradient(circle at center, #1a0000 0%, #050505 100%)", min_height="100vh",
    )


def legal_page_shell(title: str, subtitle: str, sections: list[tuple[str, str]]) -> rx.Component:
    return _public_page_frame(
        rx.vstack(
            rx.box(
                rx.vstack(
                    _marketing_badge("Public Information"),
                    rx.heading(
                        title,
                        color="white",
                        font_size="clamp(2rem, 4vw, 3.4rem)",
                        line_height="1.05",
                        letter_spacing="-0.04em",
                        font_family="var(--landing-display-font)",
                    ),
                    rx.text(
                        subtitle,
                        color="rgba(226,232,240,0.78)",
                        font_size="1.02rem",
                        line_height="1.8",
                        max_width="760px",
                    ),
                    spacing="4",
                    align_items="flex-start",
                    width="100%",
                ),
                padding="clamp(28px, 4vw, 42px)",
                border_radius="30px",
                border="1px solid var(--landing-border)",
                background="linear-gradient(180deg,rgba(7,12,24,0.8),rgba(5,8,17,0.62))",
                box_shadow="0 24px 80px rgba(2,6,23,0.38)",
                backdrop_filter="blur(18px)",
                width="100%",
            ),
            *[
                rx.box(
                    rx.vstack(
                        rx.text(
                            "Alex AI",
                            color="var(--landing-accent-2)",
                            font_size="0.78rem",
                            font_weight="700",
                            letter_spacing="0.12em",
                            text_transform="uppercase",
                        ),
                        rx.heading(
                            section_title,
                            size="5",
                            color="white",
                            font_family="var(--landing-display-font)",
                        ),
                        _legal_section_body(section_text),
                        spacing="3",
                        align_items="flex-start",
                        width="100%",
                    ),
                    padding="24px",
                    border_radius="22px",
                    border="1px solid var(--landing-border)",
                    background="linear-gradient(180deg,rgba(7,12,24,0.82),rgba(5,8,17,0.62))",
                    box_shadow="0 20px 70px rgba(2,6,23,0.32)",
                    backdrop_filter="blur(16px)",
                    width="100%",
                )
                for section_title, section_text in sections
            ],
            spacing="5",
            width="100%",
            align_items="stretch",
            padding_top="12px",
            padding_bottom="8px",
        )
    )


@rx.page(route="/return-policy", title="Return Policy", image=FAVICON_32)
def return_policy_page():
    return legal_page_shell(
        "Return Policy",
        "Simple refund and cancellation information for Alex AI subscriptions.",
        [
            (
                "Refunds",
                "We handle refund requests case-by-case.\n"
                "If you were charged incorrectly or had a technical billing issue, contact support with your order details.",
            ),
            (
                "Cancellation Rules",
                "You can cancel at any time.\n"
                "Cancellation stops future renewals. Access already provided for the paid period may remain active until that period ends.",
            ),
            (
                "Support Contact",
                f"Email support at {SUPPORT_EMAIL} with:\n"
                "- account username\n"
                "- payment/order reference\n"
                "- short description of the issue",
            ),
        ],
    )


@rx.page(route="/privacy-policy", title="Privacy Policy", image=FAVICON_32)
def privacy_policy_page():
    return legal_page_shell(
        "Privacy Policy",
        "How we collect, use, and protect your data on Alex AI.",
        [
            (
                "User Data",
                "We store account data and study-related activity needed to run the service.\n"
                "We use this data to provide login, chat history, progress tracking, and support.",
            ),
            (
                "Cookies and Local Storage",
                "We use browser storage and related technologies to keep you logged in and maintain app sessions.\n"
                "Disabling them may break some features.",
            ),
            (
                "Security",
                "We apply reasonable technical and organizational safeguards to protect user data.\n"
                "No online service can guarantee absolute security.",
            ),
        ],
    )


@rx.page(route="/terms", title="Terms of Service", image=FAVICON_32)
def terms_page():
    return legal_page_shell(
        "Terms of Service",
        "Basic usage terms for Alex AI.",
        [
            (
                "Website Usage Rules",
                "Use the platform lawfully and responsibly.\n"
                "Do not misuse the service, attempt unauthorized access, or interfere with availability.",
            ),
            (
                "Payments",
                "Paid plans are billed as shown at checkout.\n"
                "You are responsible for accurate payment details and reviewing plan pricing before purchase.",
            ),
            (
                "Responsibilities",
                "You are responsible for your account credentials and activity under your account.\n"
                "We may update features, pricing, or terms over time.",
            ),
        ],
    )


@rx.page(route="/support", title="Support", image=FAVICON_32)
def support_page():
    return legal_page_shell(
        "Support",
        "Need help with billing, login, or account access?",
        [
            (
                "Contact",
                f"Email: {SUPPORT_EMAIL}\n"
                f"Phone: {SUPPORT_PHONE}\n"
                f"Address: {BUSINESS_LOCATION}\n"
                "Please include your username and issue summary for faster help.",
            ),
            (
                "Response Time",
                "We aim to respond as quickly as possible, typically within 1-3 business days.",
            ),
            (
                "Common Help Topics",
                "Login issues\n"
                "Google sign-in issues\n"
                "Payment and subscription support\n"
                "Access and account recovery",
            ),
        ],
    )


# ──────────────────────────────────────────────────────────────
# Onboarding
# ──────────────────────────────────────────────────────────────
def onboarding_page():
    def onboarding_feedback() -> rx.Component:
        return rx.cond(
            AppState.onboarding_message != "",
            rx.text(
                AppState.onboarding_message,
                color="rgba(255,236,204,0.86)",
                font_size="0.83rem",
                text_align="center",
                line_height="1.55",
                max_width="400px",
            ),
            rx.fragment(),
        )

    return rx.box(
        rx.center(
            rx.vstack(
                rx.cond(AppState.step == 0,
                    rx.box(rx.vstack(rx.heading("Shall we begin",size="8"),rx.button("YES",color_scheme="green",on_click=AppState.next_step,size="3",style={"animation":"pulse_glow 2s infinite","cursor":"pointer"})),
                        background_image="url('/bg_image.png')",background_size="cover",width="100vw",height="100vh",display="flex",align_items="center",justify_content="center")),
                rx.cond(AppState.step == 1,
                    rx.box(rx.vstack(rx.heading("Whats your degree",size="7"),rx.select(AppState.options,placeholder="Choose your degree",value=AppState.degree,on_change=AppState.set_degree,width="100%"),rx.button("next",on_click=AppState.advance_from_degree,color_scheme="green",size="3"),onboarding_feedback()),
                        background_image="url('/bg_image.png')",background_size="cover",width="100vw",height="100vh",display="flex",align_items="center",justify_content="center")),
                rx.cond(AppState.step == 2,
                    rx.box(rx.vstack(rx.heading("What's your name?",size="7",color="white"),rx.input(placeholder="Enter your nick name",value=AppState.name,on_change=AppState.set_name,width="100%",size="3"),rx.button("Next",on_click=AppState.advance_from_name,color_scheme="green",size="3"),onboarding_feedback(),spacing="4",width="400px"),
                        background_image="url('/bg_image.png')",background_size="cover",width="100vw",height="100vh",display="flex",align_items="center",justify_content="center")),
                rx.cond(AppState.step == 3,
                    rx.box(rx.vstack(
                        rx.heading("Which year are you in?",size="7",color="white"),
                        subject_button("Year 1", on_click=AppState.choose_onboarding_year("Year 1")),
                        subject_button("Year 2", on_click=AppState.choose_onboarding_year("Year 2")),
                        subject_button("Year 3", on_click=AppState.choose_onboarding_year("Year 3")),
                        subject_button("Year 4", on_click=AppState.choose_onboarding_year("Year 4")),
                        onboarding_feedback(),
                        spacing="4",width="400px"),
                        background_image="url('/bg_image.png')",background_size="cover",width="100vw",height="100vh",display="flex",align_items="center",justify_content="center")),
                rx.cond(AppState.step == 4,
                    rx.box(rx.vstack(
                        rx.heading("Which semester should Alex open?",size="7",color="white"),
                        rx.text(AppState.selected_year,color="rgba(255,255,255,0.72)"),
                        rx.foreach(
                            AppState.available_semesters,
                            lambda sem: subject_button(sem, on_click=AppState.choose_onboarding_semester(sem)),
                        ),
                        rx.button("Back",on_click=AppState.back_to_onboarding_year,variant="outline",color_scheme="gray",size="3"),
                        onboarding_feedback(),
                        spacing="4",width="400px"),
                        background_image="url('/bg_image.png')",background_size="cover",width="100vw",height="100vh",display="flex",align_items="center",justify_content="center")),
                rx.cond(AppState.step == 5,
                    rx.box(rx.vstack(rx.heading(rx.text("Lets crush "),rx.text(AppState.degree),size="7"),rx.text(AppState.selected_year + " • " + AppState.selected_semester,color="rgba(255,255,255,0.72)"),rx.button("begin",on_click=AppState.start_app,color_scheme="green",size="3",style={"animation":"pulse_glow 2s infinite"},is_disabled=(AppState.selected_year == "") | (AppState.selected_semester == "")),onboarding_feedback()),
                        background_image="url('/bg_image.png')",background_size="cover",width="100vw",height="100vh",display="flex",align_items="center",justify_content="center")),
                spacing="4",
            ),
        ),
        height="100vh",
    )


# ──────────────────────────────────────────────────────────────
# Sidebar plan widget
# ──────────────────────────────────────────────────────────────
# FIX 4: sidebar_plan_widget — NO logo (already in header/center), just tier card
def sidebar_plan_widget() -> rx.Component:
    return rx.cond(
        AppState.has_premium_access,
        rx.box(
            rx.vstack(
                rx.text("⚡ Premium Active", font_weight="700", font_size="0.82rem", color="white"),
                rx.text("Unlimited messages", color="rgba(255,255,255,0.45)", font_size="0.7rem"),
                spacing="0",
                align_items="flex-start",
            ),
            on_click=AppState.open_pricing_modal,
            width="100%",
            padding="10px 14px",
            border_radius="10px",
            cursor="pointer",
            style={
                "background": "linear-gradient(135deg, rgba(180,83,9,0.4), rgba(245,158,11,0.25))",
                "border": "1px solid rgba(245,158,11,0.35)",
                "_hover": {"filter": "brightness(1.1)"},
            },
        ),
        rx.cond(
            AppState.is_in_trial,
            rx.box(
                rx.vstack(
                    rx.text("⚡ Trial Active", font_weight="700", font_size="0.82rem", color="white"),
                    rx.text(
                        AppState.trial_days_left.to_string() + " day(s) left",
                        color="rgba(255,255,255,0.45)",
                        font_size="0.7rem",
                    ),
                    spacing="0",
                    align_items="flex-start",
                ),
                on_click=AppState.open_pricing_modal,
                width="100%",
                padding="10px 14px",
                border_radius="10px",
                cursor="pointer",
                style={
                    "background": "rgba(0,255,136,0.08)",
                    "border": "1px solid rgba(0,255,136,0.25)",
                    "_hover": {"filter": "brightness(1.1)"},
                },
            ),
            rx.button(
                rx.hstack(
                    rx.hstack(
                        rx.box(
                            rx.text("✦", color="#dcfce7", font_size="0.78rem", font_weight="800"),
                            width="18px",
                            height="18px",
                            border_radius="999px",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                            background="rgba(220,252,231,0.1)",
                            border="1px solid rgba(220,252,231,0.12)",
                            flex_shrink="0",
                        ),
                        rx.text("Upgrade to Premium", font_size="0.8rem", font_weight="700", color="white"),
                        spacing="2",
                        align="center",
                    ),
                    rx.spacer(),
                    rx.text("→", color="rgba(220,252,231,0.76)", font_size="0.9rem"),
                    width="100%",
                    align="center",
                ),
                on_click=AppState.open_pricing_modal,
                width="100%",
                height="44px",
                border_radius="10px",
                style={
                    "background": "linear-gradient(135deg, rgba(10,24,16,0.98) 0%, rgba(16,68,43,0.92) 46%, rgba(6,8,7,0.98) 100%)",
                    "border": "1px solid rgba(110,231,183,0.24)",
                    "cursor": "pointer",
                    "transition": "all 0.2s ease",
                    "box_shadow": "0 10px 22px rgba(0,0,0,0.24), inset 0 1px 0 rgba(255,255,255,0.04)",
                    "_hover": {
                        "filter": "brightness(1.05)",
                        "border": "1px solid rgba(134,239,172,0.34)",
                        "transform": "translateY(-1px)",
                    },
                },
            ),
        ),
    )


def settings_menu_button() -> rx.Component:
    return rx.menu.root(
        rx.menu.trigger(
            rx.icon_button(
                rx.icon(tag="settings", size=17),
                variant="soft",
                color_scheme="gray",
                size="2",
                title="Settings",
                style={
                    "color": "rgba(245,248,255,0.86)",
                    "background": "rgba(255,255,255,0.08)",
                    "border": "1px solid rgba(255,255,255,0.22)",
                    "box_shadow": "0 0 10px rgba(255,255,255,0.08)",
                    "_hover": {
                        "background": "rgba(255,255,255,0.14)",
                        "border": "1px solid rgba(255,255,255,0.32)",
                    },
                },
            ),
            as_child=True,
        ),
        rx.menu.content(
            rx.menu.item("Return Policy", on_select=rx.redirect("/return-policy")),
            rx.menu.item("Privacy Policy", on_select=rx.redirect("/privacy-policy")),
            rx.menu.item("Terms", on_select=rx.redirect("/terms")),
            rx.menu.item("Support", on_select=rx.redirect("/support")),
            rx.menu.separator(),
            rx.menu.item("Logout", on_select=AppState.logout),
            align="end",
            side_offset=8,
            style={
                "background": "rgba(5,10,12,0.98)",
                "border": "1px solid rgba(0,255,136,0.22)",
                "backdrop_filter": "blur(8px)",
            },
        ),
    )


# ──────────────────────────────────────────────────────────────
# Home page
# ──────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════
# FIX 2: home_page — clean header, aligned sidebar, no yellow blur
def home_page():
    return rx.box(
        # ── Header ────────────────────────────────────────────
        rx.box(
            rx.hstack(
                # Left: greeting
                rx.vstack(
                    rx.text(
                        AppState.greeting_text,
                        color="white",
                        font_size="1rem",
                        font_weight="700",
                        letter_spacing="0.3px",
                    ),
                    rx.text(
                        "Software Engineering",
                        color="rgba(0,255,136,0.65)",
                        font_size="0.72rem",
                        font_weight="500",
                        letter_spacing="1.5px",
                        text_transform="uppercase",
                    ),
                    spacing="1",
                    align_items="flex-start",
                ),

                rx.spacer(),

                # Center: wordmark — clean, no glow blur
                rx.text(
                    "Alex AI",
                    color="white",
                    font_size="1.6rem",
                    font_weight="800",
                    letter_spacing="6px",
                    text_transform="uppercase",
                    style={
                        "background": "linear-gradient(135deg, #ffffff 0%, #a8f5d0 100%)",
                        "-webkit-background-clip": "text",
                        "-webkit-text-fill-color": "transparent",
                        "background-clip": "text",
                    },
                ),

                rx.spacer(),

                # Right: actions
                rx.hstack(
                    rx.button(
                        "+ New chat",
                        on_click=AppState.new_chat,
                        size="2",
                        style={
                            "background": "rgba(0,255,136,0.12)",
                            "border": "1px solid rgba(0,255,136,0.35)",
                            "color": "#00ff88",
                            "font_weight": "600",
                            "border_radius": "8px",
                            "font_size": "0.8rem",
                            "_hover": {"background": "rgba(0,255,136,0.22)"},
                        },
                    ),
                    settings_menu_button(),
                    spacing="2",
                    align="center",
                ),

                width="100%",
                align="center",
                padding="1.55em 2em 1.15em 1.4em",
                border_bottom="1px solid rgba(255,255,255,0.06)",
            ),
            flex_shrink="0",
        ),

        # ── Main area ─────────────────────────────────────────
        rx.flex(
            # ── Left sidebar ──────────────────────────────────
            rx.box(
                workspace_sidebar_content(),
                width="284px",
                flex_shrink="0",
                height="100%",
                border_right="1px solid rgba(255,255,255,0.06)",
                background="rgba(0,0,0,0.15)",
                padding="1.35em 1.05em",
            ),

            # ── Chat area ─────────────────────────────────────
            rx.box(
                chat_panel(),
                flex="1",
                height="100%",
                min_width="0",
                overflow="hidden",
            ),

            width="100%",
            flex="1",
            min_height="0",
            align_items="stretch",
            overflow="hidden",
        ),

        height="100vh",
        overflow="hidden",
        display="flex",
        flex_direction="column",
        background="radial-gradient(ellipse at 80% 100%, #001a0d 0%, #050505 65%)",
    )


def semester_nav_button(year: str, semester: str) -> rx.Component:
    is_active = AppState.is_semester_scope_active(year, semester)
    return rx.button(
        semester,
        on_click=AppState.open_dashboard_semester(year, semester),
        width="100%",
        justify_content="flex-start",
        text_align="left",
        variant="ghost",
        style={
            "background": rx.cond(
                is_active,
                "linear-gradient(135deg, rgba(7,34,22,0.98) 0%, rgba(12,82,50,0.94) 100%)",
                "rgba(255,255,255,0.01)",
            ),
            "border": rx.cond(
                is_active,
                "1px solid rgba(52,211,153,0.76)",
                "1px solid rgba(255,255,255,0.04)",
            ),
            "color": rx.cond(is_active, "#ecfff6", "rgba(255,255,255,0.72)"),
            "font_weight": rx.cond(is_active, "700", "500"),
            "border_radius": "12px",
            "padding": "0.46em 0.72em",
            "font_size": "0.78rem",
            "min_height": "0",
            "box_shadow": rx.cond(
                is_active,
                "0 10px 24px rgba(0,0,0,0.22), 0 0 0 1px rgba(52,211,153,0.14)",
                "none",
            ),
            "_hover": {
                "background": rx.cond(
                    is_active,
                    "linear-gradient(135deg, rgba(9,40,26,0.98) 0%, rgba(14,90,56,0.96) 100%)",
                    "rgba(255,255,255,0.06)",
                ),
                "border": rx.cond(
                    is_active,
                    "1px solid rgba(110,231,183,0.88)",
                    "1px solid rgba(255,255,255,0.12)",
                ),
                "color": "white",
            },
        },
    )


def semester_nav_group(year: str, semesters: list[str]) -> rx.Component:
    return rx.vstack(
        rx.text(
            year,
            color="rgba(255,255,255,0.4)",
            font_size="0.72rem",
            font_weight="700",
            letter_spacing="1.4px",
            text_transform="uppercase",
        ),
        *[semester_nav_button(year, semester) for semester in semesters],
        spacing="1",
        width="100%",
        align_items="stretch",
    )


def semester_chat_history_list() -> rx.Component:
    return rx.vstack(
        rx.foreach(
            AppState.sessions,
            lambda s: rx.hstack(
                rx.button(
                    s["title"],
                    on_click=AppState.switch_chat(s["id"]),
                    variant="ghost",
                    color=rx.cond(
                        AppState.current_session_id == s["id"],
                        "#00ff88",
                        "rgba(255,255,255,0.55)",
                    ),
                    font_weight=rx.cond(
                        AppState.current_session_id == s["id"],
                        "600",
                        "400",
                    ),
                    text_align="left",
                    justify_content="flex-start",
                    flex="1",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                    size="1",
                    font_size="0.8rem",
                ),
                rx.icon_button(
                    rx.icon(tag="trash_2", size=11),
                    on_click=AppState.delete_session(s["id"]),
                    variant="ghost",
                    color_scheme="red",
                    size="1",
                    style={"opacity": "0.4", "_hover": {"opacity": "0.9"}},
                ),
                width="100%",
                align="center",
                spacing="1",
            ),
        ),
        width="100%",
        spacing="0",
        align_items="stretch",
        flex="1",
        min_height="0",
        overflow_y="auto",
    )


def alex_workspace_button() -> rx.Component:
    is_active = AppState.is_home_scope_active
    return rx.button(
        rx.vstack(
            rx.text(
                "Alex AI",
                color=rx.cond(is_active, "#f4fff9", "white"),
                font_size="0.95rem",
                font_weight="700",
                letter_spacing="0.04em",
            ),
            rx.text(
                "Ask doubts in your growth",
                color=rx.cond(is_active, "rgba(240,255,248,0.86)", "rgba(226,232,240,0.68)"),
                font_size="0.76rem",
                text_align="left",
                line_height="1.45",
            ),
            spacing="1",
            align_items="flex-start",
            width="100%",
        ),
        on_click=AppState.go_home,
        width="100%",
        justify_content="flex-start",
        variant="ghost",
        style={
            "height": "auto",
            "padding": "0.9em 0.95em",
            "border_radius": "14px",
            "border": rx.cond(
                is_active,
                "1px solid rgba(52,211,153,0.78)",
                "1px solid rgba(255,255,255,0.08)",
            ),
            "background": rx.cond(
                is_active,
                "linear-gradient(135deg, rgba(7,34,22,0.98) 0%, rgba(12,82,50,0.94) 100%)",
                "rgba(255,255,255,0.03)",
            ),
            "box_shadow": rx.cond(
                is_active,
                "0 12px 24px rgba(0,0,0,0.24), 0 0 0 1px rgba(52,211,153,0.16)",
                "none",
            ),
            "_hover": {
                "background": rx.cond(
                    is_active,
                    "linear-gradient(135deg, rgba(9,40,26,0.98) 0%, rgba(14,90,56,0.96) 100%)",
                    "rgba(255,255,255,0.07)",
                ),
                "border": rx.cond(
                    is_active,
                    "1px solid rgba(110,231,183,0.9)",
                    "1px solid rgba(255,255,255,0.16)",
                ),
            },
        },
    )


def workspace_sidebar_content(show_close_button: bool = False) -> rx.Component:
    header_blocks: list[rx.Component] = []
    if show_close_button:
        header_blocks.append(
            rx.hstack(
                rx.spacer(),
                rx.icon_button(
                    rx.icon(tag="x", size=18),
                    on_click=AppState.close_semester_sidebar,
                    variant="ghost",
                    color="rgba(255,255,255,0.7)",
                ),
                width="100%",
                align="center",
            )
        )

    return rx.vstack(
        *header_blocks,
        alex_workspace_button(),
        rx.box(height="1px", width="100%", background="rgba(255,255,255,0.08)"),
        rx.text(
            "SEMESTERS",
            color="rgba(255,255,255,0.28)",
            font_size="0.68rem",
            letter_spacing="2.4px",
            font_weight="700",
        ),
        semester_nav_group("Year 1", SEMESTER_NAVIGATION["Year 1"]),
        semester_nav_group("Year 2", SEMESTER_NAVIGATION["Year 2"]),
        semester_nav_group("Year 3", SEMESTER_NAVIGATION["Year 3"]),
        semester_nav_group("Year 4", SEMESTER_NAVIGATION["Year 4"]),
        rx.box(height="1px", width="100%", background="rgba(255,255,255,0.08)"),
        rx.text(
            "CHATS",
            color="rgba(255,255,255,0.28)",
            font_size="0.68rem",
            letter_spacing="2.4px",
            font_weight="700",
        ),
        rx.box(
            semester_chat_history_list(),
            width="100%",
            flex="1",
            min_height="0",
        ),
        rx.box(height="1px", width="100%", background="rgba(255,255,255,0.08)"),
        sidebar_plan_widget(),
        spacing="3",
        width="100%",
        height="100%",
        min_height="0",
        align_items="stretch",
    )


def semester_sidebar_drawer() -> rx.Component:
    return rx.cond(
        AppState.show_semester_sidebar,
        rx.fragment(
            rx.box(
                position="fixed",
                inset="0",
                background="rgba(0,0,0,0.58)",
                z_index="30",
                on_click=AppState.close_semester_sidebar,
            ),
            rx.box(
                workspace_sidebar_content(show_close_button=True),
                position="fixed",
                top="0",
                left="0",
                width="320px",
                height="100vh",
                padding="1.3em 1.15em",
                background="rgba(5,8,9,0.98)",
                border_right="1px solid rgba(255,255,255,0.08)",
                z_index="31",
                style={
                    "box_shadow": "24px 0 48px rgba(0,0,0,0.45)",
                    "backdrop_filter": "blur(14px)",
                },
            ),
        ),
        rx.fragment(),
    )


def semester_page():
    return rx.box(
        semester_sidebar_drawer(),
        rx.hstack(
            rx.hstack(
                rx.icon_button(
                    rx.icon(tag="menu", size=18),
                    on_click=AppState.toggle_semester_sidebar,
                    variant="soft",
                    color_scheme="gray",
                    size="2",
                    style={
                        "background": "rgba(255,255,255,0.08)",
                        "border": "1px solid rgba(255,255,255,0.16)",
                        "color": "rgba(255,255,255,0.88)",
                    },
                ),
                rx.vstack(
                    rx.text(
                        rx.cond(AppState.degree != "", AppState.degree, "Software Engineering"),
                        color="white",
                        font_size="1rem",
                        font_weight="700",
                    ),
                    rx.text(
                        AppState.semester_status_label,
                        color="rgba(0,255,136,0.72)",
                        font_size="0.78rem",
                        letter_spacing="0.8px",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.text(
                                AppState.semester_progress_bar_filled,
                                color="rgba(182,255,228,0.96)",
                                font_size="0.78rem",
                                font_family="monospace",
                                letter_spacing="0",
                                line_height="1",
                                style={
                                    "text_shadow": "0 0 12px rgba(52,211,153,0.18)",
                                },
                            ),
                            rx.text(
                                AppState.semester_progress_bar_empty,
                                color="rgba(148,163,184,0.36)",
                                font_size="0.78rem",
                                font_family="monospace",
                                letter_spacing="0",
                                line_height="1",
                            ),
                            spacing="0",
                            align="center",
                            width="100%",
                        ),
                        rx.text(
                            AppState.semester_progress_label,
                            color="rgba(226,232,240,0.84)",
                            font_size="0.76rem",
                            font_family="monospace",
                            letter_spacing="0.4px",
                        ),
                        spacing="1",
                        align_items="flex-start",
                        width="100%",
                        padding_top="0.35em",
                    ),
                    spacing="1",
                    align_items="flex-start",
                    padding_left="0.35em",
                    width="max-content",
                    min_width="max-content",
                ),
                spacing="3",
                align="center",
            ),
            rx.spacer(),
            rx.text(
                "Alex AI",
                color="white",
                font_size="1.45rem",
                font_weight="800",
                letter_spacing="5px",
                text_transform="uppercase",
                style={
                    "background": "linear-gradient(135deg, #ffffff 0%, #a8f5d0 100%)",
                    "-webkit-background-clip": "text",
                    "-webkit-text-fill-color": "transparent",
                    "background-clip": "text",
                },
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    "+ New chat",
                    on_click=AppState.new_chat,
                    size="2",
                    style={
                        "background": "rgba(0,255,136,0.12)",
                        "border": "1px solid rgba(0,255,136,0.35)",
                        "color": "#00ff88",
                        "font_weight": "600",
                        "border_radius": "8px",
                        "font_size": "0.8rem",
                        "_hover": {"background": "rgba(0,255,136,0.22)"},
                    },
                ),
                settings_menu_button(),
                spacing="2",
                align="center",
            ),
            width="100%",
            padding="1.2em 1.5em",
            flex_shrink="0",
            align="center",
            border_bottom="1px solid rgba(255,255,255,0.06)",
        ),
        rx.cond(
            AppState.is_generating_plan,
            rx.box(
                rx.hstack(
                    rx.spinner(size="1", color="#34d399"),
                    rx.text(
                        "Preparing your 110-day study plan in the background...",
                        color="rgba(220,252,231,0.92)",
                        font_size="0.86rem",
                        font_weight="600",
                    ),
                    spacing="2",
                    align="center",
                ),
                width="100%",
                padding="0.72em 1.5em",
                background="linear-gradient(180deg, rgba(7,24,15,0.9) 0%, rgba(5,16,11,0.72) 100%)",
                border_bottom="1px solid rgba(110,231,183,0.14)",
            ),
            rx.cond(
                AppState.plan_generation_error != "",
                rx.box(
                    rx.hstack(
                        rx.text(
                            AppState.plan_generation_error,
                            color="rgba(255,236,204,0.96)",
                            font_size="0.86rem",
                            font_weight="600",
                        ),
                        rx.spacer(),
                        rx.button(
                            "Retry",
                            on_click=AppState.retry_study_plan_generation,
                            size="1",
                            variant="soft",
                            color_scheme="orange",
                        ),
                        spacing="3",
                        align="center",
                        width="100%",
                    ),
                    width="100%",
                    padding="0.72em 1.5em",
                    background="linear-gradient(180deg, rgba(42,18,6,0.92) 0%, rgba(28,12,4,0.78) 100%)",
                    border_bottom="1px solid rgba(251,191,36,0.18)",
                ),
                rx.fragment(),
            ),
        ),
        rx.cond(
            AppState.scope_hydrating,
            rx.box(
                rx.hstack(
                    rx.spinner(size="1", color="rgba(148,163,184,0.7)"),
                    rx.text(
                        "Loading workspace...",
                        color="rgba(226,232,240,0.64)",
                        font_size="0.82rem",
                        font_weight="500",
                    ),
                    spacing="2",
                    align="center",
                ),
                width="100%",
                padding="0.55em 1.5em",
                background="rgba(255,255,255,0.02)",
                border_bottom="1px solid rgba(255,255,255,0.04)",
            ),
            rx.fragment(),
        ),
        rx.box(
            chat_panel(),
            width="100%",
            flex="1",
            min_height="0",
            overflow="hidden",
            position="relative",
        ),
        rx.html("<style>@keyframes bounce{0%,100%{transform:translateY(0);opacity:0.4;}50%{transform:translateY(-6px);opacity:1;}}</style>"),
        width="100%", height="100vh", max_height="100vh", display="flex", flex_direction="column", overflow="hidden",
        background=(
            "radial-gradient(circle at 82% 86%, rgba(12,38,26,0.52) 0%, rgba(7,18,13,0.2) 34%, transparent 58%),"
            "linear-gradient(180deg, #060907 0%, #030504 54%, #020303 100%)"
        ),
    )

def require_app_login(page: rx.app.ComponentCallable) -> rx.app.ComponentCallable:
    def protected_page():
        return rx.fragment(
            rx.cond(
                AppState.is_hydrated,
                # Render the page shell immediately after hydration.
                # on_load handles auth check + redirect for unauthenticated users.
                page(),
                # Pre-hydration: dark background only, no blocking text.
                rx.box(
                    width="100vw",
                    min_height="100vh",
                    background=(
                        "linear-gradient(180deg, #060907 0%, #030504 54%, #020303 100%)"
                    ),
                    on_mount=AppState.auth_redir,
                ),
            )
        )

    protected_page.__name__ = page.__name__
    return protected_page


def _auth_error(text_var: rx.Var) -> rx.Component:
    return rx.cond(
        text_var != "",
        rx.callout(text_var, icon="triangle_alert", color_scheme="red", role="alert", width="100%"),
        rx.fragment(),
    )


AUTH_CARD_WIDTH = "min(92vw, 760px)"


def _csrf_field() -> rx.Component:
    return rx.input(
        name="csrf_token",
        type="hidden",
        value=AppState.auth_csrf_token,
        display="none",
        width="0",
        height="0",
        opacity="0",
    )


def _google_inline_button() -> rx.Component:
    return rx.cond(
        GOOGLE_OAUTH_ENABLED,
        
        rx.button(
            rx.hstack(
                rx.box(
                    "G",
                    width="22px",
                    height="22px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    border_radius="9999px",
                    background="linear-gradient(135deg,#ea4335,#4285f4)",
                    color="white",
                    font_weight="900",
                    font_size="0.78rem",
                    flex_shrink="0",
                ),
                rx.text("Continue with Google", font_weight="700", letter_spacing="0.2px"),
                align="center",
                justify="center",
                spacing="2",
                width="100%",
            ),
            on_click=AppState.start_google_oauth,
            width="100%",
            type="button",
            height="46px",
            border_radius="12px",
            background="linear-gradient(180deg,#f9fafb 0%,#eef2f7 100%)",
            color="#0f172a",
            border="1px solid rgba(148,163,184,0.45)",
            box_shadow="0 10px 30px rgba(0,0,0,0.24)",
            _hover={
                "background": "linear-gradient(180deg,#ffffff 0%,#f3f6fb 100%)",
                "transform": "translateY(-1px)",
            },
            _active={"transform": "translateY(0)"},
        ),
        rx.fragment(),
    )


def _or_divider() -> rx.Component:
    return rx.hstack(
        rx.box(height="1px", background="rgba(148,163,184,0.35)", flex="1"),
        rx.text("or", color="rgba(226,232,240,0.85)", font_size="0.85rem", font_weight="600", padding="0 10px"),
        rx.box(height="1px", background="rgba(148,163,184,0.35)", flex="1"),
        width="100%",
        align="center",
    )


def secure_login_form() -> rx.Component:
    return rx.form(
        rx.vstack(
            rx.heading("Login to Alex AI", size="7"),
            _auth_error(AppState.login_error),
            _google_inline_button(),
            rx.cond(GOOGLE_OAUTH_ENABLED, _or_divider(), rx.fragment()),
            rx.text("Username"),
            rx.input(id="username", name="username", width="100%"),
            rx.text("Password"),
            rx.input(id="password", name="password", type="password", width="100%"),
            _csrf_field(),
            rx.button("Sign in", width="100%"),
            rx.hstack(
                rx.link("Register", on_click=lambda: rx.redirect(auth_routes.REGISTER_ROUTE)),
                rx.spacer(),
                rx.link("Reset Password", on_click=lambda: rx.redirect("/reset-password")),
                width="100%",
            ),
            width="100%",
            spacing="3",
        ),
        on_submit=AppState.handle_login,
        width="100%",
    )


def secure_register_form() -> rx.Component:
    return rx.form(
        rx.vstack(
            rx.heading("Create your Alex AI account", size="7"),
            _auth_error(AppState.register_error),
            rx.cond(
                AppState.register_success,
                rx.callout("Registration successful. You can now sign in.", icon="check", color_scheme="green", width="100%"),
                rx.fragment(),
            ),
            rx.text("Username"),
            rx.input(id="username", name="username", width="100%"),
            rx.text("Password"),
            rx.input(id="password", name="password", type="password", width="100%"),
            rx.text("Confirm Password"),
            rx.input(id="confirm_password", name="confirm_password", type="password", width="100%"),
            _csrf_field(),
            rx.button("Sign up", width="100%"),
            rx.center(rx.link("Login", on_click=lambda: rx.redirect(auth_routes.LOGIN_ROUTE)), width="100%"),
            width="100%",
            spacing="3",
        ),
        on_submit=AppState.handle_registration,
        width="100%",
    )


def secure_reset_form() -> rx.Component:
    return rx.form(
        rx.vstack(
            rx.heading("Reset your Alex AI password", size="7"),
            _auth_error(AppState.reset_error),
            rx.cond(
                AppState.reset_success,
                rx.callout("Password updated. Please login with the new password.", icon="check", color_scheme="green", width="100%"),
                rx.fragment(),
            ),
            rx.text("Username"),
            rx.input(id="username", name="username", width="100%"),
            rx.text("Current Password"),
            rx.input(id="current_password", name="current_password", type="password", width="100%"),
            rx.text("New Password"),
            rx.input(id="new_password", name="new_password", type="password", width="100%"),
            rx.text("Confirm New Password"),
            rx.input(id="confirm_new_password", name="confirm_new_password", type="password", width="100%"),
            _csrf_field(),
            rx.button("Update Password", width="100%"),
            rx.center(rx.link("Back to Login", on_click=lambda: rx.redirect(auth_routes.LOGIN_ROUTE)), width="100%"),
            width="100%",
            spacing="3",
        ),
        on_submit=AppState.handle_password_reset,
        width="100%",
    )


def _auth_legal_footer() -> rx.Component:
    """Professional legal footer shown on all auth pages (login / register / reset)."""
    link_style = {
        "color": "rgba(148,163,184,0.75)",
        "font_size": "0.78rem",
        "text_decoration": "none",
        "_hover": {"color": "#00ff88", "text_decoration": "underline"},
        "transition": "color 0.15s ease",
        "white_space": "nowrap",
    }
    divider = rx.text("·", color="rgba(148,163,184,0.35)", font_size="0.78rem")
    return rx.box(
        rx.hstack(
            rx.link("Return Policy",  href="/return-policy",  **link_style),
            divider,
            rx.link("Privacy Policy", href="/privacy-policy", **link_style),
            divider,
            rx.link("Terms",          href="/terms",          **link_style),
            divider,
            rx.link("Support",        href="/support",        **link_style),
            align="center",
            justify="center",
            flex_wrap="wrap",
            spacing="2",
            width="100%",
        ),
        rx.text(
            f"© {CURRENT_COPYRIGHT_YEAR} {BUSINESS_NAME}. All rights reserved.",
            color="rgba(100,116,139,0.55)",
            font_size="0.72rem",
            text_align="center",
            margin_top="6px",
        ),
        width="100%",
        text_align="center",
        padding="18px 0 10px",
        z_index="2",
    )


def _auth_page_shell(content: rx.Component) -> rx.Component:
    return rx.box(
        rx.image(src="/bg_image.png", position="fixed", top="0", left="0", width="100vw", height="100vh", object_fit="cover", z_index="-1"),
        rx.box(
            rx.center(
                rx.card(
                    content,
                    width=AUTH_CARD_WIDTH,
                    padding="22px 14px",
                    border="1px solid rgba(34,197,94,0.20)",
                    border_radius="12px",
                    background="linear-gradient(120deg,rgba(2,16,22,0.88),rgba(17,74,72,0.52))",
                ),
                width="100%",
                padding_top="0",
            ),
            _auth_legal_footer(),
            display="flex",
            flex_direction="column",
            justify_content="center",
            align_items="center",
            min_height="100vh",
            padding="20px 16px",
            z_index="1",
        ),
        password_eye_script(),
        auth_token_bootstrap_script(),
        width="100vw", min_height="100vh", position="relative", overflow_x="hidden",
        on_mount=AppState.init_auth_forms,
    )


def custom_login_page():
    return _auth_page_shell(secure_login_form())


def custom_register_page():
    return _auth_page_shell(secure_register_form())


def reset_password_page():
    return _auth_page_shell(secure_reset_form())


def _fullscreen_loading_gate(title: str, subtitle: str) -> rx.Component:
    return rx.center(
        # ── Spotlight cone above logo ──
        rx.box(
            position="absolute",
            top="-80px",
            left="50%",
            transform="translateX(-50%)",
            width="160px",
            height="200px",
            background="linear-gradient(180deg, rgba(200,240,220,0.10) 0%, rgba(52,211,153,0.03) 60%, transparent 100%)",
            clip_path="polygon(40% 0%, 60% 0%, 78% 100%, 22% 100%)",
            animation="splashSpotlight 4s ease-in-out infinite",
            pointer_events="none",
        ),
        rx.vstack(
            # ── Logo with 3D float + glow ──
            rx.box(
                # Logo container with float + glow
                rx.box(
                    rx.image(
                        src="/a_logo.png",
                        width="110px",
                        height="110px",
                        border_radius="24px",
                        object_fit="cover",
                        display="block",
                    ),
                    # Glass highlight overlay
                    rx.box(
                        position="absolute",
                        top="0",
                        left="0",
                        right="0",
                        bottom="0",
                        border_radius="24px",
                        background="linear-gradient(135deg, rgba(255,255,255,0.06) 0%, transparent 40%)",
                        pointer_events="none",
                    ),
                    width="110px",
                    height="110px",
                    border_radius="24px",
                    overflow="hidden",
                    border="1px solid rgba(52,211,153,0.10)",
                    position="relative",
                    animation="splashFloat 7s ease-in-out 1s infinite, splashGlowBreath 5s ease-in-out 1s infinite",
                ),
                animation="splashLogoEntry 1s cubic-bezier(0.16,1,0.3,1) both",
                transform_style="preserve-3d",
            ),
            # ── Floor shadow ──
            rx.box(
                width="70px",
                height="8px",
                border_radius="50%",
                background="radial-gradient(ellipse, rgba(52,211,153,0.16) 0%, transparent 70%)",
                filter="blur(3px)",
                margin_top="-4px",
                animation="splashShadow 7s ease-in-out 1s infinite",
            ),
            # ── Brand text ──
            rx.text(
                "A L E X   A I",
                color="rgba(255,255,255,0.95)",
                font_size="1.35rem",
                font_weight="700",
                letter_spacing="0.20em",
                font_family="'Space Grotesk', 'Plus Jakarta Sans', sans-serif",
                text_shadow="0 1px 10px rgba(52,211,153,0.12)",
                animation="splashFadeUp 0.7s ease-out 0.4s both",
                margin_top="12px",
            ),
            # ── Subtitle ──
            rx.text(
                subtitle,
                color="rgba(226,232,240,0.35)",
                font_size="0.8rem",
                font_weight="400",
                letter_spacing="0.04em",
                animation="splashFadeUp 0.7s ease-out 0.6s both",
            ),
            # ── Shimmer loading bar ──
            rx.box(
                rx.box(
                    width="40%",
                    height="100%",
                    border_radius="2px",
                    background="linear-gradient(90deg, transparent, rgba(52,211,153,0.45), transparent)",
                    animation="splashShimmer 1.5s ease-in-out infinite",
                ),
                width="90px",
                height="2px",
                border_radius="2px",
                background="rgba(52,211,153,0.07)",
                overflow="hidden",
                margin_top="6px",
                animation="splashFadeUp 0.7s ease-out 0.75s both",
            ),
            spacing="2",
            align_items="center",
        ),
        # ── Keyframes ──
        rx.el.style("""
            @keyframes splashLogoEntry {
                0% { opacity: 0; transform: perspective(900px) rotateX(20deg) rotateY(-8deg) scale(0.7) translateY(30px); }
                60% { opacity: 1; transform: perspective(900px) rotateX(-2deg) rotateY(2deg) scale(1.02) translateY(-4px); }
                100% { opacity: 1; transform: perspective(900px) rotateX(0) rotateY(0) scale(1) translateY(0); }
            }
            @keyframes splashFloat {
                0%, 100% { transform: perspective(900px) translateY(0px) rotateX(0deg) rotateY(0deg); }
                20% { transform: perspective(900px) translateY(-7px) rotateX(2deg) rotateY(-2.5deg); }
                50% { transform: perspective(900px) translateY(-3px) rotateX(-1.5deg) rotateY(3deg); }
                75% { transform: perspective(900px) translateY(-9px) rotateX(1deg) rotateY(-1.5deg); }
            }
            @keyframes splashGlowBreath {
                0%, 100% { box-shadow: 0 6px 30px rgba(52,211,153,0.12), 0 0 50px rgba(52,211,153,0.06), 0 20px 50px rgba(0,0,0,0.5); }
                50% { box-shadow: 0 10px 40px rgba(52,211,153,0.22), 0 0 70px rgba(52,211,153,0.10), 0 28px 60px rgba(0,0,0,0.6); }
            }
            @keyframes splashShadow {
                0%, 100% { transform: scaleX(1) scaleY(1); opacity: 0.4; }
                20% { transform: scaleX(0.92) scaleY(0.95); opacity: 0.5; }
                50% { transform: scaleX(1.04) scaleY(1.02); opacity: 0.35; }
                75% { transform: scaleX(0.9) scaleY(0.94); opacity: 0.5; }
            }
            @keyframes splashFadeUp {
                0% { opacity: 0; transform: translateY(16px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            @keyframes splashShimmer {
                0% { transform: translateX(-120px); }
                100% { transform: translateX(160px); }
            }
            @keyframes splashSpotlight {
                0%, 100% { opacity: 0.07; }
                50% { opacity: 0.14; }
            }
        """),
        width="100vw",
        min_height="100vh",
        padding="24px",
        position="relative",
        overflow="hidden",
        perspective="900px",
        background=(
            "radial-gradient(ellipse at 50% 35%, rgba(52,211,153,0.09) 0%, transparent 55%),"
            "radial-gradient(circle at 30% 70%, rgba(52,211,153,0.04) 0%, transparent 40%),"
            "linear-gradient(180deg, #060f0a 0%, #040a07 50%, #030806 100%)"
        ),
    )


@rx.page(
    route="/",
    title="Alex AI | AI Study Assistant for University Students",
    description="Alex AI analyzes your degree, organizes each semester, and guides you day by day with a structured 105-day learning plan.",
    image=FAVICON_32,
    on_load=AppState.on_load_public_landing,
    meta=[
        {"name": "keywords", "content": "AI study assistant, university students, semester learning, guided study plan"},
        {"name": "robots", "content": "index, follow"},
        {"property": "og:title", "content": "Alex AI | AI Study Assistant for University Students"},
        {"property": "og:url", "content": "https://alexstudies.com"},
        {"property": "og:type", "content": "website"},
    ],
)
def landing_page():
    def hero_detail_row(title: str, body: str) -> rx.Component:
        return rx.hstack(
            rx.box(
                width="12px",
                height="12px",
                border_radius="9999px",
                background="linear-gradient(135deg,var(--landing-accent) 0%, var(--landing-accent-2) 100%)",
                box_shadow="0 0 20px rgba(56,189,248,0.28)",
                flex_shrink="0",
                margin_top="7px",
            ),
            rx.vstack(
                rx.text(title, color="white", font_weight="700"),
                rx.text(body, color="rgba(226,232,240,0.74)", line_height="1.7"),
                spacing="1",
                align_items="flex-start",
                width="100%",
            ),
            align="start",
            spacing="3",
            width="100%",
        )

    def feature_grid() -> rx.Component:
        return rx.box(
            _marketing_card(
                "Students enter their degree name",
                "A student begins by entering the degree they are studying, so Alex AI can understand the academic path ahead.",
                "01",
            ),
            _marketing_card(
                "AI analyzes subjects and semester structure",
                "Alex AI reviews the semester flow and subject breakdown so the learning sequence follows the degree structure.",
                "02",
            ),
            _marketing_card(
                "AI creates a semester-wise learning path",
                "The platform organizes the degree semester by semester instead of showing a generic course list.",
                "03",
            ),
            _marketing_card(
                "Students get daily guided teaching for 105 days per semester",
                "Each semester is turned into a guided 105-day plan so students know what to learn each day.",
                "04",
            ),
            _marketing_card(
                "It acts like a digital university professor",
                "Alex AI explains topics, keeps the plan structured, and supports students with daily academic guidance.",
                "05",
            ),
            display="grid",
            grid_template_columns="repeat(auto-fit, minmax(220px, 1fr))",
            gap="18px",
            width="100%",
        )

    def steps_grid() -> rx.Component:
        return rx.box(
            _marketing_step_card(
                "1",
                "Enter your degree",
                "Start by telling Alex AI what degree program you are studying.",
            ),
            _marketing_step_card(
                "2",
                "AI analyzes your semester subjects",
                "The system maps subjects and semesters to understand your academic structure.",
            ),
            _marketing_step_card(
                "3",
                "Receive a 105-day guided plan",
                "Each semester is organized into a structured study path with a daily schedule.",
            ),
            _marketing_step_card(
                "4",
                "Learn daily with AI support",
                "Students study day by day with AI teaching support that feels like a digital university professor.",
            ),
            display="grid",
            grid_template_columns="repeat(auto-fit, minmax(220px, 1fr))",
            gap="18px",
            width="100%",
        )

    def audience_grid() -> rx.Component:
        return rx.box(
            _marketing_card(
                "University students",
                "Built for learners who need a clear academic support system throughout their university journey.",
            ),
            _marketing_card(
                "Degree students",
                "Made for students studying full degree programs that need semester-wise organization.",
            ),
            _marketing_card(
                "Students who want step-by-step semester guidance",
                "Ideal for learners who want the next academic step explained clearly instead of guessing what comes next.",
            ),
            _marketing_card(
                "Students who need structured daily study help",
                "Designed for students who stay consistent when daily tasks are mapped out with clear guidance.",
            ),
            display="grid",
            grid_template_columns="repeat(auto-fit, minmax(220px, 1fr))",
            gap="18px",
            width="100%",
        )

    def pricing_card() -> rx.Component:
        feature_style = {
            "color": "rgba(226,232,240,0.82)",
            "font_size": "0.98rem",
            "line_height": "1.7",
        }
        return rx.box(
            rx.vstack(
                _marketing_badge("PRICING"),
                rx.heading(
                    "Monthly Plan",
                    color="white",
                    font_size="clamp(2rem, 4vw, 3rem)",
                    line_height="1.05",
                    font_family="var(--landing-display-font)",
                ),
                rx.hstack(
                    rx.text(
                        "USD 3.20",
                        color="white",
                        font_size="clamp(2.2rem, 4.4vw, 3.4rem)",
                        font_weight="800",
                        line_height="1",
                        font_family="var(--landing-display-font)",
                    ),
                    rx.text(
                        "/ month",
                        color="rgba(148,163,184,0.86)",
                        font_size="1.05rem",
                        font_weight="600",
                        align_self="end",
                        padding_bottom="7px",
                    ),
                    spacing="2",
                    align="end",
                    width="100%",
                ),
                rx.text(
                    "Simple recurring access for AI-powered semester guidance.",
                    color="rgba(226,232,240,0.76)",
                    font_size="1.02rem",
                    line_height="1.8",
                    max_width="620px",
                ),
                rx.vstack(
                    rx.text("• AI semester guidance", **feature_style),
                    rx.text("• Daily teaching support", **feature_style),
                    rx.text("• Structured semester learning", **feature_style),
                    rx.text("• Semester-wise study planning", **feature_style),
                    spacing="2",
                    align_items="flex-start",
                    width="100%",
                ),
                rx.vstack(
                    _marketing_button("Get Started", auth_routes.LOGIN_ROUTE),
                    rx.text(
                        "Secure student login required before checkout.",
                        color="rgba(148,163,184,0.82)",
                        font_size="0.9rem",
                        line_height="1.6",
                        width="100%",
                    ),
                    spacing="2",
                    align_items="flex-start",
                    width="100%",
                ),
                spacing="4",
                align_items="flex-start",
                width="100%",
            ),
            padding="clamp(28px, 4vw, 42px)",
            border_radius="30px",
            border="1px solid var(--landing-border)",
            background="linear-gradient(135deg,rgba(7,12,24,0.88) 0%, rgba(8,18,31,0.78) 55%, rgba(6,12,24,0.88) 100%)",
            box_shadow="0 28px 90px rgba(2,6,23,0.42)",
            width="100%",
        )

    def trust_grid() -> rx.Component:
        return rx.vstack(
            rx.box(
                _marketing_card(
                    "AI-powered education platform",
                    "Alex AI is a focused study service built to support university learning with AI guidance.",
                ),
                _marketing_card(
                    "Semester-wise learning guidance",
                    "The platform explains the degree structure semester by semester instead of giving a generic chatbot response.",
                ),
                _marketing_card(
                    "Daily structured study support",
                    "Students receive daily learning direction through a structured semester plan they can actually follow.",
                ),
                _marketing_card(
                    "Student-focused academic assistance",
                    "Alex AI is designed for students who want practical academic help, not just open-ended AI chat.",
                ),
                display="grid",
                grid_template_columns="repeat(auto-fit, minmax(220px, 1fr))",
                gap="18px",
                width="100%",
            ),
            rx.box(
                rx.vstack(
                    rx.text(
                        "Alex AI makes the service understandable before login.",
                        color="white",
                        font_weight="700",
                        font_size="1.05rem",
                        font_family="var(--landing-display-font)",
                    ),
                    rx.text(
                        "Students, parents, and business reviewers can see what the product does, who it is for, how it works, and where to find support and policy information before any sign-in step.",
                        color="rgba(226,232,240,0.76)",
                        line_height="1.8",
                    ),
                    spacing="2",
                    align_items="flex-start",
                    width="100%",
                ),
                padding="24px",
                border_radius="24px",
                border="1px solid rgba(56,189,248,0.18)",
                background="linear-gradient(180deg,rgba(8,16,29,0.78),rgba(6,11,22,0.62))",
                width="100%",
            ),
            spacing="4",
            width="100%",
            align_items="stretch",
        )

    hero = rx.box(
        rx.box(
            rx.vstack(
                _marketing_badge("AI-powered study platform"),
                rx.heading(
                    "AI Study Assistant for University Students",
                    color="white",
                    font_size="clamp(2.9rem, 7vw, 5.4rem)",
                    line_height="0.98",
                    letter_spacing="-0.05em",
                    font_family="var(--landing-display-font)",
                    max_width="760px",
                ),
                rx.text(
                    "Alex AI analyzes your degree organizes each semester and guides you day by day with a structured 105-day learning plan",
                    color="rgba(226,232,240,0.8)",
                    font_size="clamp(1rem, 2vw, 1.18rem)",
                    line_height="1.8",
                    max_width="720px",
                ),
                rx.hstack(
                    _marketing_button("Start Learning", auth_routes.LOGIN_ROUTE),
                    _marketing_button("Contact Support", "/support", "secondary"),
                    gap="14px",
                    flex_wrap="wrap",
                    width="100%",
                ),
                rx.box(
                    _marketing_card(
                        "Semester-wise AI guidance",
                        "Students get a clearer path through each semester before they begin the daily plan.",
                    ),
                    _marketing_card(
                        "105-day guided teaching",
                        "Each semester is taught through a structured day-by-day learning sequence.",
                    ),
                    _marketing_card(
                        "Public support and policy pages",
                        "Support, terms, privacy, and return policy stay visible before login.",
                    ),
                    display="grid",
                    grid_template_columns="repeat(auto-fit, minmax(210px, 1fr))",
                    gap="16px",
                    width="100%",
                ),
                spacing="5",
                align_items="flex-start",
                width="100%",
            ),
            rx.box(
                rx.vstack(
                    _marketing_badge("What Alex AI Does"),
                    rx.heading(
                        "A digital university professor for each semester",
                        size="7",
                        color="white",
                        font_family="var(--landing-display-font)",
                    ),
                    hero_detail_row(
                        "Students enter a degree name",
                        "Alex AI starts with the degree program so the guidance matches the student's academic path.",
                    ),
                    hero_detail_row(
                        "AI organizes the semester structure",
                        "Subjects are analyzed semester by semester to build a realistic study sequence.",
                    ),
                    hero_detail_row(
                        "A 105-day semester plan is generated",
                        "Each semester becomes a guided daily plan instead of an unstructured list of topics.",
                    ),
                    hero_detail_row(
                        "Daily AI teaching support stays available",
                        "Students learn step by step with AI support throughout the semester journey.",
                    ),
                    rx.box(
                        rx.text(
                            "This is a real student-facing education service with public support and policy pages available before login.",
                            color="rgba(226,232,240,0.78)",
                            line_height="1.8",
                        ),
                        padding="20px",
                        border_radius="22px",
                        border="1px solid rgba(52,211,153,0.18)",
                        background="rgba(7,14,24,0.68)",
                        width="100%",
                    ),
                    spacing="4",
                    align_items="flex-start",
                    width="100%",
                ),
                padding="clamp(26px, 4vw, 38px)",
                border_radius="30px",
                border="1px solid var(--landing-border)",
                background="linear-gradient(180deg,rgba(7,12,24,0.84),rgba(5,8,17,0.66))",
                box_shadow="0 28px 90px rgba(2,6,23,0.42)",
                backdrop_filter="blur(18px)",
                width="100%",
            ),
            display="grid",
            grid_template_columns="repeat(auto-fit, minmax(320px, 1fr))",
            gap="24px",
            width="100%",
            align_items="stretch",
        ),
        padding_top="10px",
        width="100%",
    )

    public_landing = _public_page_frame(
        rx.vstack(
            hero,
            _marketing_section(
                "What Alex AI Does",
                "A clear public explanation of the service",
                "Alex AI is built for university students who need a guided way to understand and study their degree structure.",
                feature_grid(),
                "what-alex-ai-does",
            ),
            _marketing_section(
                "How It Works",
                "From degree name to guided daily learning",
                "The product flow is simple and understandable before any login or payment step.",
                steps_grid(),
                "how-it-works",
            ),
            _marketing_section(
                "Who It's For",
                "Built for students who need structured academic guidance",
                "Alex AI serves students who want semester-by-semester direction and daily study support instead of figuring out the path alone.",
                audience_grid(),
                "who-its-for",
            ),
            pricing_card(),
            _marketing_section(
                "Trust and Clarity",
                "A real education platform with clear public information",
                "The service, support details, and public policy pages are visible before login so visitors can understand the business and the product immediately.",
                trust_grid(),
                "trust-and-clarity",
            ),
            spacing="6",
            width="100%",
            align_items="stretch",
        )
    )
    return rx.cond(
        AppState.root_public_ready & ~AppState.is_authenticated_now,
        public_landing,
        _fullscreen_loading_gate("Loading...", "Preparing your workspace"),
    )


@rx.page(
    route=APP_DASHBOARD_ROUTE,
    title="Alex AI Dashboard",
    description="Alex AI student dashboard",
    image=FAVICON_32,
    on_load=AppState.on_load,
)
@require_app_login
def index():
    # on_load redirects started users to /app/home or /app/y1s1 etc.
    # This page only renders for users still in onboarding.
    return onboarding_page()


@rx.page(
    route="/s/[scope]",
    title="Alex AI",
    description="Alex AI study workspace",
    image=FAVICON_32,
    on_load=AppState.on_load_scope_page,
)
@require_app_login
def scope_page():
    return rx.cond(
        AppState.view_mode == "home",
        home_page(),
        semester_page(),
    )

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if ENFORCE_HTTPS:
            proto = (
                request.headers.get("x-forwarded-proto") or ""
            ).split(",")[0].strip().lower()
            if proto == "http":
                https_url = str(request.url).replace("http://", "https://", 1)
                return StarletteRedirect(https_url, status_code=301)
        return await call_next(request)


# ──────────────────────────────────────────────────────────────
# App init
# ──────────────────────────────────────────────────────────────
app = rx.App(
    head_components=[
        rx.el.link(rel="icon", type="image/x-icon", href=FAVICON_ICO),
        rx.el.link(rel="shortcut icon", type="image/x-icon", href=FAVICON_ICO),
        rx.el.link(rel="icon", type="image/png", sizes="32x32", href=FAVICON_32),
        rx.el.link(rel="icon", type="image/png", sizes="16x16", href=FAVICON_16),
        rx.el.link(rel="apple-touch-icon", sizes="180x180", href=APPLE_TOUCH_ICON),
        rx.el.link(rel="manifest", href="/site.webmanifest"),
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        rx.el.link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap",
        ),
    ],
    style={
        "@keyframes pulse_glow": {
            "0%": {"box-shadow": "0 0 0px rgba(0,255,0,0)"},
            "50%": {"box-shadow": "0 0 20px rgba(0,255,0,0.5)", "opacity": "0.8"},
            "100%": {"box-shadow": "0 0 0px rgba(0,255,0,0)"},
        }
    },
)
api = app._api
if api is None:
    raise RuntimeError("Reflex API not initialized; cannot register middleware and routes.")
api.add_middleware(HTTPSRedirectMiddleware)


async def google_start(request: Request):
    if not GOOGLE_OAUTH_ENABLED:
        return RedirectResponse(url=f"{_frontend_base_url(request)}{auth_routes.LOGIN_ROUTE}", status_code=302)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": _google_callback_url(request),
        "response_type": "code",
        "scope": "openid email profile",
        "state": _google_make_state(),
        "prompt": "select_account",
    }
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{urlencode(params)}", status_code=302)


async def google_callback(request: Request):
    if not GOOGLE_OAUTH_ENABLED:
        return RedirectResponse(url=f"{_frontend_base_url(request)}{auth_routes.LOGIN_ROUTE}", status_code=302)
    try:
        print(f"[Google CB] started, params: {dict(request.query_params)}")
        
        if request.query_params.get("error"):
            print(f"[Google CB] error param: {request.query_params.get('error')}")
            return RedirectResponse(url=f"{_frontend_base_url(request)}{auth_routes.LOGIN_ROUTE}", status_code=302)
        
        # ADD THIS near the top of google_callback():
        state = str(request.query_params.get("state", "") or "")
        if not _google_state_is_valid(state):
            return RedirectResponse(url=f"{_frontend_base_url(request)}{auth_routes.LOGIN_ROUTE}", status_code=302)

        code = str(request.query_params.get("code", "") or "")
        if not code:
            print("[Google CB] no code")
            return RedirectResponse(url=f"{_frontend_base_url(request)}{auth_routes.LOGIN_ROUTE}", status_code=302)

        print("[Google CB] got code, fetching token...")
        async with httpx.AsyncClient(timeout=20.0) as client_http:
            token_resp = await client_http.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": _google_callback_url(request),
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            print(f"[Google CB] token response status: {token_resp.status_code}")
            token_resp.raise_for_status()
            token = token_resp.json()
            access_token = str(token.get("access_token", "") or "")
            id_token_val = str(token.get("id_token", "") or "")
            userinfo: dict[str, Any] = {}

            if access_token:
                try:
                    userinfo_resp = await client_http.get(
                        GOOGLE_USERINFO_URL,
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    userinfo_resp.raise_for_status()
                    payload = userinfo_resp.json() or {}
                    if isinstance(payload, dict):
                        userinfo = payload
                    print(f"[Google CB] userinfo ok, sub: {userinfo.get('sub','')[:8]}")
                except Exception as ue:
                    print(f"[Google CB] userinfo failed: {ue}")
                    userinfo = _id_token_payload(id_token_val)
            else:
                userinfo = _id_token_payload(id_token_val)

        subject = str((userinfo or {}).get("sub", "")).strip()
        if not subject:
            print("[Google CB] no subject in userinfo")
            raise ValueError("Google userinfo missing subject.")

        username = _google_username_from_sub(subject)
        print(f"[Google CB] username: {username}")

        with rx.session() as session:
            user = session.exec(
                select(LocalUser).where(func.lower(LocalUser.username) == username.lower())
            ).one_or_none()

            if user is None:
                user = LocalUser(
                    username=username,
                    password_hash=LocalUser.hash_password(secrets.token_urlsafe(40)),
                    enabled=True,
                )
                session.add(user)
                session.commit()
                session.refresh(user)
                print(f"[Google CB] new user created id={user.id}")
            else:
                print(f"[Google CB] existing user id={user.id}")

            if user.id is None:
                raise ValueError("Unable to create a valid local user for Google login.")

            auth_token = secrets.token_urlsafe(32)
            session.add(
                LocalAuthSession(
                    user_id=int(user.id),
                    session_id=auth_token,
                    expiration=datetime.now(timezone.utc) + timedelta(seconds=GOOGLE_COMPLETE_TOKEN_MAX_AGE_SECONDS),
                )
            )
            session.commit()
            print("[Google CB] session created, redirecting to /auth/complete/...")

        complete_url = f"{_frontend_base_url(request).rstrip('/')}/auth/complete/{auth_token}"
        print(f"[Google CB] redirect to: {complete_url[:60]}...")
        return RedirectResponse(url=complete_url, status_code=302)

    except Exception as e:
        print(f"[Google CB] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(url=f"{_frontend_base_url(request)}{auth_routes.LOGIN_ROUTE}?oauth_error=1", status_code=302)
    

api.add_route("/auth/google/start", google_start, methods=["GET"])
api.add_route("/auth/google/callback", google_callback, methods=["GET"])

try:
    rx.Model.create_all()
except Exception as e:
    print(f"ERROR create_all: {e}")


def _ensure_usermemory_columns() -> None:
    try:
        with rx.session() as session:
            conn = session.connection()
            if conn.dialect.name != "sqlite":
                return
            cols = {str(row[1]) for row in conn.exec_driver_sql("PRAGMA table_info('usermemory')").fetchall()}
            if "selected_semester" not in cols:
                conn.exec_driver_sql("ALTER TABLE usermemory ADD COLUMN selected_semester VARCHAR NOT NULL DEFAULT ''")
            session.commit()
    except Exception as e:
        print(f"ERROR ensure_usermemory_columns: {e}")
_ensure_usermemory_columns()


async def _payhere_notify_wrapper(request):
    return await payhere_notify(request)


api.add_route("/api/payhere/notify", _payhere_notify_wrapper, methods=["POST"])
api.add_route("/health", health_check, methods=["GET"])


app.add_page(custom_login_page, route=auth_routes.LOGIN_ROUTE, title="Login", image=FAVICON_32)
app.add_page(custom_register_page, route=auth_routes.REGISTER_ROUTE, title="Register", image=FAVICON_32)
app.add_page(reset_password_page, route="/reset-password", title="Reset Password", image=FAVICON_32)
