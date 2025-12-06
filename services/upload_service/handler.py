"""Simplified upload handler."""

from __future__ import annotations

import base64
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict

import boto3
import mimetypes

# Import authentication utilities
from auth_utils import get_user_from_token

s3 = boto3.client("s3")
sqs = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")

DOC_BUCKET = os.environ.get("DOCUMENTS_BUCKET", "demo-docs")
EXTRACTION_QUEUE = os.environ.get("EXTRACTION_QUEUE_URL", "demo-queue")
DOCUMENTS_TABLE = dynamodb.Table(os.environ.get("DOCUMENTS_TABLE", "DocumentsTable"))

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
}


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    # Verify user identity
    headers = event.get("headers") or {}
    auth_header = headers.get("Authorization") or headers.get("authorization", "")
    user_info = get_user_from_token(auth_header)
    if not user_info:
        return _response(401, {"message": "Unauthorized, please login first"})

    user_id = user_info.get("userId")

    body = json.loads(event.get("body") or "{}")
    file_content = body.get("base64File")
    filename = body.get("filename", "document.pdf")
    if not file_content:
        return _response(400, {"message": "base64File required"})

    try:
        binary_body = base64.b64decode(file_content)
    except Exception:
        return _response(400, {"message": "Invalid base64File"})

    document_id = str(uuid.uuid4())
    object_key = f"uploads/{document_id}/{filename}"
    s3.put_object(Bucket=DOC_BUCKET, Key=object_key, Body=binary_body)

    upload_timestamp = datetime.utcnow().isoformat()
    file_extension = (
        filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
    )
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    DOCUMENTS_TABLE.put_item(
        Item={
            "documentId": document_id,
            "userId": user_id,  # Associate with user ID
            "status": "pending_extraction",
            "filename": filename,
            "fileType": file_extension,
            "contentType": content_type,
            "uploadTimestamp": upload_timestamp,
        }
    )

    message = {
        "documentId": document_id,
        "bucket": DOC_BUCKET,
        "key": object_key,
        "uploadedAt": upload_timestamp,
        "filename": filename,
    }
    sqs.send_message(QueueUrl=EXTRACTION_QUEUE, MessageBody=json.dumps(message))

    return _response(202, {"documentId": document_id, "status": "queued"})


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body),
    }
