"""Object storage behind one interface: S3-compatible (MinIO in self-hosted
deployments) or the local filesystem (tests / single-machine dev).
URLs handed to clients are always signed and time-limited."""
from __future__ import annotations

import hashlib
import mimetypes
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import quote, urlencode

from app.core.config import get_settings
from app.core.security import sign_path


class Storage(ABC):
    @abstractmethod
    def put_bytes(self, key: str, data: bytes, content_type: str | None = None) -> None: ...

    @abstractmethod
    def put_file(self, key: str, path: str, content_type: str | None = None) -> None: ...

    @abstractmethod
    def get_bytes(self, key: str) -> bytes: ...

    @abstractmethod
    def download_to(self, key: str, path: str) -> str: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def signed_url(self, key: str, ttl: int | None = None, download_name: str | None = None) -> str: ...

    def ensure_ready(self) -> None:  # pragma: no cover - backend specific
        return None


def guess_type(key: str) -> str:
    return mimetypes.guess_type(key)[0] or "application/octet-stream"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class LocalStorage(Storage):
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        p = (self.root / key).resolve()
        if self.root not in p.parents and p != self.root:
            raise ValueError("invalid storage key")
        return p

    def put_bytes(self, key, data, content_type=None):
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def put_file(self, key, path, content_type=None):
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, p)

    def get_bytes(self, key):
        return self._path(key).read_bytes()

    def download_to(self, key, path):
        shutil.copyfile(self._path(key), path)
        return path

    def exists(self, key):
        return self._path(key).exists()

    def delete(self, key):
        p = self._path(key)
        if p.exists():
            p.unlink()

    def local_path(self, key: str) -> str:
        return str(self._path(key))

    def signed_url(self, key, ttl=None, download_name=None):
        exp, sig = sign_path(key, ttl)
        params = {"exp": exp, "sig": sig}
        if download_name:
            params["dl"] = download_name
        base = get_settings().public_api_url.rstrip("/")
        return f"{base}/api/files/{quote(key)}?{urlencode(params)}"


class S3Storage(Storage):
    def __init__(self):
        import boto3
        from botocore.config import Config

        s = get_settings()
        common = dict(region_name=s.s3_region,
                      aws_access_key_id=s.s3_access_key.get_secret_value(),
                      aws_secret_access_key=s.s3_secret_key.get_secret_value(),
                      config=Config(signature_version="s3v4", s3={"addressing_style": "path"}))
        self.bucket = s.s3_bucket
        self.client = boto3.client("s3", endpoint_url=s.s3_endpoint_url, **common)
        # A second client signs URLs for the browser-reachable endpoint.
        self.public_client = boto3.client(
            "s3", endpoint_url=s.s3_public_endpoint_url or s.s3_endpoint_url, **common)

    def ensure_ready(self):
        from botocore.exceptions import ClientError
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)

    def put_bytes(self, key, data, content_type=None):
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data,
                               ContentType=content_type or guess_type(key))

    def put_file(self, key, path, content_type=None):
        self.client.upload_file(path, self.bucket, key,
                                ExtraArgs={"ContentType": content_type or guess_type(key)})

    def get_bytes(self, key):
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def download_to(self, key, path):
        self.client.download_file(self.bucket, key, path)
        return path

    def exists(self, key):
        from botocore.exceptions import ClientError
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def delete(self, key):
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def signed_url(self, key, ttl=None, download_name=None):
        params = {"Bucket": self.bucket, "Key": key}
        if download_name:
            params["ResponseContentDisposition"] = f'attachment; filename="{download_name}"'
        return self.public_client.generate_presigned_url(
            "get_object", Params=params,
            ExpiresIn=ttl or get_settings().signed_url_ttl_seconds)


_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        s = get_settings()
        _storage = S3Storage() if s.storage_backend == "s3" else LocalStorage(s.local_storage_dir)
    return _storage


def set_storage(storage: Storage | None) -> None:
    global _storage
    _storage = storage


def ext_for_mime(mime: str) -> str:
    return {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
            "video/mp4": ".mp4", "audio/mpeg": ".mp3", "audio/wav": ".wav",
            "audio/x-wav": ".wav", "text/vtt": ".vtt"}.get(mime) or mimetypes.guess_extension(mime) or ""


def tmp_dir() -> str:
    d = os.path.join(os.environ.get("UGC_TMP", "/tmp"), "ugc-work")
    os.makedirs(d, exist_ok=True)
    return d
