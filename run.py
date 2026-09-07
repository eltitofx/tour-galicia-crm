import sys
import uvicorn
from app.config import HOST, PORT

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

if __name__ == "__main__":
    print("=" * 60)
    print("Tour Galicia - Asistente CRM & Panel WhatsApp")
    print(f"Servidor activo en: http://{HOST}:{PORT}")
    print("=" * 60)
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
