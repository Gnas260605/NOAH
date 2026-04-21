"""
config.py – Tập trung tất cả cấu hình.
LOCAL_MODE=True nếu RABBITMQ_HOST=localhost (chạy không có Docker).
"""
import os

# ── RabbitMQ ──────────────────────────────────────────────────
RABBITMQ_HOST     = os.getenv("RABBITMQ_HOST",     "localhost") # Default to localhost for easy local run
RABBITMQ_QUEUE    = os.getenv("RABBITMQ_QUEUE",    "orders")
RABBITMQ_API_URL  = os.getenv("RABBITMQ_API_URL",  f"http://{RABBITMQ_HOST}:15672/api")
RABBITMQ_USER     = os.getenv("RABBITMQ_USER",     "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

# ── Local mode detection ─────────────────────────────────────
# Nếu RABBITMQ_HOST là localhost → chạy local, kết nối qua Port Map của Docker
LOCAL_DEV = (RABBITMQ_HOST in ("localhost", "127.0.0.1"))

# ── MySQL ─────────────────────────────────────────────────────
MYSQL_CONFIG = {
    "host":     os.getenv("MYSQL_HOST",     "localhost" if LOCAL_DEV else "mysql"),
    "port":     int(os.getenv("MYSQL_PORT", 3307 if LOCAL_DEV else 3306)),
    "user":     os.getenv("MYSQL_USER",     "root"),
    "password": os.getenv("MYSQL_PASSWORD", "root"),
    "database": os.getenv("MYSQL_DATABASE", "ecommerce"),
    "connection_timeout": 5,
}

# ── PostgreSQL ────────────────────────────────────────────────
POSTGRES_CONFIG = {
    "host":            os.getenv("POSTGRES_HOST",     "localhost" if LOCAL_DEV else "postgres"),
    "port":            int(os.getenv("POSTGRES_PORT", 5432)),
    "database":        os.getenv("POSTGRES_DB",       "finance"),
    "user":            os.getenv("POSTGRES_USER",     "postgres"),
    "password":        os.getenv("POSTGRES_PASSWORD", "root"),
    "connect_timeout": 5,
}

# Preserve OLD LOCAL_MODE toggle for internal services logic
LOCAL_MODE = os.getenv("FORCE_SQLITE", "false").lower() == "true"
