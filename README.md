# Smart Document Processing & Retrieval System

Our team is rebuilding a cloud-native Smart Document Processing & Retrieval System on AWS. The new implementation keeps the architecture lightweight while satisfying the requirement of 8–12 microservices. Users can upload documents to S3, Lambdas orchestrate AI-powered metadata extraction, DynamoDB persists searchable entries, and Amazon SNS/API Gateway provide user notifications and APIs.

## Guiding Principles
- **Cloud-Native & Serverless**: Prefer managed services (Lambda, S3, DynamoDB, SNS, API Gateway).
- **Loose Coupling**: Each microservice owns a small responsibility and communicates through SQS/SNS or API Gateway.
- **AI-Augmented Extraction**: A dedicated AI agent Lambda handles metadata extraction and summarization, leaving traditional OCR optional.
- **Observability & Simplicity**: Shared logging/analytics service aggregates CloudWatch metrics into DynamoDB for quick inspection.

## Repository Structure
```
├── README.md
├── docs/
│   ├── architecture_overview.md
│   └── deployment_plan.md
├── services/
│   ├── api_gateway/
│   ├── upload_service/
│   ├── storage_service/
│   ├── extraction_service/
│   ├── metadata_service/
│   ├── classification_service/
│   ├── search_service/
│   ├── notification_service/
│   ├── status_service/
│   └── analytics_service/
└── infra/
    └── README.md
```

Each service contains a minimal Lambda-style handler plus a README explaining its contract with other services. The `docs/` folder captures the high-level architecture and deployment strategy, while `infra/` documents how CDK stacks should be organized.

## Quick Start (Conceptual)
1. **Upload**: Client uploads through API Gateway → `upload_service` stores file in S3 and enqueues work.
2. **Extraction**: `extraction_service` downloads the file, calls the AI agent, and saves metadata via `metadata_service`.
3. **Classification**: `classification_service` enriches metadata and posts results to DynamoDB.
4. **Search**: `search_service` exposes query APIs powered by DynamoDB Global Secondary Indexes.
5. **Notification**: `notification_service` publishes SNS messages when processing is complete.
6. **Status & Analytics**: `status_service` tracks lifecycle events; `analytics_service` aggregates metrics for dashboards.

The sample handlers illustrate payload formats and AWS SDK usage patterns that the real system will follow once the infrastructure is provisioned.
