import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# TuriTop CRM Credentials
TURITOP_SHORT_ID = os.getenv("TURITOP_SHORT_ID", "T955")
TURITOP_SECRET_KEY = os.getenv("TURITOP_SECRET_KEY", "NBzHliwdT2GZutt9jhUHLA8gGzAHYK9L")
TURITOP_API_BASE_URL = os.getenv("TURITOP_API_BASE_URL", "https://app.turitop.com/v1")

# Company Info
COMPANY_NAME = os.getenv("COMPANY_NAME", "Tour Galicia")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+34 981 00 00 00")

# WhatsApp Provider: 'simulator', 'evolution_api', 'wassenger', 'meta'
WHATSAPP_PROVIDER = os.getenv("WHATSAPP_PROVIDER", "simulator")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "http://localhost:8080")
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "")
WHATSAPP_INSTANCE = os.getenv("WHATSAPP_INSTANCE", "tour-galicia")

# Admin Auth Credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "TourGalicia1234.")
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "tg-secret-auth-key-2026-galicia")

# Server Config
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "127.0.0.1")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
