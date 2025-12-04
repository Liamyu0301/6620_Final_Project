# Deployment Plan

## Prerequisites
- AWS CDK v2 installed locally (`npm install -g aws-cdk`).
- Python 3.11 runtime for authoring Lambda functions.
- AWS account with permissions to create IAM roles, S3 buckets, DynamoDB tables, SQS queues, and SNS topics.

## Environments
| Env | Account | Region | Notes |
| --- | --- | --- | --- |
| `dev` | 031988646272 | us-east-1 | Default developer sandbox |
| `prod` | TBD | us-east-1 | Promote CDK stacks once dev stabilizes |

## Stack Breakdown
1. **StorageStack** – Provisions S3 buckets, DynamoDB tables, and shared IAM roles.
2. **QueueStack** – Owns SQS queues & DLQs for upload, extraction, classification, status, analytics.
3. **NotificationStack** – SNS topics + subscriptions.
4. **UploadStack** – Lambda for upload workflow; depends on Storage & Queue stacks.
5. **ExtractionStack** – AI extraction Lambda + IAM policies + scheduling alarms.
6. **ClassificationStack** – Classification Lambda + tagging configuration.
7. **SearchStack** – Search API Lambdas & API Gateway resources.
8. **TrackerStack** – Status history writer Lambda.
9. **AnalyticsStack** – Metrics aggregation Lambda & scheduled EventBridge rule.
10. **ApiStack** – Consolidated API Gateway deployment (REST + WebSocket endpoints).

## Deployment Steps
```bash
# 1. Bootstrap the environment once
cd infra/cdk
cdk bootstrap aws://031988646272/us-east-1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Deploy foundation stacks
cdk deploy SmartDocProcessingStorageStack SmartDocProcessingQueueStack SmartDocProcessingNotificationStack

# 4. Deploy compute stacks
cdk deploy SmartDocProcessingUploadStack SmartDocProcessingExtractionStack SmartDocProcessingClassificationStack
cdk deploy SmartDocProcessingTrackerStack SmartDocProcessingSearchStack SmartDocProcessingAnalyticsStack SmartDocProcessingApiStack

# 5. Configure post-deploy resources
# - Attach S3 event notifications for upload bucket → Upload Lambda
# - Subscribe email/webhook endpoints to SNS topic
# - Configure API Gateway custom domain if needed
```

## Rollback Strategy
- CDK stack tags ensure dependencies can be destroyed in reverse order (API → Analytics → ... → Storage).
- S3 buckets enable “auto delete objects” custom resources for clean teardown.
- DynamoDB backups enabled daily; manual restore script documented separately.
