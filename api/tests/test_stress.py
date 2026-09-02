from __future__ import annotations

import json
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

API_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = API_DIR / "data" / "calendar_data.json"
SEED_PATH = API_DIR / "data" / "computed_seed.json"

# Curated table start, derived from the data so tests follow coverage changes.
TABLE_FIRST = min(json.loads(DATA_PATH.read_text(encoding="utf-8"))["gregorian_to_hijri"])


def _make_computed_client(tmp_path: Path, seed_path: Path | None = None) -> TestClient:
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    shrunk: dict[str, dict[str, str]] = {"gregorian_to_hijri": {}, "hijri_to_gregorian": {}}
    for key, value in list(raw["gregorian_to_hijri"].items())[:90]:
        shrunk["gregorian_to_hijri"][key] = value
        shrunk["hijri_to_gregorian"][value] = key
    (data_dir / "calendar_data.json").write_text(json.dumps(shrunk), encoding="utf-8")

    if seed_path and seed_path.exists():
        (data_dir / "computed_seed.json").write_bytes(seed_path.read_bytes())

    settings = Settings(
        data_dir=data_dir,
        allowed_origins=[],
        rate_limit="10000/minute",
        enable_fallback=True,
        enable_computed=True,
        enable_aladhan=False,
    )
    return TestClient(create_app(settings=settings))


def _make_full_client(tmp_path: Path) -> TestClient:
    """Client with full calendar data (no seed) for range tests."""
    settings = Settings(
        data_dir=DATA_PATH.parent,
        allowed_origins=[],
        rate_limit="10000/minute",
        enable_fallback=True,
        enable_computed=True,
        enable_aladhan=False,
    )
    return TestClient(create_app(settings=settings))


