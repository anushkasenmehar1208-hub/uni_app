from dotenv import load_dotenv
load_dotenv()

import os
import threading
import hashlib
import asyncio
import json
import base64
import re
import secrets
from urllib.parse import urlencode, urlparse
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


def friendly_groq_error(e: Exception) -> str:
    s = str(e)
    if _is_rate_limit_text(s) or " 429" in s.lower():
        return RATE_LIMIT_UI_MESSAGE
    return GENERIC_ERROR_UI_MESSAGE


def _groq_generate(model: str, contents: str) -> Any:
    """Drop-in replacement for Gemini generate_content using Groq."""
    class _R:
        text = ""

    if client is None:
        _R.text = "API not ready"
        return _R()

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": contents}],
            max_tokens=2048,
        )
        _R.text = resp.choices[0].message.content or ""
        return _R()
    except Exception as e:
        _R.text = friendly_groq_error(e)
        return _R()

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
            if isinstance(item, str):
                if _is_rate_limit_text(item):
                    yield RATE_LIMIT_UI_MESSAGE
                    break

            yield item

    except Exception as e:
        yield friendly_groq_error(e)

FREE_DAILY_LIMIT = 5
TRIAL_DAYS       = 3
ADAPTIVE_PROFILE_SCOPE = "__adaptive_profile__"
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{3,32}$")
PASSWORD_MIN_LEN = 8
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
            "ts": datetime.utcnow().isoformat() + "Z",
            "uid": anon_uid,
            "scope": (scope or "home")[:64],
            "user": _redact_training_text(user_text)[:1200],
            "assistant": _redact_training_text(assistant_text)[:2800],
        }
        with TRAINING_DATA_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")
    except Exception as e:
        print(f"ERROR training log append: {e}")

