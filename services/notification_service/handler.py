from __future__ import annotations

import json
import os
from typing import Any, Dict

import boto3

sns = boto3.client("sns")
TOPIC_ARN = os.environ.get("NOTIFICATION_TOPIC_ARN", "demo-topic")


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    notified = 0
    for record in event.get("Records", []):
        body = json.loads(record.get("body", "{}"))
        sns.publish(TopicArn=TOPIC_ARN, Message=json.dumps(body), Subject="Document Update")
        notified += 1
    return {"statusCode": 200, "body": json.dumps({"notified": notified})}
