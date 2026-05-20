"""
Abstracts over local disk vs S3 storage.
Switch via STORAGE_BACKEND env var: 'local' | 's3'
"""
import os
import uuid
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


def _ext(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    return ext.lower()


async def store_file(
    content: bytes,
    original_filename: str,
    submission_id: str,
    file_kind: str,
) -> tuple[str, str]:
    """
    Returns (stored_key, public_url_or_path).
    """
    key = f"submissions/{submission_id}/{file_kind}/{uuid.uuid4()}{_ext(original_filename)}"

    if settings.storage_backend == "s3":
        return await _store_s3(content, key)
    else:
        return _store_local(content, key)


# ── Local (dev / Render Disk) ────────────────────────────────────────────────

def _store_local(content: bytes, key: str) -> tuple[str, str]:
    path = Path(settings.local_upload_dir) / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    # In production replace with a signed URL endpoint
    url = f"/uploads/{key}"
    return key, url


# ── S3 ────────────────────────────────────────────────────────────────────────

async def _store_s3(content: bytes, key: str) -> tuple[str, str]:
    import boto3
    from botocore.exceptions import ClientError

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )
    s3.put_object(
        Bucket=settings.aws_s3_bucket,
        Key=key,
        Body=content,
    )
    # Generate a time-limited presigned URL
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.aws_s3_bucket, "Key": key},
        ExpiresIn=settings.s3_presigned_url_expiry,
    )
    return key, url


async def get_presigned_url(stored_key: str) -> str:
    """Refresh presigned URL on read (for S3). Returns local path otherwise."""
    if settings.storage_backend == "s3":
        import boto3
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.aws_s3_bucket, "Key": stored_key},
            ExpiresIn=settings.s3_presigned_url_expiry,
        )
    return f"/uploads/{stored_key}"
