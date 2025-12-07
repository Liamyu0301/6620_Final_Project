"""Shared authentication utility functions"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from typing import Any, Dict

JWT_SECRET = os.environ.get("JWT_SECRET", "default-secret-key-change-in-production")


def verify_jwt(token: str) -> Dict[str, Any] | None:
    """Verify JWT token and return user information"""
    if not token:
        return None
    
    # Remove Bearer prefix
    if token.startswith("Bearer "):
        token = token[7:]
    
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        
        # Decode payload
        payload_b64 = parts[1]
        # Add padding
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        
        payload_json = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_json)
        
        # Check expiration time
        exp = payload.get("exp", 0)
        if exp < int(time.time()):
            return None
        
        # Verify signature (simplified version)
        message = f"{parts[0]}.{parts[1]}"
        expected_sig = hashlib.sha256(f"{message}.{JWT_SECRET}".encode()).hexdigest()[:32]
        if parts[2] != expected_sig:
            return None
        
        return payload
    except Exception:
        return None


def get_user_from_token(auth_header: str) -> Dict[str, Any] | None:
    """Extract user information from Authorization header"""
    if not auth_header:
        return None
    
    return verify_jwt(auth_header)
