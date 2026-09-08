import re
from typing import Dict, Any

COUNTRY_PREFIX_MAP = {
    # ==========================================
    # 1. ESPAÑOL: ESPAÑA Y TODOS LOS PAÍSES LATINOAMERICANOS
    # ==========================================
    "34": {"code": "es", "name": "Español", "flag": "🇪🇸", "country": "España"},
    "52": {"code": "es", "name": "Español", "flag": "🇲🇽", "country": "México"},
    "54": {"code": "es", "name": "Español", "flag": "🇦🇷", "country": "Argentina"},
    "57": {"code": "es", "name": "Español", "flag": "🇨🇴", "country": "Colombia"},
    "56": {"code": "es", "name": "Español", "flag": "🇨🇱", "country": "Chile"},
    "51": {"code": "es", "name": "Español", "flag": "🇵🇪", "country": "Perú"},
    "58": {"code": "es", "name": "Español", "flag": "🇻🇪", "country": "Venezuela"},
    "593": {"code": "es", "name": "Español", "flag": "🇪🇨", "country": "Ecuador"},
    "502": {"code": "es", "name": "Español", "flag": "🇬🇹", "country": "Guatemala"},
    "53": {"code": "es", "name": "Español", "flag": "🇨🇺", "country": "Cuba"},
    "591": {"code": "es", "name": "Español", "flag": "🇧🇴", "country": "Bolivia"},
    "504": {"code": "es", "name": "Español", "flag": "🇭🇳", "country": "Honduras"},
    "595": {"code": "es", "name": "Español", "flag": "🇵🇾", "country": "Paraguay"},
    "503": {"code": "es", "name": "Español", "flag": "🇸🇻", "country": "El Salvador"},
    "505": {"code": "es", "name": "Español", "flag": "🇳🇮", "country": "Nicaragua"},
    "506": {"code": "es", "name": "Español", "flag": "🇨🇷", "country": "Costa Rica"},
    "507": {"code": "es", "name": "Español", "flag": "🇵🇦", "country": "Panamá"},
    "598": {"code": "es", "name": "Español", "flag": "🇺🇾", "country": "Uruguay"},
    # Rep. Dominicana (+1-809, +1-829, +1-849)
    "1809": {"code": "es", "name": "Español", "flag": "🇩🇴", "country": "Rep. Dominicana"},
    "1829": {"code": "es", "name": "Español", "flag": "🇩🇴", "country": "Rep. Dominicana"},
    "1849": {"code": "es", "name": "Español", "flag": "🇩🇴", "country": "Rep. Dominicana"},
    # Puerto Rico (+1-787, +1-939)
    "1787": {"code": "es", "name": "Español", "flag": "🇵🇷", "country": "Puerto Rico"},
    "1939": {"code": "es", "name": "Español", "flag": "🇵🇷", "country": "Puerto Rico"},

    # ==========================================
    # 2. ITALIANO: ITALIA
    # ==========================================
    "39": {"code": "it", "name": "Italiano", "flag": "🇮🇹", "country": "Italia"},

    # ==========================================
    # 3. COREANO: COREA DEL SUR
    # ==========================================
    "82": {"code": "ko", "name": "한국어", "flag": "🇰🇷", "country": "Corea del Sur"},

    # ==========================================
    # 4. POLACO: POLONIA
    # ==========================================
    "48": {"code": "pl", "name": "Polski", "flag": "🇵🇱", "country": "Polonia"},

    # ==========================================
    # 5. PORTUGUÉS: PORTUGAL Y BRASIL
    # ==========================================
    "351": {"code": "pt", "name": "Português", "flag": "🇵🇹", "country": "Portugal"},
    "55": {"code": "pt", "name": "Português", "flag": "🇧🇷", "country": "Brasil"},

    # ==========================================
    # 6. ALEMÁN: ALEMANIA, AUSTRIA, SUIZA
    # ==========================================
    "49": {"code": "de", "name": "Deutsch", "flag": "🇩🇪", "country": "Alemania"},
    "43": {"code": "de", "name": "Deutsch", "flag": "🇦🇹", "country": "Austria"},
    "41": {"code": "de", "name": "Deutsch", "flag": "🇨🇭", "country": "Suiza"},

    # ==========================================
    # 7. FRANCÉS: FRANCIA, BÉLGICA, MÓNACO
    # ==========================================
    "33": {"code": "fr", "name": "Français", "flag": "🇫🇷", "country": "Francia"},
    "32": {"code": "fr", "name": "Français", "flag": "🇧🇪", "country": "Bélgica"},
    "377": {"code": "fr", "name": "Français", "flag": "🇲🇨", "country": "Mónaco"},

    # ==========================================
    # 8. INGLÉS (ESPECÍFICOS Y RESTO DEL MUNDO)
    # ==========================================
    "44": {"code": "en", "name": "English", "flag": "🇬🇧", "country": "Reino Unido"},
    "353": {"code": "en", "name": "English", "flag": "🇮🇪", "country": "Irlanda"},
    "1": {"code": "en", "name": "English", "flag": "🇺🇸", "country": "USA / Canadá"},
    "61": {"code": "en", "name": "English", "flag": "🇦🇺", "country": "Australia"},
    "64": {"code": "en", "name": "English", "flag": "🇳🇿", "country": "Nueva Zelanda"},
    "31": {"code": "en", "name": "English", "flag": "🇳🇱", "country": "Países Bajos"},
    "46": {"code": "en", "name": "English", "flag": "🇸🇪", "country": "Suecia"},
    "47": {"code": "en", "name": "English", "flag": "🇳🇴", "country": "Noruega"},
    "45": {"code": "en", "name": "English", "flag": "🇩🇰", "country": "Dinamarca"},
    "358": {"code": "en", "name": "English", "flag": "🇫🇮", "country": "Finlandia"},
    "81": {"code": "en", "name": "English", "flag": "🇯🇵", "country": "Japón"},
    "86": {"code": "en", "name": "English", "flag": "🇨🇳", "country": "China"},
    "91": {"code": "en", "name": "English", "flag": "🇮🇳", "country": "India"},
    "971": {"code": "en", "name": "English", "flag": "🇦🇪", "country": "Emiratos Árabes"},
    "972": {"code": "en", "name": "English", "flag": "🇮🇱", "country": "Israel"},
    "30": {"code": "en", "name": "English", "flag": "🇬🇷", "country": "Grecia"},
    "420": {"code": "en", "name": "English", "flag": "🇨🇿", "country": "República Checa"},
    "36": {"code": "en", "name": "English", "flag": "🇭🇺", "country": "Hungría"},
    "40": {"code": "en", "name": "English", "flag": "🇷🇴", "country": "Rumanía"},
}

