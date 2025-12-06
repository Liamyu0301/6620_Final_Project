"""User authentication service: registration, login, JWT generation"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from typing import Any, Dict

import boto3

dynamodb = boto3.resource("dynamodb")
users_table = dynamodb.Table(os.environ.get("USERS_TABLE", "UsersTable"))
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_urlsafe(32))

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
}


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    """Handle authentication requests"""
    method = event.get("httpMethod", "POST")
    path = event.get("path", "")

    if method == "OPTIONS":
        return _response(200, {})

    try:
        body = json.loads(event.get("body") or "{}")
        
        if path.endswith("/register") or body.get("action") == "register":
            return handle_register(body)
        elif path.endswith("/login") or body.get("action") == "login":
            return handle_login(body)
        else:
            return _response(400, {"message": "Invalid action. Use 'register' or 'login'"})
    except Exception as e:
        return _response(500, {"message": str(e)})


def handle_register(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle user registration"""
    username = body.get("username", "").strip()
    password = body.get("password", "").strip()
    email = body.get("email", "").strip()

    if not username or not password:
        return _response(400, {"message": "Username and password are required"})

    if len(password) < 6:
        return _response(400, {"message": "Password must be at least 6 characters"})

    # Check if user already exists
    try:
        response = users_table.get_item(Key={"username": username})
        if "Item" in response:
            return _response(409, {"message": "Username already exists"})
    except Exception:
        pass

    # Create new user
    password_hash = _hash_password(password)
    user_id = secrets.token_urlsafe(16)
    
    users_table.put_item(
        Item={
            "username": username,
            "userId": user_id,
            "email": email or "",
            "passwordHash": password_hash,
            "createdAt": int(time.time()),
        }
    )

    # Generate JWT token
    token = _generate_jwt(user_id, username)
    
    return _response(201, {
        "message": "Registration successful",
        "token": token,
        "userId": user_id,
        "username": username,
    })


def handle_login(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle user login"""
    username = body.get("username", "").strip()
    password = body.get("password", "").strip()

    if not username or not password:
        return _response(400, {"message": "Username and password are required"})

    # Find user
    try:
        response = users_table.get_item(Key={"username": username})
        if "Item" not in response:
            return _response(401, {"message": "Invalid username or password"})
        
        user = response["Item"]
        password_hash = user.get("passwordHash")
        
        # Verify password
        if not _verify_password(password, password_hash):
            return _response(401, {"message": "Invalid username or password"})

        # Generate JWT token
        token = _generate_jwt(user["userId"], username)
        
        return _response(200, {
            "message": "Login successful",
            "token": token,
            "userId": user["userId"],
            "username": username,
        })
    except Exception as e:
        return _response(500, {"message": f"Login failed: {str(e)}"})


def _hash_password(password: str) -> str:
    """Hash password using SHA256 (production should use bcrypt)"""
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify password"""
    return _hash_password(password) == password_hash


def _generate_jwt(user_id: str, username: str) -> str:
    """Generate simple JWT token (production should use jwt library)"""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "userId": user_id,
        "username": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400 * 7,  # 7 days expiration
    }
    
    # Simple base64 encoding (should use jwt library in production)
    import base64
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    
    # Generate signature
    message = f"{header_b64}.{payload_b64}"
    signature = hashlib.sha256(f"{message}.{JWT_SECRET}".encode()).hexdigest()[:32]
    
    return f"{header_b64}.{payload_b64}.{signature}"


def _verify_jwt(token: str) -> Dict[str, Any] | None:
    """Verify JWT token"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        
        import base64
        payload_json = base64.urlsafe_b64decode(parts[1] + "==")
        payload = json.loads(payload_json)
        
        # Check expiration time
        if payload.get("exp", 0) < int(time.time()):
            return None
        
        return payload
    except Exception:
        return None


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, ensure_ascii=False),
    }


# Export verification function for other services
def get_user_from_token(token: str) -> Dict[str, Any] | None:
    """Extract user information from token"""
    if not token:
        return None
    
    # Remove Bearer prefix
    if token.startswith("Bearer "):
        token = token[7:]
    
    return _verify_jwt(token)