# ----------------------------
# PayHere configuration
# ----------------------------
PAYHERE_MERCHANT_ID     = os.getenv("PAYHERE_MERCHANT_ID", "").strip()
PAYHERE_MERCHANT_SECRET = os.getenv("PAYHERE_MERCHANT_SECRET", "").strip()
PAYHERE_SANDBOX         = os.getenv("PAYHERE_SANDBOX", "true").lower() == "true"
APP_BASE_URL            = os.getenv("APP_BASE_URL", "http://localhost:3001").rstrip("/")
API_BASE_URL            = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
GOOGLE_CLIENT_ID        = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET    = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_REDIRECT_URI     = os.getenv("GOOGLE_REDIRECT_URI", "").strip()
GOOGLE_OAUTH_ENABLED    = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
GOOGLE_START_URL        = f"{API_BASE_URL}/auth/google/start"
AUTH_SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 90
GOOGLE_COMPLETE_TOKEN_MAX_AGE_SECONDS = max(
    60, int(os.getenv("GOOGLE_COMPLETE_TOKEN_MAX_AGE_SECONDS", "600"))
)
SESSION_SECRET          = os.getenv("SESSION_SECRET", "change-me-in-production").strip() or "change-me-in-production"
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
    return expected == md5sig.upper()


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
            "SENG:computer architecture and operating systems",
            "SENG:Software Construction",
            "SENG:Requirement Engineering",
            "SENG:Software Modeling",
            "SENG:Web Application Development",
            "SENG:interactive application development",
            "SENG:Management for Software Engineering II"
        ],
        "Semester 4": [
            "SENG:Computer Networks",
            "SENG:Software Architecture and Design",
            "SENG:Human-Computer Interaction",
            "SENG:Software Verification and Validation",
            "SENG:Mobile Application Development",
            "SENG:embedded systems development",
            "PMAT:mathematical methods",
        ],
    },
}


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
    view_mode: str = "home"
    active_scope: str = "home"

    status_text: str = ""

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

    @rx.var(cache=False)
    def is_authenticated_now(self) -> bool:
        return self._uid() >= 0

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
            from datetime import timezone
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
            return FREE_DAILY_LIMIT
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

    def _check_and_reset_daily_count(self, uid: int) -> None:
        today_str = date.today().isoformat()
        if self.last_message_date != today_str:
            self.daily_message_count = 0
            self.last_message_date   = today_str
            with rx.session() as session:
                profile = session.exec(
                    select(UserProfile).where(UserProfile.user_id == uid)
                ).one_or_none()
                if profile:
                    profile.daily_message_count = 0
                    profile.last_message_date   = date.today()
                    session.add(profile)
                    session.commit()

    def _increment_daily_count(self, uid: int) -> None:
        self.daily_message_count += 1
        today = date.today()
        self.last_message_date = today.isoformat()
        with rx.session() as session:
            profile = session.exec(
                select(UserProfile).where(UserProfile.user_id == uid)
            ).one_or_none()
            if profile:
                profile.daily_message_count = self.daily_message_count
                profile.last_message_date   = today
                session.add(profile)
                session.commit()

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
        return bool(token) and token == (self.auth_csrf_token or "")

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
            return rx.redirect(self.post_login_redirect or "/")

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
        self.app_auth_token = self.auth_token
        self.login_error = ""
        self.auth_csrf_token = secrets.token_urlsafe(24)
        return AppState.auth_redir()  # type: ignore
    
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
                        LocalAuthSession.expiration >= datetime.utcnow()
                    )
                ).one_or_none()
                if auth_sess and auth_sess.user_id is not None:
                    resolved_uid = int(auth_sess.user_id)
                    # One-time use token: consume it immediately to prevent replay.
                    db.delete(auth_sess)
                    db.commit()
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
        self.app_auth_token = self.auth_token
        new_token = self.auth_token
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
            ts         = int(datetime.utcnow().timestamp() * 1000)
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

            first_name = (self.name or "Student").split()[0]
            last_name  = " ".join((self.name or "Student").split()[1:]) or "User"

            return_url = f"{APP_BASE_URL}/payment/success"
            cancel_url = f"{APP_BASE_URL}/payment/cancel"
            notify_url = f"{APP_BASE_URL}/api/payhere/notify"

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

    def set_name(self, value: str):
        self.name = value
        uid = self._uid()
        self._save_memory(uid)

    @rx.var
    def available_semesters(self) -> list[str]:
        if not self.selected_year:
            return []
        mapping = {
            "Year 1": ["Semester 1", "Semester 2"],
            "Year 2": ["Semester 3", "Semester 4"],
            "Year 3": ["Semester 5", "Semester 6"],
        }
        return mapping.get(self.selected_year, [])

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
        y = year.lower().replace("year", "").strip()
        s = semester.lower().replace("semester", "").strip()
        if y.isdigit() and s.isdigit():
            return f"y{y}s{s}"
        return f"{year}|{semester}"

    def _current_courses_for_scope(self) -> list[str]:
        if self.view_mode != "semester" or not self.selected_year or not self.selected_semester:
            return []
        return FULL_CURRICULUM.get(self.selected_year, {}).get(self.selected_semester, [])

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

    def _load_messages(self, uid: int) -> None:
        if not self.current_session_id:
            self.chat_history = []
            return
        sid = int(self.current_session_id)
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

    def _save_message(self, uid: int, role: str, content: str) -> None:
        if uid < 0 or not self.current_session_id:
            return
        safe_content = sanitize_for_ui(content) if role == "assistant" else content
        with rx.session() as session:
            session.add(ChatMessage2(user_id=uid, session_id=int(self.current_session_id), role=role, content=safe_content))
            session.commit()

    def _save_memory(self, uid: int) -> None:
        if uid < 0:
            return
        with rx.session() as session:
            mem = session.exec(select(UserMemory).where(UserMemory.user_id == uid)).one_or_none()
            if mem is None:
                mem = UserMemory(user_id=uid)  # type: ignore
            mem.step = self.step; mem.name = self.name; mem.degree = self.degree
            mem.is_started = self.is_started; mem.selected_year = self.selected_year
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
        try: return json.loads(text)
        except Exception: pass
        try:
            a, b = text.find("["), text.rfind("]")
            if a != -1 and b != -1 and b > a: return json.loads(text[a:b+1])
        except Exception: pass
        return []
        # ----------------------------
    # memory tuning
    # ----------------------------
    SCOPE_SUMMARY_TRIGGER_NEW_MSGS = 12
    GLOBAL_MEMORY_TRIGGER_NEW_MSGS = 24
    ADAPTIVE_PROFILE_TRIGGER_NEW_MSGS = 8
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

        sids = self._scope_session_ids(uid, scope)
        if not sids:
            return ""

        conds = [func.lower(ChatMessage2.content).like(f"%{k}%") for k in kws]

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

        prompt = f"""Build an adaptive tutoring profile from this chat history.
Return ONLY short bullet points (max 10 bullets) under these labels:
- Preferred explanation depth
- Preferred format (bullets/examples/steps)
- Pace and tone
- Topics user struggles with
- Topics user handles well
- Common confusion triggers
- Best response patterns for this user

Current profile:
{current}

Recent conversation:
{recent_text}
"""

        try:
            resp = await asyncio.to_thread(_groq_generate, GEMINI_FAST_MODEL, prompt)
            new_profile = (getattr(resp, "text", "") or "").strip()
            if new_profile:
                self._set_adaptive_profile(uid, new_profile)
        except Exception as e:
            print(f"ERROR auto adaptive profile: {e}")

    def _switch_scope(self, uid: int, scope: str) -> None:
        self.active_scope = scope
        self.current_session_id = ""; self.current_session_choice = ""
        self._ensure_scope_memory(uid, scope)
        self._ensure_session(uid, scope)
        self._load_sessions(uid, scope)
        self._load_messages(uid)

    def _get_study_plan(self, uid: int, scope: str) -> list:
        if uid < 0: return []
        with rx.session() as session:
            row = session.exec(select(SemesterStudyPlan).where(SemesterStudyPlan.user_id == uid).where(SemesterStudyPlan.scope == scope)).one_or_none()
        if row is None or not row.plan_json: return []
        try: return json.loads(row.plan_json)
        except Exception: return []

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

    @rx.event
    async def on_load(self):
        if self._uid() < 0:
            yield AppState.auth_redir
            return
        uid = self._uid()
        if uid < 0:
            yield AppState.auth_redir
            return

        with rx.session() as session:
            mem = session.exec(select(UserMemory).where(UserMemory.user_id == uid)).one_or_none()
            if mem is None:
                mem = UserMemory(user_id=uid)  # type: ignore
                session.add(mem); session.commit(); session.refresh(mem)
            self.step = mem.step or 0; self.name = mem.name or ""; self.degree = mem.degree or ""
            self.is_started = bool(mem.is_started); self.selected_year = mem.selected_year or ""
            self.memory_summary = mem.summary or ""

        self._load_profile(uid)
        self.adaptive_profile = self._get_adaptive_profile(uid)
        self._migrate_legacy_messages_once(uid)
        self.view_mode = "home"; self.selected_semester = ""
        self._switch_scope(uid, "home")
        if self.selected_year:
            self._ensure_progress_for_year(uid, self.selected_year)
        self._refresh_today_plan(uid)
        self.status_text = ""
        yield rx.call_script(SCROLL_TO_BOTTOM_JS)

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
            self.step = min(self.step + 1, 3)
            self._save_memory(uid)
        except Exception as e:
            print(f"ERROR next_step: {e}")

    @rx.event
    def set_degree(self, value: str):
        uid = self._uid()
        try:
            self.degree = value
            self._save_memory(uid)
        except Exception as e:
            print(f"ERROR set_degree: {e}")

    @rx.event
    def start_app(self):
        uid = self._uid()
        try:
            self.is_started = True
            self._save_memory(uid)
        except Exception as e:
            print(f"ERROR start_app: {e}")

    @rx.event
    def back_to_years(self):
        uid = self._uid()
        try:
            self.selected_year = ""; self.selected_semester = ""; self.status_text = ""
            self._save_memory(uid); self._refresh_today_plan(uid)
        except Exception as e:
            print(f"ERROR back_to_years: {e}")

    @rx.event
    def set_year(self, year: str):
        uid = self._uid()
        try:
            if year == "Year 4":
                msg = "we are still working on that"
                self.status_text = msg
                return
            self.status_text = ""; self.selected_year = year; self.selected_semester = ""
            self._save_memory(uid)
            self._ensure_progress_for_year(uid, year)
            self._refresh_today_plan(uid)
        except Exception as e:
            print(f"ERROR set_year: {e}")

    @rx.event
    async def open_semester(self, semester: str):
        uid = self._uid()
        if uid < 0 or not self.selected_year: return
        try:
            self.selected_semester = semester; self.view_mode = "semester"
            scope = self._scope_key(self.selected_year, semester)
            self._switch_scope(uid, scope)
            existing_plan = self._get_study_plan(uid, scope)
            if existing_plan:
                day, topic_idx = self._get_day_progress(uid, scope)
                self.current_day = day; self.current_topic_index = topic_idx
                today_msg = self._build_today_message(existing_plan, day, topic_idx)
                # Avoid duplicating this auto message each time user re-opens the semester.
                if not self.chat_history:
                    self.chat_history.append({"role":"assistant","content":today_msg})
                    self._save_message(uid,"assistant",today_msg)
            else:
                self.is_generating_plan = True
                gen_msg = "AI is generating your personalized 110 day study plan please wait"
                self.chat_history.append({"role":"assistant","content":gen_msg})
                self._save_message(uid,"assistant",gen_msg)
                yield
                yield type(self).generate_study_plan
        except Exception as e:
            print(f"ERROR open_semester: {e}")

    @rx.event
    async def generate_study_plan(self):
        uid = self._uid()
        if uid < 0 or client is None:
            self.is_generating_plan = False; return
        scope = self.active_scope
        courses_text = "\n".join(self._current_courses_for_scope())
        try:
            prompt = f"""You are a university curriculum expert for {self.degree} students
Generate a realistic detailed 110 day study plan for the following semester subjects
Return ONLY a valid JSON array with exactly 110 items
Each item: {{"day":<1-110>,"subject":"<name>","unit":"<unit>","topics":["<t1>","<t2>"]}}
Subjects:\n{courses_text}"""
            resp = await asyncio.to_thread(_groq_generate, GEMINI_FAST_MODEL, prompt)
            plan = self._extract_json_list((getattr(resp,"text","") or "").strip())
            if not plan or len(plan) < 10:
                self.chat_history.append({"role":"assistant","content":"Could not generate study plan please try reopening the semester"})
                self.is_generating_plan = False; return
            self._save_study_plan(uid, scope, plan)
            self._save_day_progress(uid, scope, 1, 0)
            self.current_day = 1; self.current_topic_index = 0
            msg = "Your personalized 110 day study plan is ready\n\n" + self._build_today_message(plan, 1, 0)
            self.chat_history.append({"role":"assistant","content":msg})
            self._save_message(uid,"assistant",msg)
        except Exception as e:
            print(f"ERROR generate_study_plan: {e}")
            self.chat_history.append({"role":"assistant","content":"Something went wrong generating the plan"})
        self.is_generating_plan = False
        yield rx.call_script(SCROLL_TO_BOTTOM_JS)

    @rx.event
    def go_home(self):
        uid = self._uid()
        if uid < 0: return
        try:
            self.view_mode = "home"; self.selected_semester = ""
            self._switch_scope(uid, "home")
        except Exception as e:
            print(f"ERROR go_home: {e}")

    @rx.event
    async def send_message(self):
        uid = self._uid()
        if uid < 0 or not self.chat_input.strip():
            return

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

                scope_summary = self._get_scope_summary(uid, scope)
                recent_text = "\n".join([f'{m["role"]}: {m["content"]}' for m in self.chat_history[-14:]])
                past_hits = self._past_hits_text(uid, scope, user_msg)

                teach_prompt = f"""You are Alex, a friendly and patient university tutor helping a {self.degree} student.

Current context:
- Day {day}/110 | Subject: {entry.get("subject","")} | Unit: {entry.get("unit","")} | Topic: {current_topic}
- Student memory: {scope_summary}
- Adaptive profile from previous chats: {adaptive_profile}
- Recent conversation: {recent_text}
- Past relevant chat (db search): {past_hits}
- Student just said: {user_msg}

Your response style rules:
1. Talk like a helpful senior student, not a textbook — keep it warm and casual
2. Explain the concept simply first (1-2 sentences), THEN go deeper
3. Use a real-world example or analogy the student can relate to
4. Give ONE small practice question at the end (not overwhelming)
5. Keep responses focused — don't dump everything at once
6. If the student seems confused, slow down and break it into smaller steps
7. Use simple formatting: short paragraphs, avoid walls of text
8. Encourage the student naturally — but don't be overly cheesy about it
9. Keep responses SHORT — max 150-200 words per reply
10. Use bullet points as much as possible instead of long paragraphs
11. Never write walls of text — students lose focus fast
12. Use emojis sparingly but effectively — one per section max (📌 for key point, ✅ for answer, 💡 for tip)
13. When explaining a concept, always follow this structure:
    - What it is (1 sentence)
    - Why it matters (1 sentence)
    - Simple example
    - Quick practice
14. Never start a response with "Great question!" or "Certainly!" — just answer directly
15. If the student makes a mistake, correct gently — say "Almost! Try thinking of it this way..."
16. Always refer to the student by name: {self.name}
17. Acknowledge progress occasionally — remind {self.name} they are on Day {day}/110 and how far they've come
18. If {self.name} says words like 'confused', 'don't understand', 'what?', 'huh' — immediately simplify and use an analogy
19. Adapt to the adaptive profile above for pace, explanation depth, and examples."""

                assistant_index = len(self.chat_history)
                self.chat_history.append({"role": "assistant", "content": ""})
                yield
                yield rx.call_script(SCROLL_TO_BOTTOM_JS)

                buf = ""
                last_scroll = 0
                final_text = ""
                groq_messages = [{"role": "user", "content": teach_prompt}]

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
        rules = "You are the HOME assistant\n" if self.active_scope == "home" else f"You are a SEMESTER assistant for scope {self.active_scope}\n"
        past_hits = self._past_hits_text(uid, self.active_scope, user_msg)

        prompt = f"""You are Alex, a friendly AI study companion inside a university planner app for a {self.degree} student.

Student profile:
- Degree: {self.degree} | Year: {self.selected_year} | Semester: {self.selected_semester}
- Memory: {self.memory_summary}
- Adaptive profile from previous chats: {adaptive_profile}
- Scope summary: {scope_summary}
- All scopes: {all_scopes}
- Today's plan: {self.today_plan}
- Upcoming courses: {chr(10).join(next_courses)}
- Recent chat: {recent_text}
- Past relevant chat (db search): {past_hits}

{rules}

Your response style rules:
1. Be warm and conversational — like a smart friend who knows their stuff
2. Give clear, direct answers first — no long intros or filler
3. Break complex things into digestible steps with simple language
4. Use relatable real-world examples when explaining concepts
5. End with ONE short check-in question to keep the student engaged
6. If the student is just chatting, be natural and friendly
7. Keep responses concise — quality over quantity
8. Gently guide the student back to their studies if they go off track
9. Keep responses SHORT — max 150-200 words per reply
10. Use bullet points as much as possible instead of long paragraphs
11. Never write walls of text — students lose focus fast
12. Use emojis sparingly but effectively — one per section max (📌 for key point, ✅ for answer, 💡 for tip)
13. When explaining a concept, always follow this structure:
    - What it is (1 sentence)
    - Why it matters (1 sentence)
    - Simple example
    - Quick practice
14. Never start a response with "Great question!" or "Certainly!" — just answer directly
15. If the student makes a mistake, correct gently — say "Almost! Try thinking of it this way..."
16. Always refer to the student by name: {self.name}
17. If {self.name} says words like 'confused', 'don't understand', 'what?', 'huh' — immediately simplify and use an analogy
18. Adapt to the adaptive profile above for pace, explanation depth, and examples."""

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
                [{"role": "user", "content": prompt}],  # or prompt for home mode
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
        return [reflex_local_auth.LocalAuthState.do_logout, rx.redirect(reflex_local_auth.routes.LOGIN_ROUTE)]


