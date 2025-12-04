# Extraction Service

Downloads raw documents from S3, calls an AI agent for metadata extraction, and sends normalized metadata to the Metadata Service.

Environment variables:
- `DOCUMENTS_BUCKET`
- `METADATA_QUEUE_URL`
- `OPENAI_API_KEY` (optional; falls back to heuristic mock mode)
