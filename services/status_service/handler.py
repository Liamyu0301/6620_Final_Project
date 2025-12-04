from __future__ import annotations

import json
import os
from typing import Any, Dict

import boto3


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
            table.put_item(Item={
                "documentId": body.get("documentId"),
                "timestamp": body.get("timestamp"),
                "status": body.get("status"),
                "message": body.get("message"),
            })
            processed += 1
        return response(200, {"message": "recorded", "count": processed})

    except Exception as err:
        return response(500, {"message": str(err)})


def handle_get(event: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = event.get("pathParameters", {}).get("id")
    if not doc_id:
        return response(400, {"message": "Missing id"})

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
