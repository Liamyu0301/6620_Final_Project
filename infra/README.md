# Infrastructure Notes

This folder will contain the CDK application once we start provisioning AWS resources again. Key tasks:

1. `cdk init app --language python` inside `infra/cdk`.
2. Create stacks matching the documents in `docs/deployment_plan.md`.
3. Add `requirements.txt` with AWS CDK libraries (`aws-cdk-lib`, `constructs`, `boto3`).
4. Recreate Lambda assets by packaging each service in `services/`.
