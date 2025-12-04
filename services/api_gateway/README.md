# API Gateway Service

- Exposes REST endpoints for upload, search, and status queries.
- Validates request payloads and injects tenant/user context.
- Routes traffic to downstream Lambdas via AWS Lambda integrations.

## Endpoints (conceptual)
| Method | Path | Lambda Target |
| --- | --- | --- |
| POST | /documents | upload_service |
| GET | /documents/{id} | metadata_service |
| GET | /search | search_service |
| GET | /status/{id} | status_service |

## Environment Variables
- `UPLOAD_SERVICE_ARN`
- `SEARCH_SERVICE_ARN`
- `STATUS_SERVICE_ARN`

## Sample Event Handler
See `handler.py` for a lightweight router implementation used in local testing.
