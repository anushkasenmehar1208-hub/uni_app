import reflex as rx
import os

config = rx.Config(
    app_name="uni_app",
    api_url=os.getenv("API_URL", "https://uniapp-production-01d0.up.railway.app"),
    db_url=os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_l2RpcO8fGLtu@ep-long-feather-a1d7txg7.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"),
)