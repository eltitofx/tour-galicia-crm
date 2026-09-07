import hmac
import hashlib
import time
import base64
import json
from typing import Optional, Dict, Any
from app.config import ADMIN_USERNAME, ADMIN_PASSWORD, AUTH_SECRET_KEY

class AuthService:
    def __init__(self):
        self.username = ADMIN_USERNAME
        self.password = ADMIN_PASSWORD
        self.secret_key = AUTH_SECRET_KEY.encode("utf-8")
        # Token validity in seconds (7 days)
        self.token_expiry = 7 * 24 * 3600

    def verify_credentials(self, username: str, password: str) -> bool:
        """Verifies admin username (case-insensitive) and exact password."""
        if not username or not password:
            return False
        user_match = username.strip().lower() == self.username.strip().lower()
        pwd_match = password == self.password
        return user_match and pwd_match

    def create_token(self, username: str) -> str:
        """Generates a secure signed token with expiration timestamp."""
        payload = {
            "user": username.strip(),
            "exp": int(time.time()) + self.token_expiry,
            "created_at": int(time.time())
        }
        raw_json = json.dumps(payload).encode("utf-8")
        b64_payload = base64.urlsafe_b64encode(raw_json).decode("utf-8").rstrip("=")
        
        signature = hmac.new(self.secret_key, b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{b64_payload}.{signature}"

    def verify_token(self, token: Optional[str]) -> Optional[Dict[str, Any]]:
        """Validates token integrity, signature, and expiration."""
        if not token:
            return None
        
        token = token.replace("Bearer ", "").strip()
        parts = token.split(".")
        if len(parts) != 2:
            return None
        
        b64_payload, signature = parts
        expected_sig = hmac.new(self.secret_key, b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        try:
            # Add padding back if necessary
            padding = len(b64_payload) % 4
            if padding:
                b64_payload += "=" * (4 - padding)
            raw_json = base64.urlsafe_b64decode(b64_payload.encode("utf-8"))
            payload = json.loads(raw_json.decode("utf-8"))
            
            # Check expiration
            if payload.get("exp", 0) < time.time():
                return None
            
            return payload
        except Exception:
            return None

auth_service = AuthService()
