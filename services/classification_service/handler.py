from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime
from typing import Any, Dict

import boto3


dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")

doc_table = dynamodb.Table(os.environ.get("DOCUMENTS_TABLE", "DocumentsTable"))
status_queue = os.environ.get("STATUS_QUEUE_URL", "demo-status-queue")
notification_queue = os.environ.get("NOTIFICATION_QUEUE_URL", "demo-notification-queue")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
ALLOWED_CATEGORIES = [
    "resume", "report", "article", "invoice", "contract",
    "letter", "certificate", "legal", "presentation", "manual", "form"
]


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    for record in event.get("Records", []):
        body = json.loads(record["body"])
        doc_id = body["documentId"]
        metadata = doc_table.get_item(Key={"documentId": doc_id}).get("Item", {})

        classification = classify_with_ai(metadata)
        if classification is None:
            classification = fallback_classification(metadata)

        doc_table.update_item(
            Key={"documentId": doc_id},
            UpdateExpression=(
                "SET category=:cat, subcategory=:sub, classificationStatus=:status, "
                "#docStatus=:finalStatus, updatedAt=:ts"
            ),
            ExpressionAttributeNames={"#docStatus": "status"},
            ExpressionAttributeValues={
                ":cat": classification["category"],
                ":sub": classification["subcategory"],
                ":status": "completed",
                ":finalStatus": "completed",
                ":ts": datetime.utcnow().isoformat(),
            },
        )

        status_event = {
            "documentId": doc_id,
            "status": "classification_completed",
            "message": f"Classified as {classification['category']}",
            "timestamp": int(datetime.utcnow().timestamp()),
        }
        sqs.send_message(QueueUrl=status_queue, MessageBody=json.dumps(status_event))
        sqs.send_message(
            QueueUrl=notification_queue,
            MessageBody=json.dumps({"documentId": doc_id, "status": "completed"}),
        )
    return {"statusCode": 200, "body": json.dumps({"message": "classification completed"})}


def classify_with_ai(metadata: Dict[str, Any]) -> Dict[str, str] | None:
    if not OPENAI_API_KEY:
        return None
    prompt = (
        "You must classify documents strictly into one of these categories:\n"
        + ", ".join(ALLOWED_CATEGORIES)
        + "\nReturn JSON with keys: category (from list above) and subcategory (more specific, e.g. 'cover_letter').\n"
        "Here is the metadata:\n"
        + json.dumps(metadata, ensure_ascii=False)
    )
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "You are a precise document classifier."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    try:
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            ai_result = json.loads(content)
            category = ai_result.get("category", "letter").lower()
            if category not in ALLOWED_CATEGORIES:
                category = "letter"
            sub = ai_result.get("subcategory", category)
            return {"category": category, "subcategory": sub}
    except Exception:
        return None


def fallback_classification(metadata: Dict[str, Any]) -> Dict[str, str]:
    title = metadata.get("title", "").lower()
    if any(keyword in title for keyword in ("resume", "cv")):
        return {"category": "resume", "subcategory": "resume"}
    if "invoice" in title:
        return {"category": "invoice", "subcategory": "invoice"}
    return {"category": "letter", "subcategory": "letter"}
