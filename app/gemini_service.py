import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6IiYPqGAoemoEKmt1kvO2uFOgOoBdbQGQswJRClKItiyg")

class GeminiService:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key
        self.model = "gemini-3.5-flash"

    def set_api_key(self, key: str):
        self.api_key = key.strip()

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def test_connection(self, key: Optional[str] = None) -> Dict[str, Any]:
        """Tests Gemini API key with a simple prompt."""
        test_key = key or self.api_key
        if not test_key:
            return {"connected": False, "message": "No se ha configurado ninguna clave API de Gemini."}
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={test_key}"
        payload = {
            "contents": [{"parts": [{"text": "Responde con la palabra OK si estás activo."}]}]
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    return {"connected": True, "message": "Conexión exitosa con Google Gemini AI.", "response": text.strip()}
        except Exception as e:
            return {"connected": False, "message": f"Error conectando con Gemini: {str(e)}"}

        return {"connected": False, "message": "No se pudo validar la clave de Gemini."}

    def parse_with_gemini(self, user_instruction: str, available_tours: list) -> Optional[Dict[str, Any]]:
        """Uses Gemini to parse complex or colloquial instructions into structured data."""
        if not self.is_configured():
            return None

        system_prompt = f"""
Eres el asistente de operaciones de 'Tour Galicia'. Tu labor es interpretar instrucciones del operador turístico.
Excursiones disponibles hoy:
{json.dumps(available_tours, ensure_ascii=False, indent=2)}

Analiza la instrucción y responde ÚNICAMENTE un JSON válido con este esquema exacto:
{{
  "intent": "schedule_change | info_query | send_message | review_campaign | unknown",
  "tour_id": "id del tour coincidente (null si no se menciona ninguno concreto o no existe)",
  "tour_name": "nombre del tour (null si no aplica)",
  "target_provider": "civitatis | getyourguide | viator | guruwalk | freetour | direct | null si no se especifica proveedor",
  "target_pickup": "museo | peregrino | pilar | null si no se especifica punto de encuentro",
  "target_slots": ["franjas horarias afectadas, ej: '18:00', '18:30'"],
  "new_time": "nueva hora HH:MM (null si no hay cambio de hora)",
  "reason": "motivo resumido en español (null si no aplica)",
  "explanation": "breve resumen de la acción interpretada en español"
}}

REGLAS IMPORTANTES:
- Puntos de encuentro oficiales (solo 3):
  1) 'museo' (Museo o Dársena La Salle)
  2) 'peregrino' (Exe Peregrino)
  3) 'pilar' (Capilla del Pilar / Alameda / cualquier otro punto por defecto)
- Si el usuario menciona 'Pilar', 'Peregrino' o 'Museo/Dársena', clasifícalo en target_pickup ('pilar', 'peregrino' o 'museo').
- Si el usuario pregunta por clientes, salidas, pasajeros o info de UN tour específico, PROVEEDOR o PUNTO DE ENCUENTRO → intent: "info_query"
- Si pide avisar/cambiar hora/notificar/unificar → intent: "schedule_change"
- Si menciona Civitatis, GetYourGuide/GYG, Viator/TripAdvisor, GuruWalk o Directo/Web, pon el valor correspondiente en target_provider.
- Si no menciona ningún tour concreto o no coincide con la lista → tour_id: null
- target_slots vacío [] si aplica a todas las franjas del tour
- NO inventes tour_id que no esté en la lista disponible
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {"parts": [{"text": f"{system_prompt}\n\nInstrucción del operador:\n{user_instruction}"}]}
            ],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    parsed = json.loads(text)
                    return parsed
        except Exception as e:
            logger.warning(f"Error llamando a Gemini ({e}), usando fallback.")
            return None

gemini = GeminiService()
