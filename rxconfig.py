import reflex as rx
import os

def _resolve_public_url() -> str:
    return os.getenv("APP_BASE_URL", "https://alexstudies.com").rstrip("/")

def _resolve_api_url() -> str:
    # Support both the expected key and the currently-used typo in Railway vars.
    return (
        os.getenv("REFLEX_API_URL")
        or os.getenv("REFLEX_API_URL")
        or os.getenv("API_URL")
        or "https://alexstudies.com"
    ).rstrip("/")

config = rx.Config(
    app_name="uni_app",
    deploy_url=_resolve_public_url(),
    
    api_url=_resolve_api_url(),
    favicon="brand-favicon-20260306.ico",
    
    db_url=os.getenv("DATABASE_URL", "sqlite:///reflex.db"),
    show_built_with_reflex=False,
    
    plugins=[
        rx.plugins.SitemapPlugin(),
    ],
)
