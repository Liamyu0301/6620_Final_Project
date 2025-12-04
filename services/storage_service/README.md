# Storage Service

Owns S3 bucket policies, lifecycle rules, and signed URL issuance. In the final system this service runs as an AWS Lambda exposed via API Gateway for clients that prefer uploading directly to S3.

Sample handler illustrates how to generate pre-signed URLs for PUT and GET operations.
