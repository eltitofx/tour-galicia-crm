import os
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.config import COMPANY_NAME, TURITOP_SHORT_ID, WHATSAPP_PROVIDER
from app.turitop_service import turitop
from app.assistant import assistant
from app.whatsapp_service import whatsapp
from app.templates_service import template_mgr
from app.gemini_service import gemini
from app.auth_service import auth_service

app = FastAPI(title="Tour Galicia - Panel de Operaciones & WhatsApp CRM", version="1.0.0")

class LoginRequest(BaseModel):
    username: str
    password: str

class AssistantPromptRequest(BaseModel):
    prompt: str
    target_date: Optional[str] = None

class BroadcastRequest(BaseModel):
    messages: List[Dict[str, Any]]

class SaveTemplatesRequest(BaseModel):
    templates: Dict[str, Any]

class GeminiConfigRequest(BaseModel):
    api_key: str

class CustomTemplateModel(BaseModel):
    id: Optional[str] = None
    title: str
    tour_id: Optional[str] = "all"
    tour_name: Optional[str] = "Todos los Tours"
    language: Optional[str] = "es"
    category: Optional[str] = "departure_pickup"
    content: str

class PrepareBroadcastRequest(BaseModel):
    tour_id: str
    pickup_stop: Optional[str] = "all"
    provider: Optional[str] = "all"
    departure_time: Optional[str] = "09:00"
    departure_date: Optional[str] = None
    reason: Optional[str] = "motivos de organización"