# ============================
# UI helpers
# ============================
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

    if (box) {
      box.scrollTop = box.scrollHeight;
    }
    if (a) {
      try { a.scrollIntoView({ block: "end" }); } catch(e) {}
    }

    if (box) {
      const h = box.scrollHeight;
      if (h === lastH) stable += 1;
      else { stable = 0; lastH = h; }

      const atBottom = Math.abs((box.scrollHeight - box.clientHeight) - box.scrollTop) < 6;

      // stop only when height is stable and we are really at bottom
      if (stable >= 6 && atBottom) return;
    }

    tries += 1;
    if (tries < 180) {
      requestAnimationFrame(tick);
    }
  }

  tick();
})();
"""
AUTO_SCROLL_OBSERVER_JS = """
(function(){
  function attach(){
    const box = document.getElementById("chat_scroll");
    if(!box) return false;
    if(box.__autoScrollAttached) return true;
    box.__autoScrollAttached = true;

    const atBottom = () => (box.scrollHeight - box.scrollTop - box.clientHeight) < 80;
    let userLocked = false;

    const scrollNow = () => {
      if(userLocked) return;
      box.scrollTop = box.scrollHeight;
    };

    box.addEventListener("scroll", () => {
      userLocked = !atBottom();
    });

    const obs = new MutationObserver(() => {
      requestAnimationFrame(scrollNow);
      setTimeout(scrollNow, 0);
      setTimeout(scrollNow, 80);
      setTimeout(scrollNow, 250);
      setTimeout(scrollNow, 600);
    });

    obs.observe(box, { childList: true, subtree: true });

    scrollNow();
    return true;
  }

  let tries = 0;
  const iv = setInterval(() => {
    tries += 1;
    if(attach() || tries > 200) clearInterval(iv);
  }, 50);
})();
"""
ENTER_TO_SEND_JS = """
(function(){
  function attach(){
    var ta = document.getElementById("chat_input");
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
def subject_button(label: str, on_click=None):
    return rx.button(label, width="100%", height="60px", variant="outline", color_scheme="green", on_click=on_click,
        style={"border":"1px solid #00ff88","box-shadow":"0 0 10px rgba(0,255,136,0.2)","text_transform":"uppercase","font_weight":"bold","letter_spacing":"1px","transition":"all 0.3s ease",
               "_hover":{"box_shadow":"0 0 25px rgba(0,255,136,0.6)","transform":"translateX(10px)","background":"rgba(0,255,136,0.1)"}})

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
    window.location.replace("/");
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
                        rx.text("LKR 200.00", font_size="2.1rem", font_weight="800", color="white"),
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
                                rx.cond(
                                    AppState.payment_processing,
                                    rx.hstack(rx.spinner(size="1", color="white"), rx.text("Redirecting..."), spacing="2"),
                                    rx.text("Continue to Secure Checkout"),
                                ),
                                on_click=AppState.initiate_payment(1),
                                width="100%",
                                height="52px",
                                border_radius="12px",
                                is_disabled=AppState.payment_processing,
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
                            "Secure checkout via PayHere",
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
                rx.text("Unlock Unlimited Access", font_weight="800", font_size="1rem", color="white",
                        style={"text_shadow": "0 1px 4px rgba(0,0,0,0.6)"}),
                rx.spacer(),
                rx.text("→", color="white", font_size="1.4rem", font_weight="bold"),
                align="center", spacing="3", width="100%",
            ),
            on_click=AppState.open_pricing_modal,
            width="100%", height="68px", border_radius="16px",
            style={
                "background": "linear-gradient(135deg, #0d0d0d 0%, #252525 50%, #1a1a1a 100%)",
                "border": "none", "cursor": "pointer",
                "box_shadow": "0 4px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06)",
                "transition": "all 0.25s ease", "padding": "0 24px",
                "_hover": {"box_shadow": "0 6px 32px rgba(255,255,255,0.1)", "transform": "translateY(-2px)", "filter": "brightness(1.2)"},
                "_active": {"transform": "translateY(0)"},
            },
        ),
        rx.text("🔒 You've reached your 5 free messages for today. Resets at midnight.",
                color="rgba(255,255,255,0.35)", font_size="0.7rem", text_align="center", margin_top="8px"),
        width="100%", max_width="860px", margin_x="auto", padding="1em",
    )


