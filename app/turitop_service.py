import os
import json
import logging
import html
import re
import time
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import urllib.request
import urllib.error

from app.config import TURITOP_SHORT_ID, TURITOP_SECRET_KEY, TURITOP_API_BASE_URL, COMPANY_NAME
from app.language_detector import detect_language, clean_phone_number

logger = logging.getLogger(__name__)

PICKUP_POINTS_CONFIG = {
    "museo": {
        "id": "museo",
        "short_name": "Museo",
        "full_name": "Museo / Dársena La Salle",
        "keywords": ["museo", "darsena", "dársena", "salle", "la salle", "pobo", "san domingos", "xoan", "juan xxiii"],
        "badge_color": "bg-indigo-100 text-indigo-800 border-indigo-300",
        "icon": "🏛️"
    },
    "peregrino": {
        "id": "peregrino",
        "short_name": "Peregrino",
        "full_name": "Hotel Exe Peregrino",
        "keywords": ["peregrino", "exe", "pregrino", "rosalia", "rosalía"],
        "badge_color": "bg-emerald-100 text-emerald-800 border-emerald-300",
        "icon": "🏨"
    },
    "pilar": {
        "id": "pilar",
        "short_name": "Pilar",
        "full_name": "Capilla del Pilar",
        "keywords": ["pilar", "capilla", "alameda"],
        "badge_color": "bg-amber-100 text-amber-800 border-amber-300",
        "icon": "⛪"
    }
}

def extract_departure_point(booking: dict, tour_name: str = "") -> dict:
    """
    Classifies the client into EXACTLY ONE OF THE 3 OFFICIAL PICKUP POINTS:
    1: Museo o Darsena la Salle = Museo ("Museo / Dársena La Salle")
    2: Exe peregrino = Peregrino ("Hotel Exe Peregrino")
    3: Cualquier otro producto o recogida Capilla del Pilar = Pilar ("Capilla del Pilar") [DEFAULT]
    """
    client = booking.get("client_data") or {}
    comments = str(client.get("comments") or "")
    notes = str(booking.get("notes") or "")
    pickup = str(booking.get("pickup_point") or "")
    hotel = str(booking.get("hotel_name") or "")
    location = str(booking.get("location") or "")

    combined = f"{comments} {notes} {pickup} {hotel} {location}".lower()

    # 1. Museo o Dársena La Salle
    if any(k in combined for k in ["museo", "darsena", "dársena", "salle", "la salle", "pobo", "san domingos", "xoan", "juan xxiii"]):
        return PICKUP_POINTS_CONFIG["museo"]

    # 2. Exe Peregrino
    if any(k in combined for k in ["peregrino", "exe", "pregrino", "rosalia", "rosalía"]):
        return PICKUP_POINTS_CONFIG["peregrino"]

    # 3. Capilla del Pilar (Cualquier otro producto o recogida por defecto)
    return PICKUP_POINTS_CONFIG["pilar"]

