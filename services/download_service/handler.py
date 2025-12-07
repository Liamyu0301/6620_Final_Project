"""File download service: generate presigned URLs"""
from __future__ import annotations

import json
import os
from typing import Any, Dict

import boto3

# Import authentication utilities
from auth_utils import get_user_from_token

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

BUCKET = os.environ.get("DOCUMENTS_BUCKET", "demo-docs")
DOCUMENTS_TABLE = dynamodb.Table(os.environ.get("DOCUMENTS_TABLE", "DocumentsTable"))

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "OPTIONS,GET",
}


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    """Handle file download requests"""
    if event.get("httpMethod") == "OPTIONS":
        return _response(200, {})

    try:
        # Get authentication token
        headers = event.get("headers") or {}
        auth_header = headers.get("Authorization") or headers.get("authorization", "")
        
        user_info = get_user_from_token(auth_header)
        if not user_info:
            return _response(401, {"message": "Unauthorized, please login first"})

        user_id = user_info.get("userId")
        
        # Get document ID
        params = event.get("queryStringParameters") or {}
        document_id = params.get("documentId") or params.get("id")
        
        if not document_id:
            return _response(400, {"message": "Missing documentId parameter"})

        # Verify document ownership
        doc_response = DOCUMENTS_TABLE.get_item(Key={"documentId": document_id})
        if "Item" not in doc_response:
            return _response(404, {"message": "Document not found"})

        document = doc_response["Item"]
        doc_user_id = document.get("userId")
        
        if doc_user_id != user_id:
            return _response(403, {"message": "Access denied to this document"})

        # Build S3 object key
        filename = document.get("filename", "document")
        object_key = f"uploads/{document_id}/{filename}"

        # Generate presigned URL (15 minutes expiration)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET, "Key": object_key},
            ExpiresIn=900,  # 15 minutes
        )

        return _response(200, {
            "downloadUrl": url,
            "documentId": document_id,
            "filename": filename,
            "expiresIn": 900,
        })
    except Exception as e:
        return _response(500, {"message": f"Download failed: {str(e)}"})


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, ensure_ascii=False),
    }

