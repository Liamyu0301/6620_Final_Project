from __future__ import annotations

import json
import os
from typing import Any, Dict

import boto3

s3 = boto3.client("s3")
BUCKET = os.environ.get("DOCUMENTS_BUCKET", "demo-docs")


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    action = event.get("queryStringParameters", {}).get("action", "put")
    key = event.get("queryStringParameters", {}).get("key", "demo.pdf")

    params = {"Bucket": BUCKET, "Key": key}
    if action == "put":
        url = s3.generate_presigned_url("put_object", Params=params, ExpiresIn=900)
    else:
        url = s3.generate_presigned_url("get_object", Params=params, ExpiresIn=900)

    return {"statusCode": 200, "body": json.dumps({"url": url, "action": action})}
