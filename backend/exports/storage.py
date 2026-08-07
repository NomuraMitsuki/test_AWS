"""S3 境界。本番は boto3、テストはインメモリモック。"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod


class StorageClient(ABC):
    @abstractmethod
    def put_object(self, key: str, body: bytes, content_type: str = "text/csv") -> None:
        raise NotImplementedError

    @abstractmethod
    def generate_presigned_url(self, key: str, expires_in: int) -> str:
        raise NotImplementedError


class InMemoryStorageClient(StorageClient):
    """pytest 用モック。"""

    def __init__(self, bucket: str = "test-exports-bucket"):
        self.bucket = bucket
        self.objects: dict[str, bytes] = {}
        self.fail_put = False
        self.fail_presign = False

    def put_object(self, key: str, body: bytes, content_type: str = "text/csv") -> None:
        if self.fail_put:
            raise RuntimeError("S3 PutObject failed")
        self.objects[key] = body

    def generate_presigned_url(self, key: str, expires_in: int) -> str:
        if self.fail_presign:
            raise RuntimeError("S3 presign failed")
        if key not in self.objects:
            raise KeyError(f"object not found: {key}")
        return f"https://{self.bucket}.s3.amazonaws.com/{key}?X-Amz-Expires={expires_in}&signed=1"


class Boto3S3Client(StorageClient):
    """本番用。EXPORTS_BUCKET_NAME 環境変数必須。単体テストでは使わない。"""

    def __init__(self, bucket: str, client=None):
        self.bucket = bucket
        if client is not None:
            self._client = client
        else:
            import boto3

            self._client = boto3.client("s3")

    def put_object(self, key: str, body: bytes, content_type: str = "text/csv") -> None:
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )

    def generate_presigned_url(self, key: str, expires_in: int) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )


def default_storage_client() -> StorageClient:
    bucket = os.environ.get("EXPORTS_BUCKET_NAME")
    if bucket:
        return Boto3S3Client(bucket)
    return InMemoryStorageClient()
