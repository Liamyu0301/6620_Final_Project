# Download Service

Generates presigned URLs for file downloads, ensuring users can only download their own files.

## Features

- Verify user identity
- Verify document ownership
- Generate S3 presigned download URLs

## API Endpoints

### GET /download?documentId={id}
Get file download URL

Request headers:
```
Authorization: Bearer {token}
```

Response:
```json
{
  "downloadUrl": "https://...",
  "documentId": "xxx",
  "filename": "document.pdf",
  "expiresIn": 900
}
```

## Environment Variables

- `DOCUMENTS_BUCKET`: S3 bucket name
- `DOCUMENTS_TABLE`: DynamoDB documents table name