def extract_provider(booking: dict) -> dict:
    """
    Identifies the OTA / booking platform provider:
    - Civitatis
    - GetYourGuide
    - Viator / TripAdvisor
    - GuruWalk
    - FreeTour.com
    - Web Directa (TuriTop)
    - Otros / Directo
    """
    client = booking.get("client_data") or {}
    comments = str(client.get("comments") or "")
    notes = str(booking.get("notes") or "")
    short_id = str(booking.get("short_id") or "")
    email = str(client.get("email") or "").lower()
    agent_name = str(booking.get("agent_name") or "")
    agency = str(booking.get("agency") or "")

    combined = f"{comments} {notes} {short_id} {email} {agent_name} {agency}".lower()

    # 1. CIVITATIS
    if "civitatis" in combined or short_id.startswith("C731") or "c731" in short_id.lower():
        ref_match = re.search(r'civitatis\s*(?:bookingid:?)?\s*([a-zA-Z0-9]+)', f"{comments} {notes}", re.IGNORECASE)
        ref = ref_match.group(1) if ref_match else ""
        return {
            "id": "civitatis",
            "name": "Civitatis",
            "code": "CIV",
            "reference": ref,
            "badge_color": "bg-purple-100 text-purple-800 border-purple-300",
            "icon": "🟣"
        }

    # 2. GETYOURGUIDE
    if "gyg" in combined or "getyourguide" in combined:
        ref_match = re.search(r'(GYG[A-Za-z0-9]+)', notes) or re.search(r'(GYG[A-Za-z0-9]+)', comments)
        ref = ref_match.group(1) if ref_match else ""
        return {
            "id": "getyourguide",
            "name": "GetYourGuide",
            "code": "GYG",
            "reference": ref,
            "badge_color": "bg-orange-100 text-orange-800 border-orange-300",
            "icon": "🟠"
        }

    # 3. VIATOR / TRIPADVISOR
    if "viator" in combined or "tripadvisor" in combined or "*** viator" in combined:
        ref_match = re.search(r'(BR-[A-Za-z0-9]+)', combined, re.IGNORECASE) or re.search(r'booking\s*reference:?\s*([A-Za-z0-9-]+)', combined, re.IGNORECASE)
        ref = ref_match.group(1) if ref_match else ""
        return {
            "id": "viator",
            "name": "Viator / TripAdvisor",
            "code": "VIA",
            "reference": ref,
            "badge_color": "bg-emerald-100 text-emerald-800 border-emerald-300",
            "icon": "🟢"
        }

    # 4. GURUWALK
    if "guruwalk" in combined:
        return {
            "id": "guruwalk",
            "name": "GuruWalk",
            "code": "GUR",
            "reference": "",
            "badge_color": "bg-teal-100 text-teal-800 border-teal-300",
            "icon": "🔵"
        }

    # 5. FREETOUR.COM
    if "freetour.com" in combined or "freetour" in combined:
        return {
            "id": "freetour",
            "name": "FreeTour.com",
            "code": "FT",
            "reference": "",
            "badge_color": "bg-cyan-100 text-cyan-800 border-cyan-300",
            "icon": "🌐"
        }

    # 6. WEB DIRECTA (TURITOP)
    if booking.get("source") == "frontoffice" or (client.get("email") and not "none" in str(client.get("email")).lower()):
        return {
            "id": "direct",
            "name": "Web Directa",
            "code": "WEB",
            "reference": "",
            "badge_color": "bg-blue-100 text-blue-800 border-blue-300",
            "icon": "🌐"
        }

    # 7. OTROS / AGENCIA
    return {
        "id": "otros",
        "name": "Otros / Directo",
        "code": "OTR",
        "reference": "",
        "badge_color": "bg-slate-100 text-slate-700 border-slate-300",
        "icon": "⚪"
    }