def get_current_user(authorization: Optional[str] = Header(None)):
    """Verifies that the incoming request has a valid auth token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No autorizado. Inicie sesión.")
    payload = auth_service.verify_token(authorization)
    if not payload:
        raise HTTPException(status_code=401, detail="Sesión expirada o token inválido.")
    return payload

@app.post("/api/auth/login")
def login(req: LoginRequest):
    if not auth_service.verify_credentials(req.username, req.password):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
    token = auth_service.create_token(req.username)
    return {
        "success": True,
        "token": token,
        "user": {
            "username": "Admin",
            "role": "Administrador",
            "company": COMPANY_NAME
        },
        "message": "Inicio de sesión correcto."
    }

@app.get("/api/auth/verify")
def verify_auth(user: dict = Depends(get_current_user)):
    return {
        "authenticated": True,
        "user": user.get("user", "Admin"),
        "company": COMPANY_NAME
    }

@app.post("/api/auth/logout")
def logout():
    return {"success": True, "message": "Sesión cerrada correctamente."}

@app.get("/api/status")
def get_system_status():
    turitop_conn = turitop.test_connection()
    return {
        "company": COMPANY_NAME,
        "turitop": {
            "short_id": TURITOP_SHORT_ID,
            "connected": turitop_conn.get("connected", False),
            "total_products": turitop_conn.get("total_products", 44),
            "message": turitop_conn.get("message", "Conectado en Vivo")
        },
        "whatsapp": {
            "provider": WHATSAPP_PROVIDER,
            "status": "Activo (Simulador Seguro)" if WHATSAPP_PROVIDER == "simulator" else "Conectado"
        },
        "gemini": {
            "configured": gemini.is_configured(),
            "model": gemini.model
        }
    }

@app.get("/api/tours")
def get_tours():
    return turitop.get_tours()

@app.get("/api/overview")
def get_daily_overview(target_date: Optional[str] = None):
    return {
        "summary_message": turitop.get_all_tours_summary_message(target_date=target_date),
        "total_bookings": len(turitop.get_bookings(target_date=target_date))
    }

@app.get("/api/bookings")
def get_bookings(tour_id: Optional[str] = None, pickup: Optional[str] = None, target_date: Optional[str] = None, provider: Optional[str] = None):
    return turitop.get_bookings(tour_id=tour_id, pickup_filter=pickup, target_date=target_date, provider_filter=provider)

@app.post("/api/broadcast/prepare")
def prepare_broadcast_by_pickup(req: PrepareBroadcastRequest):
    """
    Filters bookings by tour, departure date, departure point, and provider, then prepares the multilingual
    messages with audioguide links in 1 click.
    """
    bookings = turitop.get_bookings(
        tour_id=req.tour_id,
        pickup_filter=req.pickup_stop if req.pickup_stop != "all" else None,
        target_date=req.departure_date,
        provider_filter=req.provider if req.provider != "all" else None
    )
    
    tours = turitop.get_tours()
    tour_obj = next((t for t in tours if t["id"] == req.tour_id or t.get("short_id") == req.tour_id), None)
    tour_name = tour_obj["name"] if tour_obj else "Excursión Tour Galicia"

    prepared = []
    lang_summary = {}

    for b in bookings:
        lang_code = b["language"]["code"]
        lang_name = b["language"]["name"]
        flag = b["language"]["flag"]

        lang_summary[lang_name] = lang_summary.get(lang_name, {"count": 0, "flag": flag})
        lang_summary[lang_name]["count"] += 1

        msg = template_mgr.render(
            client_name=b["client_name"],
            tour_name=tour_name,
            new_time=req.departure_time or b["slot"],
            pickup_stop=b["pickup_stop"],
            reason=req.reason,
            lang_code=lang_code,
            company_name=COMPANY_NAME,
            template_type="departure_pickup"
        )

        prepared.append({
            "booking_id": b["id"],
            "client_name": b["client_name"],
            "phone": b["phone"],
            "language": b["language"],
            "pickup_stop": b["pickup_stop"],
            "pickup_short": b.get("pickup_short", "Pilar"),
            "pickup_code": b.get("pickup_code", "pilar"),
            "pickup_badge": b.get("pickup_badge", "bg-amber-100 text-amber-800 border-amber-300"),
            "pickup_icon": b.get("pickup_icon", "⛪"),
            "slot": req.departure_time or b["slot"],
            "pax": b.get("pax", 1),
            "status": b.get("status", "Confirmado"),
            "provider": b.get("provider", {}),
            "message": msg
        })

    total_pax = sum(b.get("pax", 1) for b in bookings)

    return {
        "success": True,
        "tour_name": tour_name,
        "pickup_stop": req.pickup_stop,
        "provider": req.provider,
        "departure_time": req.departure_time,
        "total_clients": len(prepared),
        "total_pax": total_pax,
        "languages_summary": lang_summary,
        "clients": prepared
    }

class PrepareReviewsRequest(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    tour_id: Optional[str] = "all"
    provider: Optional[str] = "all"
    destination_type: Optional[str] = "smart_by_provider"
    custom_google_link: Optional[str] = None

@app.post("/api/reviews/prepare")
def prepare_reviews_campaign(req: PrepareReviewsRequest):
    """
    Finds clients who took tours in a date period and generates personalized WhatsApp review
    requests based on where they booked (Civitatis, GYG, Viator, or Google Maps).
    """
    from datetime import date, timedelta
    d_to_str = req.date_to or (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    d_from_str = req.date_from or d_to_str

    bookings = turitop.get_bookings(
        tour_id=req.tour_id if req.tour_id != "all" else None,
        provider_filter=req.provider if req.provider != "all" else None,
        date_from=d_from_str,
        date_to=d_to_str
    )

    tours = turitop.get_tours()
    tours_dict = {t["id"]: t["name"] for t in tours}

    prepared = []
    lang_summary = {}
    prov_summary = {}

    from app.templates_service import REVIEW_LINKS

    for b in bookings:
        lang_code = b["language"]["code"]
        lang_name = b["language"]["name"]
        flag = b["language"]["flag"]
        p_info = b.get("provider", {})
        p_id = p_info.get("id", "otros")
        p_name = p_info.get("name", "Web")

        # Determine review destination
        if req.destination_type == "google":
            dest_platform = "Google Maps"
            dest_url = req.custom_google_link or REVIEW_LINKS.get("google")
        elif req.destination_type == "smart_by_provider":
            if p_id == "civitatis":
                dest_platform = "Civitatis"
                dest_url = REVIEW_LINKS.get("civitatis")
            elif p_id == "getyourguide":
                dest_platform = "GetYourGuide"
                dest_url = REVIEW_LINKS.get("getyourguide")
            elif p_id == "viator":
                dest_platform = "TripAdvisor / Viator"
                dest_url = REVIEW_LINKS.get("viator")
            elif p_id == "guruwalk":
                dest_platform = "GuruWalk"
                dest_url = REVIEW_LINKS.get("guruwalk")
            elif p_id == "freetour":
                dest_platform = "FreeTour.com"
                dest_url = REVIEW_LINKS.get("freetour")
            else:
                dest_platform = "Google Maps"
                dest_url = req.custom_google_link or REVIEW_LINKS.get("google")
        else:
            dest_platform = "Google Maps"
            dest_url = req.custom_google_link or REVIEW_LINKS.get("google")

        t_name = b.get("tour_name") or tours_dict.get(b.get("tour_id"), "Excursión Tour Galicia")

        msg = template_mgr.render(
            client_name=b["client_name"],
            tour_name=t_name,
            lang_code=lang_code,
            company_name=COMPANY_NAME,
            template_type="review_request",
            review_link=dest_url,
            platform_name=dest_platform
        )

        lang_summary[lang_name] = lang_summary.get(lang_name, {"count": 0, "flag": flag})
        lang_summary[lang_name]["count"] += 1

        prov_summary[p_name] = prov_summary.get(p_name, 0) + 1

        prepared.append({
            "booking_id": b["id"],
            "client_name": b["client_name"],
            "phone": b["phone"],
            "language": b["language"],
            "pax": b.get("pax", 1),
            "tour_name": t_name,
            "provider": p_info,
            "platform_name": dest_platform,
            "review_link": dest_url,
            "message": msg
        })

    total_pax = sum(b.get("pax", 1) for b in bookings)

    return {
        "success": True,
        "date_from": d_from_str,
        "date_to": d_to_str,
        "total_clients": len(prepared),
        "total_pax": total_pax,
        "languages_summary": lang_summary,
        "providers_summary": prov_summary,
        "clients": prepared
    }

@app.post("/api/assistant/chat")
def process_chat_instruction(req: AssistantPromptRequest):
    if not req.prompt:
        raise HTTPException(status_code=400, detail="La instrucción no puede estar vacía.")
    result = assistant.parse_instruction(req.prompt, target_date=req.target_date)
    return result

@app.post("/api/messages/broadcast")
def broadcast_messages(req: BroadcastRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="No se proporcionaron mensajes para enviar.")
    result = whatsapp.send_broadcast(req.messages)
    return result

@app.get("/api/messages/history")
def get_history():
    return whatsapp.get_history()

@app.get("/api/whatsapp/status")
def get_whatsapp_status():
    return whatsapp.get_status()

@app.get("/api/whatsapp/qr")
def get_whatsapp_qr():
    return whatsapp.get_qr_code()

@app.get("/api/templates")
def get_templates():
    return template_mgr.get_all()

@app.post("/api/templates/save")
def save_templates(req: SaveTemplatesRequest):
    success = template_mgr.save_base_templates(req.templates)
    if not success:
        raise HTTPException(status_code=500, detail="Error al guardar las plantillas en disco.")
    return {"success": True, "message": "Plantillas guardadas correctamente."}

@app.get("/api/templates/custom")
def get_custom_templates():
    return template_mgr.get_custom_templates()

@app.post("/api/templates/custom")
def add_custom_template(req: CustomTemplateModel):
    saved = template_mgr.add_custom_template(req.dict())
    return {"success": True, "template": saved}

@app.delete("/api/templates/custom/{tpl_id}")
def delete_custom_template(tpl_id: str):
    success = template_mgr.delete_custom_template(tpl_id)
    return {"success": success}

@app.post("/api/gemini/config")
def config_gemini(req: GeminiConfigRequest):
    test_res = gemini.test_connection(req.api_key)
    if test_res.get("connected"):
        gemini.set_api_key(req.api_key)
        return {"success": True, "message": "Clave de Gemini verificada y conectada con éxito."}
    else:
        return {"success": False, "message": test_res.get("message", "Error al verificar la clave.")}

# Mount static folder
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Tour Galicia API is running."}
