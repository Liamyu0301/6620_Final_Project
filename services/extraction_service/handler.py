from __future__ import annotations

import base64
import io
import json
import os
import sys
import zipfile
import urllib.request
from pathlib import Path
from typing import Any, Dict

import boto3

sys.path.append(str(Path(__file__).resolve().parent / "lib"))
from PyPDF2 import PdfReader  # type: ignore

s3 = boto3.client("s3")
sqs = boto3.client("sqs")

BUCKET = os.environ.get("DOCUMENTS_BUCKET", "demo-docs")
METADATA_QUEUE = os.environ.get("METADATA_QUEUE_URL", "demo-metadata-queue")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    processed = 0
    for record in event.get("Records", []):
        body = json.loads(record["body"])
        key = body["key"]
        doc_id = body["documentId"]
        filename = body.get("filename", key.split("/")[-1])

        obj = s3.get_object(Bucket=BUCKET, Key=key)
        content_bytes = obj["Body"].read()
        text_snippet = extract_text(content_bytes, filename)

        metadata = _extract_metadata_with_ai(text_snippet, filename, doc_id)
        sqs.send_message(QueueUrl=METADATA_QUEUE, MessageBody=json.dumps(metadata))
        processed += 1

    return {"statusCode": 200, "body": json.dumps({"processed": processed})}


def extract_text(data: bytes, filename: str) -> str:
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    try:
        if ext == 'pdf':
            reader = PdfReader(io.BytesIO(data))
            text = "\n".join(page.extract_text() or '' for page in reader.pages)
            if text.strip():
                return text
        elif ext in ('docx', 'doc'):
            return extract_docx_text(data)
        elif ext in ('txt', 'csv'):
            return data.decode('utf-8', errors='ignore')
    except Exception:
        pass
    return _bytes_to_text(data)


def extract_docx_text(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as doc:
            xml_content = doc.read('word/document.xml')
        from xml.etree.ElementTree import XML
        tree = XML(xml_content)
        paragraphs = []
        for node in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if node.text:
                paragraphs.append(node.text)
        return '\n'.join(paragraphs)
    except Exception:
        return _bytes_to_text(data)


def _bytes_to_text(data: bytes, limit: int = 6000) -> str:
    try:
        return data.decode('utf-8', errors='ignore')[:limit]
    except UnicodeDecodeError:
        return base64.b64encode(data[:limit]).decode()


def _extract_metadata_with_ai(text: str, filename: str, doc_id: str) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        return _mock_metadata(text, filename, doc_id)

    prompt = (
        "You receive plain text extracted from a user document. "
        "Return JSON with keys: title (string), summary (string), documentType (string), keywords (array of strings)."\
        "Focus on the real content and keep summary under 120 words.\n\nTEXT:\n" + text[:6000]
    )
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "You extract metadata for document management systems."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
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
            ai_metadata = json.loads(content)
            return {
                "documentId": doc_id,
                "title": filename.rsplit(".", 1)[0],
                "summary": ai_metadata.get("summary", text[:200]),
                "documentType": ai_metadata.get("documentType", ext_from_filename(filename)),
                "keywords": ai_metadata.get("keywords", []),
                "extractionStatus": "completed",
            }
    except Exception:
        return _mock_metadata(text, filename, doc_id)


def ext_from_filename(filename: str) -> str:
    return filename.rsplit('.', 1)[-1] if '.' in filename else 'document'


def _mock_metadata(text: str, filename: str, doc_id: str) -> Dict[str, Any]:
    snippet = text[:400] if text else filename
    return {
        "documentId": doc_id,
        "title": filename.rsplit('.', 1)[0],
        "summary": snippet,
        "documentType": ext_from_filename(filename),
        "keywords": [],
        "extractionStatus": "completed",
    }
