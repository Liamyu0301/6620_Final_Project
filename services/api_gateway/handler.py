"""Lightweight API Gateway router used for local testing."""
from __future__ import annotations

import json
from typing import Any, Dict


ROUTES = {
    ("POST", "/documents"): "upload_service",
    ("GET", "/search"): "search_service",
    ("GET", "/status/{id}"): "status_service",
}


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "GET")
    path = event.get("resource", event.get("path", "/"))

    target = ROUTES.get((method, path))
    if not target:
        return {
            "statusCode": 404,
            "body": json.dumps({"message": "Route not found"}),
        }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Request accepted",
            "target_service": target,
        }),
    }
