import time
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import WHATSAPP_PROVIDER, WHATSAPP_API_URL, WHATSAPP_API_KEY, WHATSAPP_INSTANCE

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.provider = WHATSAPP_PROVIDER  # 'evolution_api', 'wassenger', 'simulator'
        self.api_url = WHATSAPP_API_URL.rstrip('/')
        self.api_key = WHATSAPP_API_KEY
        self.instance = WHATSAPP_INSTANCE
        self.delivery_history: List[Dict[str, Any]] = []

    def get_status(self) -> Dict[str, Any]:
        """Checks the live WhatsApp gateway connection state."""
        if self.provider == "simulator" or not self.api_url:
            return {
                "provider": "simulator",
                "connected": True,
                "status": "Modo Simulador Seguro (Activo)",
                "details": "Listo para probar y verificar mensajes en pantalla."
            }

        # Check Evolution API instance status
        try:
            url = f"{self.api_url}/instance/connectionState/{self.instance}"
            req = urllib.request.Request(
                url,
                headers={"apikey": self.api_key, "User-Agent": "TourGalicia-CRM/1.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    state = data.get("instance", {}).get("state", "close")
                    return {
                        "provider": "evolution_api",
                        "connected": state == "open",
                        "status": "Conectado por QR" if state == "open" else "Desconectado (Escanear QR)",
                        "state": state,
                        "instance": self.instance
                    }
        except Exception as e:
            return {
                "provider": self.provider,
                "connected": False,
                "status": f"No conectado al gateway ({str(e)})",
                "instance": self.instance
            }

    def get_qr_code(self) -> Dict[str, Any]:
        """Fetches the QR code for scanning with the WhatsApp mobile app."""
        if self.provider == "simulator" or not self.api_url:
            return {
                "success": True,
                "simulator": True,
                "message": "En modo simulador no se requiere escanear QR."
            }

        try:
            url = f"{self.api_url}/instance/connect/{self.instance}"
            req = urllib.request.Request(
                url,
                headers={"apikey": self.api_key, "User-Agent": "TourGalicia-CRM/1.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status in (200, 201):
                    data = json.loads(resp.read().decode("utf-8"))
                    base64_qr = data.get("base64") or data.get("qrcode", {}).get("base64")
                    code = data.get("code") or data.get("qrcode", {}).get("code")
                    return {
                        "success": True,
                        "base64": base64_qr,
                        "code": code,
                        "instance": self.instance
                    }
        except Exception as e:
            logger.error(f"Error fetching WhatsApp QR code: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Error conectando con el servidor de WhatsApp QR: {e}"
            }

    def send_single_message(self, phone: str, text: str) -> Dict[str, Any]:
        """Dispatches a single WhatsApp message via QR gateway or simulator."""
        clean_p = phone.replace("+", "").replace(" ", "").replace("-", "").strip()

        if self.provider == "evolution_api" and self.api_url:
            try:
                url = f"{self.api_url}/message/sendText/{self.instance}"
                payload = json.dumps({
                    "number": clean_p,
                    "text": text,
                    "options": {
                        "delay": 1200,
                        "presence": "composing"
                    }
                }).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={
                        "apikey": self.api_key,
                        "Content-Type": "application/json",
                        "User-Agent": "TourGalicia-CRM/1.0"
                    }
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status in (200, 201):
                        return {"success": True, "provider": "evolution_api", "status": "Enviado"}
            except Exception as e:
                logger.error(f"Error sending WhatsApp to {phone}: {e}")
                return {"success": False, "error": str(e), "status": "Error de envío"}

        # Simulator fallback
        return {"success": True, "provider": "simulator", "status": "Entregado (Simulación)"}

    def send_broadcast(self, messages_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sends a batch of WhatsApp messages.
        Dispatches in real time if Evolution API is configured, or logs in simulator mode.
        """
        results = []
        sent_count = 0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for msg in messages_batch:
            phone = msg.get("phone", "")
            content = msg.get("message", "")
            dispatch_res = self.send_single_message(phone=phone, text=content)

            delivery_record = {
                "id": f"MSG-{int(time.time()*1000)}-{sent_count}",
                "timestamp": timestamp,
                "client_name": msg.get("client_name"),
                "phone": phone,
                "language": msg.get("language", {}).get("name", "Español"),
                "flag": msg.get("language", {}).get("flag", "🇪🇸"),
                "status": dispatch_res.get("status", "Enviado"),
                "preview": content[:120] + "...",
                "full_message": content,
                "provider": dispatch_res.get("provider", self.provider)
            }
            
            results.append(delivery_record)
            self.delivery_history.insert(0, delivery_record) # most recent first
            sent_count += 1

        return {
            "success": True,
            "provider": self.provider,
            "total_sent": sent_count,
            "timestamp": timestamp,
            "deliveries": results
        }

    def get_history(self) -> List[Dict[str, Any]]:
        return self.delivery_history

whatsapp = WhatsAppService()
