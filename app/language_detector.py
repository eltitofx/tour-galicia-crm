import re
from typing import Dict, Any

COUNTRY_PREFIX_MAP = {
    # Spain
    "34": {"code": "es", "name": "Español", "flag": "🇪🇸", "country": "España"},
    # Portugal & Brazil
    "351": {"code": "pt", "name": "Português", "flag": "🇵🇹", "country": "Portugal"},
    "55": {"code": "pt", "name": "Português", "flag": "🇧🇷", "country": "Brasil"},
    # France & Belgium
    "33": {"code": "fr", "name": "Français", "flag": "🇫🇷", "country": "France"},
    "32": {"code": "fr", "name": "Français", "flag": "🇧🇪", "country": "Belgique"},
    # Germany, Austria, Switzerland
    "49": {"code": "de", "name": "Deutsch", "flag": "🇩🇪", "country": "Deutschland"},
    "43": {"code": "de", "name": "Deutsch", "flag": "🇦🇹", "country": "Österreich"},
    "41": {"code": "de", "name": "Deutsch", "flag": "🇨🇭", "country": "Schweiz"},
    # Italy
    "39": {"code": "it", "name": "Italiano", "flag": "🇮🇹", "country": "Italia"},
    # UK & Ireland
    "44": {"code": "en", "name": "English", "flag": "🇬🇧", "country": "United Kingdom"},
    "353": {"code": "en", "name": "English", "flag": "🇮🇪", "country": "Ireland"},
    # US & Canada
    "1": {"code": "en", "name": "English", "flag": "🇺🇸", "country": "USA / Canada"},
    # Australia & New Zealand
    "61": {"code": "en", "name": "English", "flag": "🇦🇺", "country": "Australia"},
    "64": {"code": "en", "name": "English", "flag": "🇳🇿", "country": "New Zealand"},
    # Netherlands (English default)
    "31": {"code": "en", "name": "English", "flag": "🇳🇱", "country": "Netherlands"},
}

def clean_phone_number(phone: str) -> str:
    """Cleans phone string to digits only with optional leading '+'."""
    if not phone:
        return ""
    phone = phone.strip()
    # Replace common 00 prefix with +
    if phone.startswith("00"):
        phone = "+" + phone[2:]
    
    has_plus = phone.startswith("+")
    digits = re.sub(r"[^\d]", "", phone)
    
    if not digits:
        return ""
    
    # If standard 9-digit Spanish number without prefix, assume +34
    if len(digits) == 9 and digits[0] in "6789":
        return f"+34{digits}"
        
    return f"+{digits}" if has_plus or len(digits) > 9 else f"+{digits}"

def detect_language(phone: str) -> Dict[str, Any]:
    """
    Detects user language from international phone prefix.
    Returns language code, display name, flag, and country.
    Defaults to 'es' for Spanish numbers, 'en' for other foreign countries.
    """
    cleaned = clean_phone_number(phone)
    if not cleaned or not cleaned.startswith("+"):
        return {"code": "es", "name": "Español", "flag": "🇪🇸", "country": "España (por defecto)"}

    # Extract digits without plus
    digits = cleaned[1:]

    # Check 3-digit prefixes first (e.g. 351, 353)
    for length in (3, 2, 1):
        if len(digits) >= length:
            prefix = digits[:length]
            if prefix in COUNTRY_PREFIX_MAP:
                return COUNTRY_PREFIX_MAP[prefix]

    # Fallback for unknown international numbers: English
    return {"code": "en", "name": "English", "flag": "🌐", "country": "Internacional (Inglés)"}