def chat_input_field() -> rx.Component:
    return rx.hstack(
        rx.text_area(
            id="chat_input",
            placeholder="Ask Alex AI anything...",
            value=AppState.chat_input,
            on_change=AppState.set_chat_input,
            background="rgba(30,30,35,0.85)",
            border="1px solid rgba(0,255,136,0.25)",
            color="white",
            flex="1",
            min_height="52px",
            max_height="140px",
            resize="none",
            border_radius="14px",
            padding="14px 16px",
            font_size="0.95rem",
            style={
                "_placeholder": {"color": "rgba(255,255,255,0.3)"},
                "_focus": {"border_color": "rgba(0,255,136,0.55)", "box_shadow": "0 0 0 2px rgba(0,255,136,0.12)", "outline": "none"},
            },
        ),
        rx.button(
            rx.cond(AppState.is_processing, rx.spinner(size="1", color="white"), rx.icon(tag="arrow_up", color="white", size=18)),
            id="chat_send_btn",
            on_click=AppState.send_message,
            is_disabled=AppState.is_processing,
            border_radius="12px", width="52px", height="52px",
            style={
                "background": rx.cond(AppState.is_processing, "rgba(0,255,136,0.3)", "rgba(0,255,136,0.85)"),
                "border": "none", "cursor": "pointer", "transition": "all 0.2s ease", "flex_shrink": "0",
                "_hover": {"background": "#00ff88", "box_shadow": "0 0 16px rgba(0,255,136,0.5)"},
            },
        ),
        rx.script(ENTER_TO_SEND_JS),
        align="end", spacing="2", width="100%",
    )

