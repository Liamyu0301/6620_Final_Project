from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict

import boto3

dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")

table = dynamodb.Table(os.environ.get("DOCUMENTS_TABLE", "DocumentsTable"))
classification_queue = os.environ.get("CLASSIFICATION_QUEUE_URL", "demo-classification-queue")


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    processed = 0
    for record in event.get("Records", []):
        body = json.loads(record["body"])
        doc_id = body["documentId"]

        existing = table.get_item(Key={"documentId": doc_id}).get("Item", {})
        merged: Dict[str, Any] = {**existing, **body}
        merged["documentId"] = doc_id
        merged.setdefault("filename", existing.get("filename"))

        if not merged.get("fileType") and merged.get("filename"):
            merged["fileType"] = merged["filename"].rsplit(".", 1)[-1].lower()

        merged["status"] = body.get("status", "extraction_completed")
        merged["extractionStatus"] = body.get("extractionStatus", "completed")
        merged["updatedAt"] = datetime.utcnow().isoformat()

        table.put_item(Item=merged)
        sqs.send_message(QueueUrl=classification_queue, MessageBody=json.dumps({"documentId": doc_id}))
        processed += 1
    return {"statusCode": 200, "body": json.dumps({"processed": processed})}
