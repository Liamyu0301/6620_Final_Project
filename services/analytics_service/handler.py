from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict

import boto3

dynamodb = boto3.resource("dynamodb")
doc_table = dynamodb.Table(os.environ.get("DOCUMENTS_TABLE", "DocumentsTable"))
analytics_table = dynamodb.Table(os.environ.get("ANALYTICS_TABLE", "AnalyticsTable"))


def lambda_handler(_event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    items = doc_table.scan().get("Items", [])
    total = len(items)
    completed = sum(1 for item in items if item.get("status") == "completed")
    analytics_table.put_item(
        Item={
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "totalDocuments": total,
            "completedDocuments": completed,
        }
    )
    return {"statusCode": 200, "body": json.dumps({"total": total, "completed": completed})}