# ──────────────────────────────────────────────────────────────
# NEW: Empty chat state — centered like ChatGPT home
# ──────────────────────────────────────────────────────────────
def empty_chat_panel() -> rx.Component:
    return rx.box(
        # Centered content
        rx.vstack(
            rx.spacer(),
            # Logo / icon
            rx.image(
                src="/a_logo.png",
                width="120px",
                height="120px",
                object_fit="contain",
                style={
                    "filter": "drop-shadow(0 0 20px rgba(255,215,0,0.4)) drop-shadow(0 0 40px rgba(0,255,136,0.15))",
                    "opacity": "0.92",
                },
            ),
            rx.text(
                "What do you want to learn today?",
                color="rgba(255,255,255,0.55)",
                font_size="1.05rem",
                font_weight="400",
                letter_spacing="0.3px",
            ),
            rx.spacer(),
            # Input bar pushed down
            rx.box(
                rx.cond(
                    AppState.can_send_message,
                    rx.box(
                        chat_input_field(),
                        width="100%",
                    ),
                    upgrade_button(),
                ),
                width="100%", max_width="680px",
            ),
            # Tier bar below input
            tier_status_bar(),
            rx.spacer(height="16em"),
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
        background="transparent",
        padding="2em",
    )


# ──────────────────────────────────────────────────────────────
# Active chat state — messages + input at bottom
# ──────────────────────────────────────────────────────────────
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
            # User message — right aligned, subtle pill
                            rx.box(
                                rx.text(
                                    msg["content"],
                                    color="white",
                                    font_size="0.95rem",
                                ),
                                background="rgba(255,255,255,0.08)",
                                border_radius="18px 18px 4px 18px",
                                padding="10px 16px",
                                max_width="70%",
                                margin_left="auto",
                                margin_right="0",
                            ),
            # Assistant message — left aligned, plain no box
                            rx.box(
                                rx.markdown(msg["content"]),
                                color="rgba(255,255,255,0.95)",
                                font_size="0.95rem",
                                max_width="85%",
                                margin_left="0",
                            ),
                        ),
                        width="100%",
                        margin_bottom="16px",
                        display="flex",
                        flex_direction="column",
                    ),
                ),
                rx.cond(
                    AppState.is_processing,
                    rx.html("""
                        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                            <div style="width:24px;height:24px;position:relative;flex-shrink:0;">
                                <style>
                                    @keyframes alexorbit {
                                        from { transform: rotate(0deg) translateX(10px); }
                                        to   { transform: rotate(360deg) translateX(10px); }
                                    }
                                </style>
                                <div style="
                                    width:4px;height:4px;
                                    background:#FFD700;
                                    border-radius:50%;
                                    position:absolute;
                                    top:50%;left:50%;
                                    margin-top:-2px;margin-left:-2px;
                                    animation:alexorbit 0.3s linear infinite;
                                    box-shadow:0 0 4px rgba(255,215,0,0.9);
                                "></div>
                            </div>
                            <span style="color:rgba(255,255,255,0.35);font-size:0.82rem;font-weight:300;letter-spacing:0.5px;">Alex is thinking...</span>
                        </div>
                    """),
                ),
                rx.box(id="chat_bottom_anchor", height="1px"),
                width="100%", max_width="760px", margin_x="auto",padding_x="2em", padding_bottom="1em",
            ),
            id="chat_scroll",
            flex="1", min_height="0", overflow_y="auto", padding="1em", width="100%",
        ),
        rx.script(AUTO_SCROLL_OBSERVER_JS),
        # Tier bar
        tier_status_bar(),
        # Input bar at bottom
        rx.cond(
            AppState.can_send_message,
            rx.box(
                chat_input_field(),
                width="100%", max_width="860px", margin_x="auto", padding="0 1em 1em 1em",
            ),
            upgrade_button(),
        ),
        pricing_modal(),
        width="100%", height="100%", display="flex", flex_direction="column",
        overflow="hidden", background="transparent", position="relative",
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
                rx.button("Go to App →", on_click=rx.redirect("/"), color_scheme="green", size="3",
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
                rx.button("Back to App", on_click=rx.redirect("/"), variant="outline", color_scheme="green", size="3"),
                spacing="5", align="center",
            ),
            height="100vh",
        ),
        background="radial-gradient(circle at center, #1a0000 0%, #050505 100%)", min_height="100vh",
    )


