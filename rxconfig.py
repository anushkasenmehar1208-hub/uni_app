import reflex as rx
import os

def _resolve_public_url() -> str:
    return os.getenv("APP_BASE_URL", "https://alexstudies.com").rstrip("/")

def _resolve_api_url() -> str:
    # Prefer Reflex-specific config when present, otherwise fall back to the generic API host.
    # In dev mode (no env vars set), use localhost so the websocket connects locally.
    return (
        os.getenv("REFLEX_API_URL")
        or os.getenv("API_URL")
        or "http://localhost:8000"
    ).rstrip("/")

config = rx.Config(
    app_name="uni_app",
    deploy_url=_resolve_public_url(),
    
    api_url=_resolve_api_url(),
    favicon="favicon-v2.ico",
    
    db_url=os.getenv("DATABASE_URL", "sqlite:///reflex.db"),
    show_built_with_reflex=False,
    
    plugins=[
        rx.plugins.SitemapPlugin(),
    ],
)
