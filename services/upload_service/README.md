# Upload Service

Responsibilities:
- Receive signed-upload metadata from API Gateway.
- Persist raw files to S3 (`documents-bucket`).
- Emit an SQS message to the Extraction Service containing document ID, bucket, and key.

Key AWS resources:
- Lambda (Python 3.11)
- Amazon S3 (document storage)
- Amazon SQS (`document-extraction-queue`)

Environment variables:
- `DOCUMENTS_BUCKET`
- `EXTRACTION_QUEUE_URL`
- `STATUS_QUEUE_URL`

See `handler.py` for the minimal Lambda implementation.
