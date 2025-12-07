from __future__ import annotations

import os
from pathlib import Path

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_events,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_sns as sns,
    aws_sqs as sqs,
)
from constructs import Construct

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


class SmartDocProcessingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        base_dir = Path(__file__).resolve().parents[3]
        services_dir = base_dir / "services"
        frontend_dir = base_dir / "frontend"

        documents_bucket = s3.Bucket(
            self,
            "DocumentsBucket",
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        documents_table = dynamodb.Table(
            self,
            "DocumentsTable",
            partition_key=dynamodb.Attribute(
                name="documentId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        status_table = dynamodb.Table(
            self,
            "StatusTable",
            partition_key=dynamodb.Attribute(
                name="documentId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        users_table = dynamodb.Table(
            self,
            "UsersTable",
            partition_key=dynamodb.Attribute(
                name="username", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        frontend_bucket = s3.Bucket(
            self,
            "FrontendBucket",
            website_index_document="index.html",
            website_error_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        extraction_queue = sqs.Queue(
            self,
            "ExtractionQueue",
            visibility_timeout=Duration.minutes(5),
        )
        metadata_queue = sqs.Queue(
            self, "MetadataQueue", visibility_timeout=Duration.minutes(5)
        )
        classification_queue = sqs.Queue(
            self,
            "ClassificationQueue",
            visibility_timeout=Duration.minutes(5),
        )
        notification_queue = sqs.Queue(
            self,
            "NotificationQueue",
            visibility_timeout=Duration.minutes(1),
        )
        status_queue = sqs.Queue(
            self,
            "StatusEventQueue",
            visibility_timeout=Duration.minutes(1),
        )

        notification_topic = sns.Topic(self, "NotificationTopic")

        def service_code(path: str) -> lambda_.Code:
            return lambda_.Code.from_asset(str(services_dir / path))

        def build_lambda(
            id_: str,
            path: str,
            env: dict[str, str],
            timeout: Duration = Duration.seconds(60),
        ) -> lambda_.Function:
            fn = lambda_.Function(
                self,
                id_,
                runtime=lambda_.Runtime.PYTHON_3_11,
                handler="handler.lambda_handler",
                code=service_code(path),
                timeout=timeout,
                environment=env,
            )
            return fn

        upload_lambda = build_lambda(
            "UploadFunction",
            "upload_service",
            {
                "DOCUMENTS_BUCKET": documents_bucket.bucket_name,
                "EXTRACTION_QUEUE_URL": extraction_queue.queue_url,
                "DOCUMENTS_TABLE": documents_table.table_name,
            },
        )

        extraction_lambda = build_lambda(
            "ExtractionFunction",
            "extraction_service",
            {
                "DOCUMENTS_BUCKET": documents_bucket.bucket_name,
                "METADATA_QUEUE_URL": metadata_queue.queue_url,
                "OPENAI_API_KEY": OPENAI_API_KEY,
            },
            timeout=Duration.minutes(5),
        )

        metadata_lambda = build_lambda(
            "MetadataFunction",
            "metadata_service",
            {
                "DOCUMENTS_TABLE": documents_table.table_name,
                "CLASSIFICATION_QUEUE_URL": classification_queue.queue_url,
            },
        )

        classification_lambda = build_lambda(
            "ClassificationFunction",
            "classification_service",
            {
                "DOCUMENTS_TABLE": documents_table.table_name,
                "STATUS_QUEUE_URL": status_queue.queue_url,
                "NOTIFICATION_QUEUE_URL": notification_queue.queue_url,
            },
        )

        notification_lambda = build_lambda(
            "NotificationFunction",
            "notification_service",
            {
                "NOTIFICATION_TOPIC_ARN": notification_topic.topic_arn,
            },
        )

        search_lambda = build_lambda(
            "SearchFunction",
            "search_service",
            {"DOCUMENTS_TABLE": documents_table.table_name},
        )

        status_lambda = build_lambda(
            "StatusFunction",
            "status_service",
            {
                "STATUS_TABLE": status_table.table_name,
                "DOCUMENTS_TABLE": documents_table.table_name,
            },
        )

        # Generate JWT secret (get from environment variable, use default if not set, production should use AWS Secrets Manager)
        jwt_secret = os.environ.get(
            "JWT_SECRET", "change-this-secret-key-in-production-" + construct_id
        )

        auth_lambda = build_lambda(
            "AuthFunction",
            "auth_service",
            {
                "USERS_TABLE": users_table.table_name,
                "JWT_SECRET": jwt_secret,
            },
        )

        download_lambda = build_lambda(
            "DownloadFunction",
            "download_service",
            {
                "DOCUMENTS_BUCKET": documents_bucket.bucket_name,
                "DOCUMENTS_TABLE": documents_table.table_name,
                "JWT_SECRET": jwt_secret,
            },
        )

        documents_bucket.grant_put(upload_lambda)
        documents_table.grant_read_write_data(upload_lambda)
        extraction_queue.grant_send_messages(upload_lambda)

        documents_bucket.grant_read(extraction_lambda)
        metadata_queue.grant_send_messages(extraction_lambda)

        documents_table.grant_read_write_data(metadata_lambda)
        classification_queue.grant_send_messages(metadata_lambda)

        documents_table.grant_read_write_data(classification_lambda)
        status_queue.grant_send_messages(classification_lambda)
        notification_queue.grant_send_messages(classification_lambda)

        notification_topic.grant_publish(notification_lambda)
        documents_table.grant_read_data(search_lambda)
        status_table.grant_read_write_data(status_lambda)
        status_queue.grant_consume_messages(status_lambda)

        # Auth service permissions
        users_table.grant_read_write_data(auth_lambda)

        # Download service permissions
        documents_table.grant_read_data(download_lambda)
        documents_bucket.grant_read(download_lambda)

        extraction_queue.grant_consume_messages(extraction_lambda)
        metadata_queue.grant_consume_messages(metadata_lambda)
        classification_queue.grant_consume_messages(classification_lambda)
        notification_queue.grant_consume_messages(notification_lambda)

        extraction_lambda.add_event_source(
            lambda_events.SqsEventSource(extraction_queue)
        )
        metadata_lambda.add_event_source(lambda_events.SqsEventSource(metadata_queue))
        classification_lambda.add_event_source(
            lambda_events.SqsEventSource(classification_queue)
        )
        notification_lambda.add_event_source(
            lambda_events.SqsEventSource(notification_queue)
        )
        status_lambda.add_event_source(lambda_events.SqsEventSource(status_queue))

        api = apigw.RestApi(
            self,
            "SmartDocApi",
            rest_api_name="SmartDocAPI",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=["*"],
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["*"],
            ),
        )

        # Authentication endpoints
        auth_resource = api.root.add_resource("auth")
        auth_register_resource = auth_resource.add_resource("register")
        auth_register_resource.add_method("POST", apigw.LambdaIntegration(auth_lambda))
        auth_login_resource = auth_resource.add_resource("login")
        auth_login_resource.add_method("POST", apigw.LambdaIntegration(auth_lambda))

        # Document upload (requires authentication)
        documents_resource = api.root.add_resource("documents")
        documents_resource.add_method("POST", apigw.LambdaIntegration(upload_lambda))

        # Search (requires authentication)
        search_resource = api.root.add_resource("search")
        search_resource.add_method("GET", apigw.LambdaIntegration(search_lambda))

        # Status query (requires authentication)
        status_resource = api.root.add_resource("status").add_resource("{id}")
        status_resource.add_method("GET", apigw.LambdaIntegration(status_lambda))

        # File download (requires authentication)
        download_resource = api.root.add_resource("download")
        download_resource.add_method("GET", apigw.LambdaIntegration(download_lambda))

        documents_table.grant_read_data(status_lambda)

        # Add JWT_SECRET environment variable to all services that require authentication
        for lambda_fn in [upload_lambda, search_lambda, status_lambda, download_lambda]:
            lambda_fn.add_environment("JWT_SECRET", jwt_secret)

        upload_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject"],
                resources=[documents_bucket.arn_for_objects("*")],
            )
        )

        s3deploy.BucketDeployment(
            self,
            "FrontendDeployment",
            destination_bucket=frontend_bucket,
            sources=[
                s3deploy.Source.asset(str(frontend_dir)),
                s3deploy.Source.data(
                    "config.js",
                    f"window.APP_CONFIG={{apiBaseUrl: '{api.url}'}};",
                ),
            ],
        )

        CfnOutput(self, "ApiBaseUrl", value=api.url)
        CfnOutput(self, "FrontendUrl", value=frontend_bucket.bucket_website_url)
