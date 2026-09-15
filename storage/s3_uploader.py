"""
## Part 3 , Cloud sync (data engineering)

The edge device batches processed windows (features + anomaly flags and 10Hz samples) and uploads them to S3.

- Batch and compress windowed output before upload.
- Use (eg LocalStack) to mock S3 , we do not expect a real AWS account or live credentials.
- Simulate intermittent connectivity: uploads should sometimes fail. Buffer unsent batches durably on local disk (eg. file based queue) so no data is lost across a simulated process restart, and retry with backoff once connectivity returns.
- CreateDesign the S3 object layout/partitioning and briefly justify it in the README.
"""

import json
import boto3


class S3Uploader:
    def __init__(
        self,
        bucket: str,
        endpoint_url: str = "http://localhost:4566",
    ):
        self.bucket = bucket

        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )

    def upload_batch(self, batch_id: str, windows: list[dict]):
        key = f"windows/{batch_id}.json"

        payload = json.dumps(
            {
                "batch_id": batch_id,
                "windows": windows,
            }
        ).encode("utf-8")

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=payload,
            ContentType="application/json",
        )

        return key