class TuriTopService:
    def __init__(self, short_id: str = TURITOP_SHORT_ID, secret_key: str = TURITOP_SECRET_KEY):
        self.short_id = short_id
        self.secret_key = secret_key
        self.cached_products = []
        self.cached_bookings = []

    def test_connection(self) -> Dict[str, Any]:
        """Tests live connection to TuriTop API with Bearer token."""
        if not self.secret_key:
            return {"connected": False, "message": "Falta Secret_key de TuriTop."}
        
        try:
            url = f"{TURITOP_API_BASE_URL}/product/getproducts"
            req = urllib.request.Request(
                url,
                data=b"{}",
                headers={
                    "Authorization": f"Bearer {self.secret_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "TourGalicia-Assistant/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    products = data.get("data", {}).get("products", [])
                    return {
                        "connected": True,
                        "total_products": len(products),
                        "message": f"Conectado en Vivo con TuriTop ({self.short_id}) - {len(products)} excursiones activas."
                    }
        except Exception as e:
            return {
                "connected": False,
                "fallback_mode": True,
                "message": f"Error conectando con TuriTop: {str(e)}"
            }

        return {"connected": False, "message": "Respuesta no satisfactoria de TuriTop."}

    def fetch_live_products(self) -> List[Dict[str, Any]]:
        """Retrieves all real products from TuriTop."""
        if not self.secret_key:
            return []
        try:
            url = f"{TURITOP_API_BASE_URL}/product/getproducts"
            req = urllib.request.Request(
                url,
                data=b"{}",
                headers={
                    "Authorization": f"Bearer {self.secret_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "TourGalicia-Assistant/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    raw_products = data.get("data", {}).get("products", [])
                    cleaned = []
                    for p in raw_products:
                        if not p.get("disabled", False):
                            name = html.unescape(p.get("name", ""))
                            cleaned.append({
                                "id": p.get("short_id"),
                                "short_id": p.get("short_id"),
                                "name": name,
                                "summary": html.unescape(p.get("summary", "") or "")
                            })
                    self.cached_products = cleaned
                    return cleaned
        except Exception as e:
            logger.error(f"Error fetching live products: {e}")
        return []

    def get_tours(self) -> List[Dict[str, Any]]:
        if not self.cached_products:
            self.fetch_live_products()
        return self.cached_products

    def get_bookings(
        self,
        tour_id: Optional[str] = None,
        pickup_filter: Optional[str] = None,
        target_date: Optional[Any] = None,
        provider_filter: Optional[str] = None,
        date_from: Optional[Any] = None,
        date_to: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves real bookings from TuriTop CRM for TODAY (or specific date/period YYYY-MM-DD).
        Enriches each booking with cleaned phone, language, normalized pick-up point, provider/OTA, and exact pax.
        """
        if not self.secret_key:
            return []

        try:
            url = f"{TURITOP_API_BASE_URL}/booking/getbookings"
            
            # Determine date range
            if date_from and date_to:
                if isinstance(date_from, str):
                    d_from = datetime.strptime(date_from.strip(), "%Y-%m-%d").date()
                else:
                    d_from = date_from
                if isinstance(date_to, str):
                    d_to = datetime.strptime(date_to.strip(), "%Y-%m-%d").date()
                else:
                    d_to = date_to
                day_start = int(datetime(d_from.year, d_from.month, d_from.day, 0, 0, 0).timestamp())
                day_end = int(datetime(d_to.year, d_to.month, d_to.day, 23, 59, 59).timestamp())
            elif isinstance(target_date, str) and target_date.strip():
                try:
                    d = datetime.strptime(target_date.strip(), "%Y-%m-%d").date()
                except Exception:
                    d = date.today()
                day_start = int(datetime(d.year, d.month, d.day, 0, 0, 0).timestamp())
                day_end = int(datetime(d.year, d.month, d.day, 23, 59, 59).timestamp())
            elif isinstance(target_date, date):
                d = target_date
                day_start = int(datetime(d.year, d.month, d.day, 0, 0, 0).timestamp())
                day_end = int(datetime(d.year, d.month, d.day, 23, 59, 59).timestamp())
            else:
                d = date.today()
                day_start = int(datetime(d.year, d.month, d.day, 0, 0, 0).timestamp())
                day_end = int(datetime(d.year, d.month, d.day, 23, 59, 59).timestamp())

            payload = {
                "data": {
                    "filter": {
                        "event_date_from": day_start,
                        "event_date_to": day_end
                    }
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.secret_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "TourGalicia-Assistant/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    raw_bookings = data.get("data", {}).get("bookings", [])
                    parsed = []

                    for b in raw_bookings:
                        p_id = b.get("product_short_id", "")
                        if tour_id and p_id != tour_id:
                            continue

                        provider_data = extract_provider(b)
                        if provider_filter and provider_filter != "all":
                            # Check either provider id or name match
                            p_filter_norm = provider_filter.lower().strip()
                            if provider_data["id"] != p_filter_norm and p_filter_norm not in provider_data["name"].lower():
                                continue

                        client = b.get("client_data") or {}
                        client_name = html.unescape(client.get("name", "Cliente") or "Cliente")
                        phone = client.get("phone", "")
                        clean_phone = clean_phone_number(phone)
                        lang_info = detect_language(clean_phone)

                        p_name = html.unescape(b.get("product_name", "") or "")
                        pickup_data = extract_departure_point(b, p_name)

                        if pickup_filter and pickup_filter != "all":
                            p_norm = str(pickup_filter).lower().strip()
                            matches = (
                                pickup_data["id"] == p_norm
                                or pickup_data["short_name"].lower() == p_norm
                                or p_norm in pickup_data["full_name"].lower()
                                or any(p_norm in kw for kw in pickup_data["keywords"])
                                or any(kw in p_norm for kw in pickup_data["keywords"])
                            )
                            if not matches:
                                continue

                        # Date & hour
                        date_iso = b.get("date_event_iso8601", "")
                        slot_str = "09:00"
                        if "T" in date_iso:
                            time_part = date_iso.split("T")[1][:5]
                            if time_part and time_part != "00:00":
                                slot_str = time_part

                        pax = 1
                        t_counts = b.get("ticket_type_count")
                        if isinstance(t_counts, list) and t_counts:
                            pax_calc = sum(item.get("count", 0) for item in t_counts if isinstance(item, dict))
                            pax = pax_calc if pax_calc > 0 else 1
                        elif isinstance(t_counts, dict) and t_counts:
                            pax = sum(t_counts.values()) or 1

                        status_raw = str(b.get("status") or "confirmed").lower()
                        status_label = "Confirmado"
                        if "paid" in status_raw and "not" not in status_raw:
                            status_label = "Pagado"
                        elif "not paid" in status_raw or "unpaid" in status_raw:
                            status_label = "Pendiente Pago"
                        elif "cancelled" in status_raw or "cancel" in status_raw:
                            status_label = "Cancelado"

                        parsed.append({
                            "id": b.get("short_id"),
                            "tour_id": p_id,
                            "tour_name": p_name,
                            "client_name": client_name,
                            "phone": clean_phone or phone,
                            "raw_phone": phone,
                            "slot": slot_str,
                            "date_iso": date_iso,
                            "pickup_stop": pickup_data["full_name"],
                            "pickup_short": pickup_data["short_name"],
                            "pickup_code": pickup_data["id"],
                            "pickup_badge": pickup_data["badge_color"],
                            "pickup_icon": pickup_data["icon"],
                            "pickup_info": pickup_data,
                            "comments": html.unescape(str(client.get("comments") or "")),
                            "notes": html.unescape(str(b.get("notes") or "")),
                            "pax": pax,
                            "status": status_label,
                            "raw_status": status_raw,
                            "checked": b.get("checked", False),
                            "language": lang_info,
                            "provider": provider_data
                        })

                    self.cached_bookings = parsed
                    return parsed
        except Exception as e:
            logger.error(f"Error fetching live bookings: {e}")

        return self.cached_bookings

    def get_all_tours_summary_message(self, target_date: Optional[Any] = None) -> str:
        now_str = datetime.now().strftime("%d/%m/%Y")
        all_b = self.get_bookings(target_date=target_date)
        
        lines = []
        lines.append(f"🚌 *RESUMEN DE SALIDAS Y PUNTOS DE RECOGIDA — {COMPANY_NAME}*")
        lines.append(f"📅 *Fecha:* {now_str} (Sincronizado TuriTop CRM)")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        if not all_b:
            lines.append("ℹ️ No hay reservas registradas en TuriTop.")
            return "\n".join(lines)

        tours_map = {}
        for b in all_b:
            tours_map.setdefault(b["tour_name"], []).append(b)

        total_passengers = 0
        lang_counts = {}
        prov_counts = {}

        for tour_name, b_list in tours_map.items():
            tour_pax = sum(b.get("pax", 1) for b in b_list)
            total_passengers += tour_pax
            lines.append(f"📍 *{tour_name}* ({len(b_list)} reservas / {tour_pax} pax)")

            # Group by pickup stop
            pickups = {}
            for b in b_list:
                p_stop = b["pickup_stop"]
                pickups.setdefault(p_stop, []).append(b)
                flag = b["language"]["flag"]
                lang_name = b["language"]["name"]
                lang_counts[f"{flag} {lang_name}"] = lang_counts.get(f"{flag} {lang_name}", 0) + 1
                
                prov = b.get("provider", {})
                prov_name = prov.get("name", "Otros")
                prov_counts[prov_name] = prov_counts.get(prov_name, 0) + 1

            for p_stop, p_bookings in pickups.items():
                lines.append(f"  🏢 *Punto de Salida:* _{p_stop}_ ({len(p_bookings)} pax):")
                for b in p_bookings:
                    prov = b.get("provider", {})
                    prov_badge = f"[{prov.get('code', 'OTR')}]"
                    ref_str = f" Ref:{prov.get('reference')}" if prov.get('reference') else ""
                    lines.append(f"    • {b['client_name']} ({b['pax']} pax) {prov_badge}{ref_str} — {b['slot']} [{b['language']['flag']}]")
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"📊 *TOTAL:* {len(all_b)} reservas | {total_passengers} pasajeros")
        lines.append(f"🏢 *Proveedores / Canales:* " + " | ".join(f"{k}: {v}" for k, v in prov_counts.items()))
        lines.append(f"🌍 *Idiomas:* " + " | ".join(f"{k}: {v}" for k, v in lang_counts.items()))

        return "\n".join(lines)

turitop = TuriTopService()
