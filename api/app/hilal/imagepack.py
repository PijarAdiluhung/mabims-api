"""CDN-hosted image pack reader for the pre-rendered hilal cards.

Mirrors ``astrocache``: on first use the pack manifest is fetched from
``MABIMS_IMAGEPACK_URL`` (default the public CDN). If the local sidecar
version differs, the versioned tar is downloaded, hash-verified and
extracted into the writable cache dir (``images.cache_dir()``). Failures
are silent — the endpoints fall back to bundled PNGs and lazy rendering.
"""

from __future__ import annotations

import hashlib
import json
import os
import tarfile
import tempfile
import threading
import urllib.request
from pathlib import Path

from . import images

DEFAULT_URL = "https://mabims-dev.b-cdn.net/hilal_images"

_lock = threading.Lock()
_installed = False


def _base_url() -> str:
    return os.environ.get("MABIMS_IMAGEPACK_URL", DEFAULT_URL).rstrip("/")


def is_disabled() -> bool:
    return os.environ.get("MABIMS_DISABLE_IMAGEPACK", "") == "1"


def installed_version() -> str | None:
    try:
        sidecar = images.cache_dir() / ".version"
        return sidecar.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def _fetch(url: str, target: Path, timeout: int = 120) -> bool:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "mabims-api"})
        with urllib.request.urlopen(request, timeout=timeout) as response, open(target, "wb") as fh:
            while chunk := response.read(1 << 22):
                fh.write(chunk)
        return True
    except (OSError, ValueError):
        target.unlink(missing_ok=True)
        return False


def _extract(tar_path: Path, base: Path) -> bool:
    import shutil

    staging = Path(tempfile.mkdtemp(prefix="mabims-pack-"))
    try:
        with tarfile.open(str(tar_path), "r:*") as tar:
            members = []
            for member in tar.getmembers():
                name = Path(member.name).as_posix()
                parts = name.split("/")
                if len(parts) != 2 or parts[1] == "" or not parts[1].endswith(".png"):
                    continue
                (dst := staging / name).parent.mkdir(exist_ok=True)
                src = tar.extractfile(member)
                if src is None:
                    continue
                with open(dst, "wb") as fh:
                    fh.write(src.read())
                members.append(member)
            if not members:
                return False
        for kind_dir in ("viz", "map"):
            shutil.rmtree(base / kind_dir, ignore_errors=True)
        for kind_dir in ("viz", "map"):
            if (staging / kind_dir).is_dir():
                (staging / kind_dir).replace(base / kind_dir)
        return True
    except (tarfile.TarError, OSError):
        return False
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def ensure_pack() -> bool:
    """Download + extract the pack when the CDN version is new. Silent on failure."""
    global _installed
    if _installed or is_disabled():
        return _installed
    with _lock:
        if _installed:
            return _installed
        base = images.cache_dir()
        try:
            base.mkdir(parents=True, exist_ok=True)
        except OSError:
            return False
        sidecar = base / ".version"
        tmp_manifest = base / ".manifest.json"
        if not _fetch(f"{_base_url()}/manifest.json", tmp_manifest, timeout=30):
            return False
        try:
            manifest = json.loads(tmp_manifest.read_text(encoding="utf-8"))
            version, path = manifest["render_version"], manifest["path"]
            tar_sha = manifest["tar_sha256"]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            tmp_manifest.unlink(missing_ok=True)
            return False
        if installed_version() == version:
            _installed = True
            return True
        tar_path = base / (f".pack-{version}.tar.gz")
        if not _fetch(f"{_base_url()}/{path}", tar_path):
            return False
        digest = hashlib.sha256(tar_path.read_bytes()).hexdigest()
        if digest != tar_sha:
            tar_path.unlink(missing_ok=True)
            return False
        if not _extract(tar_path, base):
            tar_path.unlink(missing_ok=True)
            return False
        tar_path.unlink(missing_ok=True)
        tmp = base / ".version.tmp"
        try:
            tmp.write_text(version, encoding="utf-8")
            os.replace(tmp, sidecar)
        except OSError:
            return False
        _installed = True
        return True
