"""
Abstracts over local disk, S3, and Google Drive storage.
Switch via STORAGE_BACKEND env var: 'local' | 's3' | 'gdrive'
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
    mime_type: str = "application/octet-stream",
) -> tuple[str, str]:
    """
    Returns (stored_key, public_url_or_path).
    stored_key is the Drive file ID for gdrive, S3 key for s3, or local path for local.
    """
    key = f"submissions/{submission_id}/{file_kind}/{uuid.uuid4()}{_ext(original_filename)}"

    if settings.storage_backend == "cloudinary":
        return _store_cloudinary(content, original_filename, file_kind)
    if settings.storage_backend == "gdrive":
        return _store_gdrive(content, original_filename, mime_type)
    if settings.storage_backend == "s3":
        return await _store_s3(content, key)
    return _store_local(content, key)


# ── Cloudinary ───────────────────────────────────────────────────────────────

def _store_cloudinary(
    content: bytes,
    original_filename: str,
    file_kind: str,
) -> tuple[str, str]:
    """
    Upload to Cloudinary and return (public_id, secure_url).
    Photos go to the 'image' resource type; documents use 'raw'.
    """
    import cloudinary
    import cloudinary.uploader
    import io

    from app.core.config import get_settings as _gs
    _s = _gs()
    cloudinary.config(
        cloud_name=_s.cloudinary_cloud_name,
        api_key=_s.cloudinary_api_key,
        api_secret=_s.cloudinary_api_secret,
        secure=True,
    )

    # Photos → "image" resource type (CDN-optimised delivery)
    # Documents (PDF, Word, Excel) → "raw" so Cloudinary serves the original
    # file bytes without trying to render pages, which requires a paid plan.
    resource_type = "image" if file_kind == "photo" else "raw"

    # Build an explicit public_id that includes the file extension.
    # Uploading BytesIO gives Cloudinary no filename to infer from, so
    # use_filename=True has no effect — we must set the id ourselves.
    # For raw resources the extension in the public_id appears in the URL,
    # which is what tells browsers (and macOS) the correct content type.
    import uuid as _uuid
    ext = os.path.splitext(original_filename)[1].lower()  # e.g. ".pdf"
    public_id = f"mbsse-srgbv/{file_kind}/{_uuid.uuid4()}{ext}"

    result = cloudinary.uploader.upload(
        io.BytesIO(content),
        resource_type=resource_type,
        public_id=public_id,
        overwrite=False,
        type="upload",
    )
    return result["public_id"], result["secure_url"]


# ── Google Drive ─────────────────────────────────────────────────────────────

def _gdrive_service():
    """Build and return an authenticated Drive v3 service.

    GDRIVE_CREDENTIALS_JSON accepts either:
      - A file path to the service account JSON key file  (recommended)
      - The raw JSON string itself (must be on one line in .env)
    """
    import json, os, logging
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    # Re-read settings fresh each call to avoid stale cached values
    from app.core.config import get_settings as _gs
    _settings = _gs()
    raw = _settings.gdrive_credentials_json.strip()
    logging.getLogger(__name__).info("GDRIVE raw value (first 60 chars): %r", raw[:60])
    if not raw:
        raise ValueError("GDRIVE_CREDENTIALS_JSON is not set")

    # If it looks like a file path, read the file
    if not raw.startswith("{"):
        if not os.path.isfile(raw):
            raise FileNotFoundError(f"Service account key file not found: {raw!r}")
        with open(raw) as f:
            creds_info = json.load(f)
        logging.getLogger(__name__).info("GDRIVE loaded from file, keys: %s", list(creds_info.keys()))
    else:
        creds_info = json.loads(raw)
        logging.getLogger(__name__).info("GDRIVE parsed inline JSON, keys: %s", list(creds_info.keys()))

    creds = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _store_gdrive(
    content: bytes,
    original_filename: str,
    mime_type: str,
) -> tuple[str, str]:
    """
    Upload content to Google Drive, make it readable by anyone with the link,
    and return (file_id, shareable_url).
    """
    import io
    from googleapiclient.http import MediaIoBaseUpload

    service = _gdrive_service()

    from app.core.config import get_settings as _gs
    _settings = _gs()
    file_metadata = {
        "name": original_filename,
        "parents": [_settings.gdrive_folder_id],
    }
    media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=False)
    uploaded = (
        service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True,
        )
        .execute()
    )
    file_id = uploaded["id"]

    # Grant "anyone with the link" read access so admins can open it directly
    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
        supportsAllDrives=True,
    ).execute()

    url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
    return file_id, url


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
    """
    Return a URL for the stored file.
    - gdrive: stored_key IS the file_id; return permanent shareable URL.
    - s3: generate a time-limited presigned URL.
    - local: return a local path.
    """
    if settings.storage_backend == "cloudinary":
        # stored_key is the public_id; reconstruct the URL via Cloudinary SDK
        import cloudinary
        from app.core.config import get_settings as _gs
        _s = _gs()
        cloudinary.config(cloud_name=_s.cloudinary_cloud_name, api_key=_s.cloudinary_api_key, api_secret=_s.cloudinary_api_secret, secure=True)
        return cloudinary.utils.cloudinary_url(stored_key, resource_type="raw")[0]
    if settings.storage_backend == "gdrive":
        return f"https://drive.google.com/file/d/{stored_key}/view?usp=sharing"
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
