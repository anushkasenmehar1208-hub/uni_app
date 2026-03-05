import reflex as rx
import os

config = rx.Config(
    app_name="uni_app",
    # This fixes your Google Sitemap localhost issue
    frontend_url="https://alexstudies.com", 
    
    # This fixes the connection to your Railway backend
    api_url="https://uniapp-production-01d0.up.railway.app",
    
    db_url=os.getenv("DATABASE_URL", "sqlite:///reflex.db"),
    show_built_with_reflex=False,
    
    # The correct syntax to enable the plugin
    plugins=[
        rx.plugins.SitemapPlugin(),
    ],
)