from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import boto3

# Import authentication utilities
from auth_utils import get_user_from_token


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("STATUS_TABLE", "StatusTable"))

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
}


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    try:
        if event.get("httpMethod") == "GET":
            return handle_get(event)

        processed = 0
        for record in event.get("Records", []):
            body = json.loads(record.get("body", "{}"))
            table.put_item(
                Item={
                    "documentId": body.get("documentId"),
                    "timestamp": body.get("timestamp"),
                    "status": body.get("status"),
                    "message": body.get("message"),
                }
            )
            processed += 1
        return response(200, {"message": "recorded", "count": processed})

    except Exception as err:
        return response(500, {"message": str(err)})


def handle_get(event: Dict[str, Any]) -> Dict[str, Any]:
    # Verify user identity
    headers = event.get("headers") or {}
    auth_header = headers.get("Authorization") or headers.get("authorization", "")
    user_info = get_user_from_token(auth_header)
    if not user_info:
        return response(401, {"message": "Unauthorized, please login first"})

    user_id = user_info.get("userId")

    doc_id = event.get("pathParameters", {}).get("id")
    if not doc_id:
        return response(400, {"message": "Missing id"})

    # Verify document ownership (need to query Documents table)
    documents_table = boto3.resource("dynamodb").Table(
        os.environ.get("DOCUMENTS_TABLE", "DocumentsTable")
    )
    doc_response = documents_table.get_item(Key={"documentId": doc_id})
    if "Item" not in doc_response:
        return response(404, {"message": "Document not found"})

    document = doc_response["Item"]
    if document.get("userId") != user_id:
        return response(403, {"message": "Access denied to this document"})

    items = table.query(
        KeyConditionExpression="documentId = :doc",
        ExpressionAttributeValues={":doc": doc_id},
    ).get("Items", [])
    items.sort(key=lambda x: x.get("timestamp", 0))
    return response(200, {"history": items}, default=str)


def response(status: int, body: Dict[str, Any], default=None) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, default=default),
    }
