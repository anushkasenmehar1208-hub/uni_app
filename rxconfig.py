import reflex as rx
import os

config = rx.Config(
    app_name="uni_app",
    api_url="https://uniapp-production-01d0.up.railway.app",
    db_url=os.getenv("DATABASE_URL"),
)