def _sample_dates(start: date, end: date, n: int) -> list[str]:
    """Pick n evenly-spaced dates across a range."""
    span = (end - start).days
    step = max(1, span // (n - 1))
    return [(start + timedelta(days=i * step)).isoformat() for i in range(n)]


# ---------------------------------------------------------------------------
# 1. Concurrency stress test
# ---------------------------------------------------------------------------
class TestConcurrency:
    DATES = _sample_dates(date(2024, 6, 1), date(2050, 12, 31), 50)

    def test_concurrent_requests_no_errors(self, tmp_path):
        client = _make_computed_client(tmp_path, SEED_PATH)
        errors: list[str] = []
        latencies: list[float] = []

        def fetch(d: str) -> None:
            t0 = time.perf_counter()
            try:
                r = client.get(f"/api/v1/convert?date={d}&calendar=gregorian")
                elapsed = time.perf_counter() - t0
                latencies.append(elapsed)
                if r.status_code != 200:
                    errors.append(f"{d}: HTTP {r.status_code} {r.json()}")
            except Exception as exc:
                errors.append(f"{d}: {exc}")

        with ThreadPoolExecutor(max_workers=20) as pool:
            list(pool.map(fetch, self.DATES))

        assert not errors, "Errors under concurrency:\n" + "\n".join(errors)
        assert latencies
        p50 = statistics.median(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        p99 = sorted(latencies)[int(len(latencies) * 0.99)]
        print(f"\n  Latency: p50={p50:.3f}s  p95={p95:.3f}s  p99={p99:.3f}s  n={len(latencies)}")

    def test_concurrent_requests_consistent_results(self, tmp_path):
        client = _make_computed_client(tmp_path, SEED_PATH)
        date_str = "2035-06-15"
        results: list[str] = []
        lock = threading.Lock()

        def fetch():
            r = client.get(f"/api/v1/convert?date={date_str}&calendar=gregorian")
            body = r.json()
            with lock:
                results.append(body["output"]["date"])

        with ThreadPoolExecutor(max_workers=20) as pool:
            list(pool.map(lambda _: fetch(), range(30)))

        assert len(set(results)) == 1, f"Inconsistent results: {set(results)}"


# ---------------------------------------------------------------------------
# 2. Cold start test (no seed)
# ---------------------------------------------------------------------------
class TestColdStart:
    def test_far_future_date_without_seed(self, tmp_path):
        client = _make_computed_client(tmp_path, seed_path=None)
        t0 = time.perf_counter()
        r = client.get("/api/v1/convert?date=2035-06-15&calendar=gregorian")
        elapsed = time.perf_counter() - t0
        assert r.status_code == 200
        body = r.json()
        assert body["source"] == "mabims-computed"
        print(f"\n  Cold start 2035-06-15 (no seed): {elapsed:.2f}s")

    def test_near_anchor_date_without_seed(self, tmp_path):
        client = _make_computed_client(tmp_path, seed_path=None)
        t0 = time.perf_counter()
        r = client.get("/api/v1/convert?date=2024-06-15&calendar=gregorian")
        elapsed = time.perf_counter() - t0
        assert r.status_code == 200
        body = r.json()
        assert body["source"] == "mabims-computed"
        print(f"\n  Cold start 2024-06-15 (no seed, near anchor): {elapsed:.2f}s")


# ---------------------------------------------------------------------------
# 3. Corrupt seed test
# ---------------------------------------------------------------------------
class TestCorruptSeed:
    def test_garbage_seed_graceful_degradation(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        shrunk: dict[str, dict[str, str]] = {"gregorian_to_hijri": {}, "hijri_to_gregorian": {}}
        for key, value in list(raw["gregorian_to_hijri"].items())[:90]:
            shrunk["gregorian_to_hijri"][key] = value
            shrunk["hijri_to_gregorian"][value] = key
        (data_dir / "calendar_data.json").write_text(json.dumps(shrunk), encoding="utf-8")
        (data_dir / "computed_seed.json").write_text("{ BAD JSON", encoding="utf-8")

        settings = Settings(
            data_dir=data_dir,
            allowed_origins=[],
            rate_limit="10000/minute",
            enable_fallback=True,
            enable_computed=True,
            enable_aladhan=False,
        )
        client = TestClient(create_app(settings=settings))
        r = client.get("/api/v1/convert?date=2025-06-15&calendar=gregorian")
        assert r.status_code == 200
        body = r.json()
        assert body["source"] == "mabims-computed"

    def test_truncated_seed_graceful_degradation(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        shrunk: dict[str, dict[str, str]] = {"gregorian_to_hijri": {}, "hijri_to_gregorian": {}}
        for key, value in list(raw["gregorian_to_hijri"].items())[:90]:
            shrunk["gregorian_to_hijri"][key] = value
            shrunk["hijri_to_gregorian"][value] = key
        (data_dir / "calendar_data.json").write_text(json.dumps(shrunk), encoding="utf-8")
        seed_raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
        half = len(seed_raw["hijri_to_gregorian"]) // 2
        truncated = {"hijri_to_gregorian": dict(list(seed_raw["hijri_to_gregorian"].items())[:half])}
        (data_dir / "computed_seed.json").write_text(json.dumps(truncated), encoding="utf-8")

        settings = Settings(
            data_dir=data_dir,
            allowed_origins=[],
            rate_limit="10000/minute",
            enable_fallback=True,
            enable_computed=True,
            enable_aladhan=False,
        )
        client = TestClient(create_app(settings=settings))
        r = client.get("/api/v1/convert?date=2025-06-15&calendar=gregorian")
        assert r.status_code == 200
        body = r.json()
        assert body["source"] == "mabims-computed"


# ---------------------------------------------------------------------------
# 4. Range stress test
# ---------------------------------------------------------------------------
class TestRangeStress:
    def test_full_year_range(self, tmp_path):
        client = _make_full_client(tmp_path)
        r = client.get("/api/v1/range?start=2024-01-13&end=2024-02-26&calendar=gregorian")
        assert r.status_code == 200
        body = r.json()
        expected_days = (date(2024, 2, 26) - date(2024, 1, 13)).days + 1
        assert body["count"] == expected_days
        sources = {item["source"] for item in body["items"]}
        assert "mabims" in sources or "mabims-computed" in sources

    def test_cross_boundary_range(self, tmp_path):
        client = _make_full_client(tmp_path)
        r = client.get("/api/v1/range?start=2026-12-15&end=2027-01-28&calendar=gregorian")
        assert r.status_code == 200
        body = r.json()
        expected_days = (date(2027, 1, 28) - date(2026, 12, 15)).days + 1
        assert body["count"] == expected_days
        sources = {item["source"] for item in body["items"]}
        assert "mabims" in sources
        assert "mabims-computed" in sources

    def test_all_days_resolve_correctly(self, tmp_path):
        client = _make_computed_client(tmp_path, SEED_PATH)
        r = client.get("/api/v1/range?start=2025-01-01&end=2025-02-14&calendar=gregorian")
        assert r.status_code == 200
        body = r.json()
        expected_days = (date(2025, 2, 14) - date(2025, 1, 1)).days + 1
        assert body["count"] == expected_days
        for item in body["items"]:
            parts = item["hijri"].split("-")
            assert len(parts) == 3
            assert 1 <= int(parts[1]) <= 12
            assert 1 <= int(parts[2]) <= 30

    def test_range_too_large_rejected(self, tmp_path):
        client = _make_full_client(tmp_path)
        r = client.get("/api/v1/range?start=2025-01-01&end=2025-03-01&calendar=gregorian")
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "range_too_large"


# ---------------------------------------------------------------------------
# 5. Boundary test
# ---------------------------------------------------------------------------
class TestBoundary:
    def test_hard_cap_start(self, tmp_path):
        client = _make_computed_client(tmp_path, SEED_PATH)
        r = client.get(f"/api/v1/convert?date={TABLE_FIRST}&calendar=gregorian")
        assert r.status_code == 200

    def test_before_hard_cap_start(self, tmp_path):
        client = _make_computed_client(tmp_path, SEED_PATH)
        before = (date.fromisoformat(TABLE_FIRST) - timedelta(days=1)).isoformat()
        r = client.get(f"/api/v1/convert?date={before}&calendar=gregorian")
        assert r.status_code == 400
        body = r.json()
        assert body["error"]["code"] == "date_out_of_supported_range"

    def test_hard_cap_end(self, tmp_path):
        client = _make_computed_client(tmp_path, SEED_PATH)
        r = client.get("/api/v1/convert?date=2053-07-31&calendar=gregorian")
        assert r.status_code == 200

    def test_beyond_hard_cap_end(self, tmp_path):
        client = _make_computed_client(tmp_path, SEED_PATH)
        r = client.get("/api/v1/convert?date=2053-08-01&calendar=gregorian")
        assert r.status_code in (400, 404, 503)

    def test_far_beyond_hard_cap_end(self, tmp_path):
        client = _make_computed_client(tmp_path, SEED_PATH)
        r = client.get("/api/v1/convert?date=2100-01-01&calendar=gregorian")
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# 6. Concurrent seed extension
# ---------------------------------------------------------------------------
class TestConcurrentSeedExtension:
    def test_parallel_future_months(self, tmp_path):
        client = _make_computed_client(tmp_path, SEED_PATH)
        future_dates = _sample_dates(date(2045, 1, 1), date(2050, 12, 31), 30)
        errors: list[str] = []
        results: dict[str, str] = {}
        lock = threading.Lock()

        def fetch(d: str):
            r = client.get(f"/api/v1/convert?date={d}&calendar=gregorian")
            body = r.json()
            with lock:
                if r.status_code != 200:
                    errors.append(f"{d}: HTTP {r.status_code}")
                else:
                    results[d] = body["output"]["date"]

        with ThreadPoolExecutor(max_workers=15) as pool:
            list(pool.map(fetch, future_dates))

        assert not errors, f"Errors: {errors}"
        assert len(results) == len(future_dates)

    def test_parallel_hijri_and_gregorian(self, tmp_path):
        client = _make_computed_client(tmp_path, SEED_PATH)
        errors: list[str] = []

        def fetch_g(d: str):
            r = client.get(f"/api/v1/convert?date={d}&calendar=gregorian")
            if r.status_code != 200:
                errors.append(f"G {d}: {r.status_code}")

        def fetch_h(d: str):
            r = client.get(f"/api/v1/convert?date={d}&calendar=hijri")
            if r.status_code != 200:
                errors.append(f"H {d}: {r.status_code}")

        g_dates = _sample_dates(date(2030, 1, 1), date(2045, 12, 31), 20)
        h_dates = [f"{y:04d}-{m:02d}-15" for y in range(1455, 1470) for m in range(1, 13, 3)]

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(fetch_g, d) for d in g_dates]
            futures += [pool.submit(fetch_h, d) for d in h_dates]
            for f in as_completed(futures):
                f.result()

        assert not errors, f"Errors: {errors}"
