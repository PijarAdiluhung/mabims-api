from __future__ import annotations

import shutil
from pathlib import Path

from scripts import verify_ephemeris as verify

KERNEL = Path(__file__).resolve().parents[1] / "scripts" / ".ephemeris-cache" / "de440s.bsp"


def test_tracked_kernel_validates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    shutil.copyfile(KERNEL, tmp_path / "de440s.bsp")
    assert verify.main(["verify", "--no-download", str(tmp_path)]) == 0


def test_missing_kernel_fails_without_touching_the_network(tmp_path):
    assert verify.main(["verify", "--no-download", str(tmp_path)]) == 1


def test_partial_download_fails(tmp_path):
    """A short fetch — the shape that reached prod and 503'd /hilal/*."""
    (tmp_path / "de440s.bsp").write_bytes(b"\0" * 1024)
    assert verify.main(["verify", "--no-download", str(tmp_path)]) == 1


def test_full_length_but_corrupt_kernel_fails(tmp_path):
    """Size alone is not proof: the jplephem read must actually work."""
    (tmp_path / "de440s.bsp").write_bytes(b"\0" * (verify.MIN_BYTES + 1))
    assert verify.main(["verify", "--no-download", str(tmp_path)]) == 1
