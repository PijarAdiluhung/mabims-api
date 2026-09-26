# ── Test-gate stage ────────────────────────────────────────────────────────
# Runs the CI gates ON BUILD: a red suite fails the build, and a failed build
# fails Dokploy's compose deploy before `up` — the previous containers keep
# serving. Moved out of GitHub Actions so the gate lives in the same pipeline
# that deploys.
FROM python:3.12-slim AS test

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp \
    MABIMS_EPHEMERIS_DIR=/app/data/ephemeris

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY tests ./tests
COPY static ./static
COPY scripts ./scripts
COPY data /app/data
# The kernel is tracked in git (31 MB); the astronomy tests and the verify
# probe load it from the MABIMS_EPHEMERIS_DIR path.
COPY scripts/.ephemeris-cache/de440s.bsp /app/data/ephemeris/de440s.bsp

# PIP_NO_CACHE_DIR is deliberately unset here: a persistent pip cache makes
# warm rebuilds skip re-downloads.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -e ".[dev]" && \
    pytest -q && \
    ruff check app tests scripts

# ── Runtime stage ──────────────────────────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLCONFIGDIR=/tmp \
    MABIMS_EPHEMERIS_DIR=/app/data/ephemeris

RUN python -c "import secrets; open('/build_hash','w').write(secrets.token_hex(8))"

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY static ./static
RUN pip install .

COPY data /app/data
# The kernel is tracked in git (31 MB). Bake it from the checkout instead of
# fetching from JPL, which re-ran (and hung) on every push that touched app/.
COPY scripts/.ephemeris-cache/de440s.bsp /app/data/ephemeris/de440s.bsp
COPY scripts/verify_ephemeris.py /app/scripts/verify_ephemeris.py

# Prove the baked kernel *computes* before the image can exist. A truncated
# de440s.bsp opens fine and only explodes at request time (jplephem: "buffer
# is too small for requested array"), which prod served as /hilal/* 503s.
# The first pass never touches the network; a bad kernel is deleted and fetched
# once more, and a second failure fails the build instead of the deploy.
RUN python /app/scripts/verify_ephemeris.py --no-download /app/data/ephemeris \
      || { echo "de440s.bsp unusable, refetching"; \
           rm -f /app/data/ephemeris/de440s.bsp; \
           python /app/scripts/verify_ephemeris.py /app/data/ephemeris; } \
    && mkdir -p /data \
    && chown -R nobody:nogroup /data /app/data/ephemeris

USER nobody

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*", "--timeout-keep-alive", "65"]
