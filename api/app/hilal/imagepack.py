"""CDN-hosted image pack reader for the pre-rendered hilal cards.

Mirrors ``astrocache``: on first use the pack manifest is fetched from
``MABIMS_IMAGEPACK_URL`` (default the public CDN). If the local sidecar
version differs, the versioned tar is downloaded, hash-verified and
extracted into the writable cache dir (``images.cache_dir()``). Failures
log a warning and fall back to bundled PNGs / lazy rendering.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tarfile
import tempfile
import threading
import urllib.request
from pathlib import Path

from . import images

logger = logging.getLogger("mabims.imagepack")

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
    except (OSError, ValueError) as exc:
        logger.warning("imagepack: fetch failed %s -> %s (%s)", url, target.name, exc)
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
                (dst := staging / name).parent.mkdir(parents=True, exist_ok=True)
                src = tar.extractfile(member)
                if src is None:
                    continue
                with open(dst, "wb") as fh:
                    fh.write(src.read())
                members.append(member)
            if not members:
                return False
        # Merge, never wipe: lazily rendered out-of-range cards may already
        # live in the cache dir and must survive a pack install. Staging is
        # on /tmp (a different device from the /data volume), so files are
        # copied next to their destination and renamed atomically there.
        for staged in staging.rglob("*.png"):
            dst = base / staged.relative_to(staging)
            dst.parent.mkdir(parents=True, exist_ok=True)
            tmp = dst.with_name(dst.name + ".packtmp")
            shutil.copyfile(staged, tmp)
            os.replace(tmp, dst)
        return True
    except (tarfile.TarError, OSError) as exc:
        logger.warning("imagepack: extract failed: %s", exc)
        return False
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def ensure_pack() -> bool:
    """Download + extract the pack when the CDN version is new. Logs on failure."""
    global _installed
    if _installed or is_disabled():
        return _installed
    with _lock:
        if _installed:
            return _installed
        base = images.cache_dir()
        try:
            base.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.warning("imagepack: cache dir unusable %s: %s", base, exc)
            return False
        sidecar = base / ".version"
        tmp_manifest = base / ".manifest.json"
        if not _fetch(f"{_base_url()}/manifest.json", tmp_manifest, timeout=30):
            logger.warning("imagepack: no manifest — keeping bundled/lazy fallbacks")
            return False
        try:
            manifest = json.loads(tmp_manifest.read_text(encoding="utf-8"))
            version, path = manifest["render_version"], manifest["path"]
            tar_sha = manifest["tar_sha256"]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            logger.warning("imagepack: bad manifest: %s", exc)
            tmp_manifest.unlink(missing_ok=True)
            return False
        if installed_version() == version:
            _installed = True
            logger.info("imagepack: already installed %s", version)
            return True
        tar_path = base / (f".pack-{version}.tar.gz")
        if not _fetch(f"{_base_url()}/{path}", tar_path):
            return False
        digest = hashlib.sha256(tar_path.read_bytes()).hexdigest()
        if digest != tar_sha:
            logger.warning("imagepack: sha mismatch for %s (expected %s, got %s)",
                           path, tar_sha, digest)
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
        except OSError as exc:
            logger.warning("imagepack: sidecar write failed: %s", exc)
            return False
        logger.info("imagepack: installed %s (%s files) into %s", version,
                    manifest.get("files", "?"), base)
        _installed = True
        return True
