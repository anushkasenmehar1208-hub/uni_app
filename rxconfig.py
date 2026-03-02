import reflex as rx
import os

config = rx.Config(
    app_name="uni_app",
    api_url=f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}",
    db_url=os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_l2RpcO8fGLtu@ep-long-feather-a1d7txg7.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"),
)