def clean_phone_number(phone: str) -> str:
    """Cleans phone string to digits only with leading '+'."""
    if not phone:
        return ""
    phone = str(phone).strip()
    if phone.startswith("00"):
        phone = "+" + phone[2:]
    
    has_plus = phone.startswith("+")
    digits = re.sub(r"[^\d]", "", phone)
    
    if not digits:
        return ""
    
    # Standard 9-digit Spanish number without prefix, assume +34
    if len(digits) == 9 and digits[0] in "6789":
        return f"+34{digits}"
        
    return f"+{digits}"

def detect_language(phone: str) -> Dict[str, Any]:
    """
    Detects user language from international phone prefix.
    - Español (es): España (+34) y todos los países hispanohablantes de Latinoamérica.
    - Italiano (it): Italia (+39).
    - Koreano (ko): Corea del Sur (+82).
    - Polaco (pl): Polonia (+48).
    - Portugués (pt): Portugal (+351) y Brasil (+55).
    - Alemán (de): Alemania (+49), Austria (+43), Suiza (+41).
    - Francés (fr): Francia (+33), Bélgica (+32), Mónaco (+377).
    - Resto de países del mundo: Inglés (en).
    """
    cleaned = clean_phone_number(phone)
    if not cleaned or not cleaned.startswith("+"):
        return {"code": "es", "name": "Español", "flag": "🇪🇸", "country": "España (por defecto)"}

    digits = cleaned[1:]

    # Check 4-digit prefixes first (e.g. 1809, 1787), then 3, 2, 1
    for length in (4, 3, 2, 1):
        if len(digits) >= length:
            prefix = digits[:length]
            if prefix in COUNTRY_PREFIX_MAP:
                return COUNTRY_PREFIX_MAP[prefix]

    # All other countries in the world default to English
    return {"code": "en", "name": "English", "flag": "🌐", "country": "Internacional (Inglés)"}
