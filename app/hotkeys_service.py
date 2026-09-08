import os
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

HOTKEYS_FILE = Path(__file__).resolve().parent.parent / "custom_hotkeys.json"

DEFAULT_HOTKEYS = [
    {
        "id": "hk_catedrales_0800",
        "title": "🏖️ Catedrales 08:00 mañana",
        "description": "Aviso de salida a las 08:00 para Playa de las Catedrales de mañana",
        "icon": "🏖️",
        "color": "bg-blue-50 text-blue-700 border-blue-300 hover:bg-blue-100",
        "prompt": "Avisa a los clientes de la Playa de las Catedrales de que mañana sale el tour a las 08:00",
        "auto_execute": True
    },
    {
        "id": "hk_meigas_1900",
        "title": "🌙 Meigas a las 19:00 (Cambio hora)",
        "description": "Cambio de hora a las 19:00 para Meigas (solo avisa a clientes de otras horas)",
        "icon": "🌙",
        "color": "bg-purple-50 text-purple-700 border-purple-300 hover:bg-purple-100",
        "prompt": "Avisa a los clientes del Tour de Meigas de hoy que la salida sera a las 19:00",
        "auto_execute": True
    },
    {
        "id": "hk_cambio_finisterre_regular",
        "title": "🔄 Finisterre Express a Regular",
        "description": "Avisa del cambio de Finisterre Express a Finisterre Costa da Morte Regular",
        "icon": "🔄",
        "color": "bg-amber-50 text-amber-800 border-amber-300 hover:bg-amber-100",
        "prompt": "Avisa a los clientes de Finisterre Express de mañana del cambio del tour a Finisterre Costa da Morte regular desde Santiago",
        "auto_execute": True
    },
    {
        "id": "hk_finisterre_salidas_manana",
        "title": "🚌 Finisterre Salidas Mañana",
        "description": "Aviso de paradas y horas de salida para Finisterre mañana",
        "icon": "🚌",
        "color": "bg-emerald-50 text-emerald-800 border-emerald-300 hover:bg-emerald-100",
        "prompt": "Avisa a los clientes de Finisterre y Costa da Morte de mañana del punto de salida",
        "auto_execute": True
    },
    {
        "id": "hk_rias_baixas_hoy",
        "title": "🌊 Rías Baixas Salidas Hoy",
        "description": "Aviso de salida para Rías Baixas hoy",
        "icon": "🌊",
        "color": "bg-cyan-50 text-cyan-800 border-cyan-300 hover:bg-cyan-100",
        "prompt": "Avisa a los clientes de Rías Baixas de hoy del punto de salida",
        "auto_execute": True
    },
    {
        "id": "hk_minimo_finisterre_express",
        "title": "⚠️ Falta Mínimo Finisterre Express",
        "description": "Aviso de cancelación por no alcanzar mínimo de pax para Finisterre Express mañana",
        "icon": "⚠️",
        "color": "bg-rose-50 text-rose-800 border-rose-300 hover:bg-rose-100",
        "prompt": "Avisa a todos los clientes del tour Finisterre Express que no hemos alcanzado el numero minimo de participantes para mañana",
        "auto_execute": True
    },
    {
        "id": "hk_resenas_ayer",
        "title": "⭐ Solicitar Reseñas de Ayer",
        "description": "Pide reseñas a los clientes que viajaron ayer según su plataforma e idioma",
        "icon": "⭐",
        "color": "bg-yellow-50 text-yellow-800 border-yellow-300 hover:bg-yellow-100",
        "prompt": "Solicita una reseña a los clientes que viajaron ayer con nosotros acorde a su plataforma e idioma",
        "auto_execute": True
    }
]

class HotkeysManager:
    def __init__(self):
        self.hotkeys = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if HOTKEYS_FILE.exists():
            try:
                with open(HOTKEYS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        return data
            except Exception as e:
                print("Error loading custom_hotkeys.json:", e)

        # Fallback to default hotkeys
        self._save(DEFAULT_HOTKEYS)
        return DEFAULT_HOTKEYS.copy()

    def _save(self, data: List[Dict[str, Any]]) -> bool:
        try:
            with open(HOTKEYS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print("Error saving hotkeys to disk:", e)
            return False

    def get_all(self) -> List[Dict[str, Any]]:
        return self.hotkeys

    def add_or_update(self, item: Dict[str, Any]) -> Dict[str, Any]:
        hk_id = item.get("id") or f"hk_{uuid.uuid4().hex[:8]}"
        new_hk = {
            "id": hk_id,
            "title": str(item.get("title", "Acción Rápida")).strip(),
            "description": str(item.get("description", "")).strip(),
            "icon": str(item.get("icon", "⚡")).strip() or "⚡",
            "color": str(item.get("color", "bg-blue-50 text-blue-700 border-blue-300 hover:bg-blue-100")),
            "prompt": str(item.get("prompt", "")).strip(),
            "auto_execute": bool(item.get("auto_execute", True))
        }

        existing_idx = next((i for i, h in enumerate(self.hotkeys) if h.get("id") == hk_id), None)
        if existing_idx is not None:
            self.hotkeys[existing_idx] = new_hk
        else:
            self.hotkeys.append(new_hk)

        self._save(self.hotkeys)
        return new_hk

    def delete(self, hk_id: str) -> bool:
        init_len = len(self.hotkeys)
        self.hotkeys = [h for h in self.hotkeys if h.get("id") != hk_id]
        if len(self.hotkeys) != init_len:
            return self._save(self.hotkeys)
        return False

hotkeys_mgr = HotkeysManager()
