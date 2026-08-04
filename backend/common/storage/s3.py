from dataclasses import dataclass
from urllib.parse import urlparse
import boto3
from botocore.client import Config
from django.conf import settings

@dataclass(frozen=True)
class PresignedUpload:
    object_key: str
    upload_url: str
    headers: dict
    public_url: str | None = None


def client(public: bool = False):
    endpoint = settings.S3_PUBLIC_ENDPOINT_URL if public else settings.S3_ENDPOINT_URL
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def presign_put(bucket: str, object_key: str, content_type: str, expires: int = 600, is_public: bool = False) -> PresignedUpload:
    public_client = client(public=True)
    url = public_client.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": object_key, "ContentType": content_type},
        ExpiresIn=expires,
    )
    public_url = f"{settings.S3_PUBLIC_ENDPOINT_URL.rstrip('/')}/{bucket}/{object_key}" if is_public else None
    return PresignedUpload(object_key, url, {"Content-Type": content_type}, public_url)


def presign_get(bucket: str, object_key: str, expires: int = 300) -> str:
    return client(public=True).generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": object_key}, ExpiresIn=expires)


def delete_object(bucket: str, object_key: str) -> None:
    client().delete_object(Bucket=bucket, Key=object_key)


def head_object(bucket: str, object_key: str) -> dict:
    return client().head_object(Bucket=bucket, Key=object_key)


def get_object_bytes(bucket: str, object_key: str) -> tuple[bytes, dict]:
    response = client().get_object(Bucket=bucket, Key=object_key)
    return response["Body"].read(), response


def put_object_bytes(bucket: str, object_key: str, data: bytes, content_type: str, *, public: bool = False) -> None:
    kwargs = {"Bucket": bucket, "Key": object_key, "Body": data, "ContentType": content_type}
    if public:
        kwargs["CacheControl"] = "public, max-age=31536000, immutable"
    client().put_object(**kwargs)