def legal_page_shell(title: str, subtitle: str, sections: list[tuple[str, str]]) -> rx.Component:
    return rx.box(
        rx.center(
            rx.vstack(
                rx.hstack(
                    rx.button("Back to App", on_click=rx.redirect("/"), variant="outline", color_scheme="green"),
                    width="100%",
                    align="center",
                ),
                rx.heading(title, size="8", color="white"),
                rx.text(subtitle, color="rgba(255,255,255,0.72)", text_align="left", width="100%"),
                *[
                    rx.box(
                        rx.heading(section_title, size="5", color="#00ff88"),
                        rx.text(section_text, color="rgba(255,255,255,0.78)", white_space="pre-wrap"),
                        padding="1.1em",
                        border_radius="12px",
                        border="1px solid rgba(0,255,136,0.22)",
                        background="rgba(3,12,10,0.6)",
                        width="100%",
                    )
                    for section_title, section_text in sections
                ],
                spacing="4",
                width="min(92vw, 940px)",
                padding="2em",
                align_items="stretch",
            ),
            width="100%",
        ),
        min_height="100vh",
        width="100%",
        background="radial-gradient(circle at top right,#003120 0%,#050505 62%)",
        padding_y="2em",
    )


@rx.page(route="/return-policy", title="Return Policy", image=FAVICON_32)
def return_policy_page():
    return legal_page_shell(
        "Return Policy",
        "Simple refund and cancellation information for Alex Studies subscriptions.",
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
                "Email support at support@alexstudies.com with:\n"
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
        "How we collect, use, and protect your data on Alex Studies.",
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
        "Basic usage terms for Alex Studies.",
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
                "Email: support@alexstudies.com\n"
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
    return rx.box(
        rx.center(
            rx.vstack(
                rx.cond(AppState.step == 0,
                    rx.box(rx.vstack(rx.heading("Shall we begin",size="8"),rx.button("YES",color_scheme="green",on_click=AppState.next_step,size="3",style={"animation":"pulse_glow 2s infinite","cursor":"pointer"})),
                        background_image="url('/bg_image.png')",background_size="cover",width="100vw",height="100vh",display="flex",align_items="center",justify_content="center")),
                rx.cond(AppState.step == 1,
                    rx.box(rx.vstack(rx.heading("Whats your degree",size="7"),rx.select(AppState.options,placeholder="Choose your degree",on_change=AppState.set_degree,width="100%"),rx.button("next",on_click=AppState.next_step,color_scheme="green",size="3")),
                        background_image="url('/bg_image.png')",background_size="cover",width="100vw",height="100vh",display="flex",align_items="center",justify_content="center")),
                rx.cond(AppState.step == 2,
                    rx.box(rx.vstack(rx.heading("What's your name?",size="7",color="white"),rx.input(placeholder="Enter your name",on_change=AppState.set_name,width="100%",size="3"),rx.button("Next",on_click=AppState.next_step,color_scheme="green",size="3"),spacing="4",width="400px"),
                        background_image="url('/bg_image.png')",background_size="cover",width="100vw",height="100vh",display="flex",align_items="center",justify_content="center")),
                rx.cond(AppState.step == 3,
                    rx.box(rx.vstack(rx.heading(rx.text("Lets crush "),rx.text(AppState.degree),size="7"),rx.button("begin",on_click=AppState.start_app,color_scheme="green",size="3",style={"animation":"pulse_glow 2s infinite"})),
                        background_image="url('/bg_image.png')",background_size="cover",width="100vw",height="100vh",display="flex",align_items="center",justify_content="center")),
                spacing="4",
            ),
        ),
        height="100vh",
    )


# ──────────────────────────────────────────────────────────────
# Sidebar plan widget
# ──────────────────────────────────────────────────────────────
def sidebar_plan_widget() -> rx.Component:
    return rx.vstack(
        rx.image(src="/a_logo.png", width="80px", height="80px", object_fit="contain", border_radius="12px", opacity="0.85", margin_x="auto"),
        rx.cond(
            AppState.has_premium_access,
            rx.box(
                rx.vstack(
                    rx.text("⚡ Premium", font_weight="800", font_size="0.95rem", color="white", text_align="center"),
                    rx.text("Unlimited messages active", color="rgba(255,255,255,0.45)", font_size="0.72rem", text_align="center"),
                    spacing="1", align_items="center", width="100%",
                ),
                on_click=AppState.open_pricing_modal, width="100%", padding="12px 16px", border_radius="14px", cursor="pointer",
                style={"background":"linear-gradient(135deg,#b45309,#f59e0b)","box_shadow":"0 0 20px rgba(245,158,11,0.35)","transition":"all 0.2s ease","_hover":{"filter":"brightness(1.1)","transform":"translateY(-1px)"}},
            ),
            rx.cond(
                AppState.is_in_trial,
                rx.box(
                    rx.vstack(
                        rx.text("⚡ Premium Trial", font_weight="800", font_size="0.95rem", color="white", text_align="center", style={"text_shadow":"0 1px 4px rgba(0,0,0,0.6)"}),
                        rx.text("Day access left: " + AppState.trial_days_left.to_string(), color="rgba(255,255,255,0.55)", font_size="0.72rem", text_align="center"),
                        spacing="1", align_items="center", width="100%",
                    ),
                    on_click=AppState.open_pricing_modal, width="100%", padding="12px 16px", border_radius="14px", cursor="pointer",
                    style={"background":"linear-gradient(135deg,#111111 0%,#2a2a2a 50%,#1a1a1a 100%)","transition":"all 0.2s ease","_hover":{"filter":"brightness(1.2)","transform":"translateY(-1px)"}},
                ),
                rx.vstack(
                    rx.button(
                        rx.text("Upgrade to Premium", font_weight="700", font_size="0.88rem", color="white", style={"text_shadow":"0 1px 4px rgba(0,0,0,0.6)"}),
                        on_click=AppState.open_pricing_modal, width="100%", height="52px", border_radius="14px",
                        style={
                            "background":"linear-gradient(135deg,#0d0d0d 0%,#252525 50%,#1a1a1a 100%)","border":"none","cursor":"pointer",
                            "box_shadow":"0 4px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06)","transition":"all 0.25s ease",
                            "_hover":{"box_shadow":"0 6px 28px rgba(255,255,255,0.1)","transform":"translateY(-2px)","filter":"brightness(1.2)"},
                            "_active":{"transform":"translateY(0)"},
                        },
                    ),
                    rx.text("Unlock unlimited access", color="rgba(255,255,255,0.3)", font_size="0.68rem", text_align="center"),
                    spacing="2", align_items="center", width="100%",
                ),
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
def home_page():
    return rx.box(
        # header
        rx.box(
            rx.hstack(
                rx.heading(rx.text("Hi ", color="white"), rx.text(AppState.name, color="white")),
                rx.text(
                    f"Lets study {AppState.degree}",
                    color="rgba(0,255,136,0.7)",
                    font_size="0.85rem",
                    font_weight="bold",
                    letter_spacing="1px",
                ),
                align_items="flex-start",
                flex_direction="column",
            ),
            rx.box(
                rx.text(
                    "Alex AI",
                    color="#FFD700",
                    font_size="3.5rem",
                    font_weight="bold",
                    letter_spacing="4px",
                    text_shadow="0 0 20px rgba(255,215,0,0.4)",
                ),
                position="absolute",
                left="50%",
                transform="translateX(-50%)",
            ),
            rx.hstack(
                rx.button("New chat", on_click=AppState.new_chat, variant="outline", color_scheme="green"),
                settings_menu_button(),
                spacing="2",
                margin_left="auto",
            ),
            position="relative",
            display="flex",
            align_items="center",
            width="100%",
            padding="2em",
            flex_shrink="0",
        ),

        # main area fills remaining height
        rx.flex(
            rx.vstack(
                rx.text("ACADEMIC YEAR", color="gray", font_size="0.8em", letter_spacing="2px"),
                rx.cond(AppState.status_text != "", rx.callout(AppState.status_text, icon="info", color_scheme="yellow", width="100%")),
                rx.cond(
                    AppState.selected_year == "",
                    rx.vstack(
                        subject_button("FIRST YEAR", on_click=AppState.set_year("Year 1")),
                        subject_button("SECOND YEAR", on_click=AppState.set_year("Year 2")),
                        subject_button("THIRD YEAR", on_click=AppState.set_year("Year 3")),
                        subject_button("FOURTH YEAR", on_click=AppState.set_year("Year 4")),
                        spacing="3",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.button("Back", on_click=AppState.back_to_years, variant="outline", color_scheme="green", width="100%"),
                        rx.text(AppState.selected_year, color="white", font_weight="bold"),
                        rx.foreach(AppState.available_semesters, lambda sem: subject_button(sem.upper(), on_click=AppState.open_semester(sem))),
                        spacing="3",
                        width="100%",
                    ),
                ),
                sidebar_plan_widget(),
                rx.box(
                    rx.text("CHATS", color="gray", font_size="0.8em", letter_spacing="2px"),
                    rx.vstack(
                        rx.foreach(AppState.sessions, lambda s: rx.hstack(
                            rx.button(
                                s["title"],
                                on_click=AppState.switch_chat(s["id"]),
                                variant="ghost",
                                color=rx.cond(AppState.current_session_id == s["id"], "#00ff88", "white"),
                                font_weight=rx.cond(AppState.current_session_id == s["id"], "bold", "normal"),
                                text_align="left",
                                justify_content="flex-start",
                                flex="1",
                                overflow="hidden",
                                text_overflow="ellipsis",
                                white_space="nowrap",
                                size="1",
                            ),
                            rx.icon_button(
                                rx.icon(tag="trash_2", size=12),
                                on_click=AppState.delete_session(s["id"]),
                                variant="ghost",
                                color_scheme="red",
                                size="1",
                                style={"opacity": "0.5", "_hover": {"opacity": "1"}},
                            ),
                            width="100%",
                            align="center",
                            spacing="1",
                        )),
                        width="100%",
                        spacing="1",
                        align_items="stretch",
                        max_height="200px",
                        overflow_y="auto",
                    ),
                    width="100%",
                    padding_top="1em",
                ),
                spacing="4",
                width="30%",
                padding="2em",
                align_items="flex-start",
                height="100%",
                min_height="0",
                overflow="hidden",
            ),

            rx.vstack(
                chat_panel(),
                width="65%",
                height="100%",
                min_height="0",
                overflow="hidden",
            ),

            width="100%",
            flex="1",
            min_height="0",
            align_items="stretch",
            overflow="hidden",
        ),

        # lock page scroll
        height="100vh",
        overflow="hidden",
        display="flex",
        flex_direction="column",
        background="radial-gradient(circle at bottom right,#002d1a 0%,#050505 100%)",
    )

def semester_page():
    return rx.box(
        # Compact header — no banner image
        rx.hstack(
            rx.button("Back to home", on_click=AppState.go_home, variant="outline", color_scheme="green"),
            rx.heading(
                AppState.semester_short_label,
                size="6", color="white", font_family="monospace", letter_spacing="2px",
            ),
            rx.spacer(),
            rx.badge(
                rx.text("Day "), rx.text(AppState.current_day), rx.text("/110"),
                color_scheme="blue", variant="solid", size="2",
            ),
            settings_menu_button(),
            width="100%", padding="1em 2em", flex_shrink="0", align="center",
        ),
        rx.cond(
            AppState.is_generating_plan,
            rx.center(
                rx.vstack(
                    rx.spinner(size="3", color="green"),
                    rx.text("🧠 Generating your 110-day study plan...", color="#00ff88", font_size="1.2em"),
                    spacing="4",
                ),
                position="absolute",
                top="80px",
                left="0",
                right="0",
                z_index="10",
            ),
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
        background="radial-gradient(circle at bottom right,#002d1a 0%,#050505 100%)",
    )

def require_app_login(page: rx.app.ComponentCallable) -> rx.app.ComponentCallable:
    def protected_page():
        return rx.fragment(
            rx.cond(
                AppState.is_hydrated & AppState.is_authenticated_now,
                page(),
                rx.center(rx.text("Loading...", on_mount=AppState.auth_redir)),
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
    google_start_script = f"""
    (function() {{
        var host = (window.location.hostname || '').toLowerCase();
        var isLocal = host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0' || host.endsWith('.local');
        window.location.href = isLocal ? {json.dumps(GOOGLE_START_URL)} : '/auth/google/start';
    }})();
    """
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
            on_click=rx.call_script(google_start_script),
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
            rx.heading("Login into your Account", size="7"),
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
            rx.heading("Create an account", size="7"),
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
            rx.heading("Reset Password", size="7"),
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


def _auth_page_shell(content: rx.Component) -> rx.Component:
    return rx.box(
        rx.image(src="/bg_image.png", position="fixed", top="0", left="0", width="100vw", height="100vh", object_fit="cover", z_index="-1"),
        rx.center(
            rx.card(
                content,
                width=AUTH_CARD_WIDTH,
                padding="22px 14px",
                border="1px solid rgba(34,197,94,0.20)",
                border_radius="12px",
                background="linear-gradient(120deg,rgba(2,16,22,0.88),rgba(17,74,72,0.52))",
            ),
            height="100vh",
            z_index="1",
        ),
        password_eye_script(),
        auth_token_bootstrap_script(),
        width="100vw", height="100vh", position="relative", overflow="hidden",
        on_mount=AppState.init_auth_forms,
    )


def custom_login_page():
    return _auth_page_shell(secure_login_form())


def custom_register_page():
    return _auth_page_shell(secure_register_form())


def reset_password_page():
    return _auth_page_shell(secure_reset_form())


@rx.page(
    route="/",
    title="Alex Studies - AI-Powered University Degree Learning",
    description="Learn a full university degree with AI, day by day...",
    image=FAVICON_32,
    meta=[
        {"name": "keywords", "content": "AI university, online degree, AI learning"},
        {"name": "robots", "content": "index, follow"},
        {"property": "og:title", "content": "Alex Studies - AI-Powered University Degree Learning"},
        {"property": "og:url", "content": "https://alexstudies.com"},
        {"property": "og:type", "content": "website"},
    ],
    on_load=AppState.on_load
)
@require_app_login
def index():
    return rx.cond(
        AppState.is_started,
        rx.cond(AppState.view_mode == "home", home_page(), semester_page()),
        onboarding_page(),
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
    

# ✅ This actually registers the routes
api.add_route("/auth/google/start", google_start, methods=["GET"])
api.add_route("/auth/google/callback", google_callback, methods=["GET"])

try:
    rx.Model.create_all()
except Exception as e:
    print(f"ERROR create_all: {e}")


async def _payhere_notify_wrapper(request):
    return await payhere_notify(request)

api.add_route("/api/payhere/notify", _payhere_notify_wrapper, methods=["POST"])
api.add_route("/health", health_check, methods=["GET"])

app.add_page(custom_login_page, route=auth_routes.LOGIN_ROUTE, title="Login", image=FAVICON_32)
app.add_page(custom_register_page, route=auth_routes.REGISTER_ROUTE, title="Register", image=FAVICON_32)
app.add_page(reset_password_page, route="/reset-password", title="Reset Password", image=FAVICON_32)
