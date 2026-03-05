import reflex as rx
import os

config = rx.Config(
    app_name="uni_app",
    # 1. This fixes the sitemap (localhost -> alexstudies.com)
    frontend_url="https://alexstudies.com", 
    
    # 2. This fixes the connection to your database/backend
    api_url="https://uniapp-production-01d0.up.railway.app",
    
    db_url=os.getenv("DATABASE_URL", "sqlite:///reflex.db"),
    show_built_with_reflex=False,
    plugins=[
        rx.sitemap,
    ],
)