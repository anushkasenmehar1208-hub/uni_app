import reflex as rx
import os

railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
default_api_url = "https://alexstudies.com"

config = rx.Config(
    app_name="uni_app",
    api_url=os.getenv("API_URL", default_api_url),
    db_url=os.getenv("DATABASE_URL", "sqlite:///reflex.db"),
    frontend_port=3001,
    backend_port=8000,
    show_built_with_reflex=False,
)
