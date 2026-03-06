import reflex as rx
import os

config = rx.Config(
    app_name="uni_app",
    # This fixes your Google Sitemap localhost issue
    deploy_url="https://alexstudies.com", 
    
    # This fixes the connection to your Railway backend
    api_url="https://alexstudies.com",
    
    db_url=os.getenv("DATABASE_URL", "sqlite:///reflex.db"),
    show_built_with_reflex=False,
    
    # The correct syntax to enable the plugin
    plugins=[
        rx.plugins.SitemapPlugin(),
    ],
)