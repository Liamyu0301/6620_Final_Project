from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List

import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("DOCUMENTS_TABLE", "DocumentsTable"))

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "OPTIONS,GET",
}


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    try:
        params = event.get("queryStringParameters") or {}
        query = (params.get("q") or params.get("query") or "").strip().lower()
        category_filter = (params.get("category") or "").strip().lower()
        type_filter = (params.get("type") or "").strip().lower()
        status_filter = (params.get("status") or "").strip().lower()
        limit = min(int(params.get("limit") or 50), 200)

        items = _scan_all_items()
        filtered: List[Dict[str, Any]] = []
        for item in items:
            if not _matches_query(item, query):
                continue
            if category_filter and item.get("category", "").lower() != category_filter:
                continue
            if type_filter and _extract_file_type(item) != type_filter:
                continue
            if status_filter and _extract_status(item) != status_filter:
                continue
            filtered.append(item)

        sorted_results = sorted(
            filtered,
            key=lambda x: _to_datetime(x.get("updatedAt") or x.get("uploadTimestamp")),
            reverse=True,
        )

        return _response(
            200,
            {
                "results": sorted_results[:limit],
                "count": len(sorted_results[:limit]),
                "query": query,
                "filters": {
                    "category": category_filter,
                    "type": type_filter,
                    "status": status_filter,
                },
            },
        )
    except Exception as err:
        return _response(500, {"message": str(err)})


def _scan_all_items() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    kwargs: Dict[str, Any] = {}
    while True:
        resp = table.scan(**kwargs)
        items.extend(resp.get("Items", []))
        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break
        kwargs["ExclusiveStartKey"] = last_key
    return items


def _matches_query(item: Dict[str, Any], query: str) -> bool:
    if not query:
        return True
    haystack = " ".join(
        filter(
            None,
            [
                item.get("title", ""),
                item.get("summary", ""),
                item.get("filename", ""),
                item.get("documentType", ""),
            ],
        )
    ).lower()
    return query in haystack


def _extract_file_type(item: Dict[str, Any]) -> str:
    file_type = (item.get("fileType") or "").lower()
    if file_type:
        return file_type
    filename = item.get("filename") or ""
    if "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return ""


def _extract_status(item: Dict[str, Any]) -> str:
    for key in ("status", "classificationStatus", "extractionStatus"):
        value = (item.get(key) or "").lower()
        if value:
            return value
    return ""


def _to_datetime(value: Any) -> datetime:
    if not value:
        return datetime.min
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value))
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.fromtimestamp(float(value))
    except Exception:
        return datetime.min
    return datetime.min


def _response(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, default=str),
    }
