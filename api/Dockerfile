# ── Test-gate stage ────────────────────────────────────────────────────────
# Runs the CI gates ON BUILD, and freezes the exact resolution it tested:
# the runtime stage installs from that frozen set, so the artifact pytest
# verified is the artifact that serves. A red suite fails the build, and a
# failed build fails Dokploy's compose deploy before `up` — the previous
# containers keep serving.
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
#
# Install 1 — non-editable prod deps, exactly the command the runtime used
# to run. `pip freeze` captures that resolution; the app itself is stripped
# from it (freeze of a plain `pip install .` emits `mabims-api @ file:///app`
# — the runtime stage serves /app directly, not from a package install).
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install . && \
    pip freeze | sed -E '/^mabims-api[ =@]/d' > /req.lock

# Install 2 — dev tools for the gates.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install pytest ruff

# Install 3 — re-enforce the frozen prod pins (pip may have upgraded shared
# transitives when installing dev tools; the suite must run against the exact
# set that will ship), then gate.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /req.lock && \
    pytest -q && \
    ruff check app tests scripts && \
    touch /gate-passed

# ── Runtime stage ──────────────────────────────────────────────────────────
# BuildKit only builds stages the final image references — dropping this COPY
# would skip the gate silently (prod shipped exactly that, build done in 11s,
# pytest never ran). Copying the 0-byte marker makes the runtime stage
# require the test stage to have completed green.
FROM python:3.12-slim

COPY --from=test /gate-passed /tmp/gate-passed
COPY --from=test /req.lock /tmp/req.lock

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLCONFIGDIR=/tmp \
    MABIMS_EPHEMERIS_DIR=/app/data/ephemeris \
    PYTHONPATH=/app

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY static ./static
COPY data /app/data
# The kernel is tracked in git (31 MB). Bake it from the checkout instead of
# fetching from JPL, which re-ran (and hung) on every push that touched app/.
COPY scripts/.ephemeris-cache/de440s.bsp /app/data/ephemeris/de440s.bsp
COPY scripts/verify_ephemeris.py /app/scripts/verify_ephemeris.py

# Install the FROZEN set the test stage verified — no fresh resolution here:
# "tested artifact == shipped artifact" is the whole point. No dev tools
# enter the image.
RUN --mount=type=cache,target=/root/.cache/pip \
    PIP_NO_CACHE_DIR=0 pip install -r /tmp/req.lock

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

# build_hash is content-derived — sorted sha256 over app/, static/, data/,
# pyproject.toml and the verify script — replacing the old random token that
# survived cache rebuilds unchanged and made the prod monitor's hash-diff
# useless. Changed api content => new hash => an honest "new build is live"
# signal for the monitor in .github/workflows/ci.yml.
RUN find /app/pyproject.toml /app/app /app/static /app/data \
      /app/scripts/verify_ephemeris.py -type f -print0 \
    | sort -z \
    | xargs -0 sha256sum \
    | sha256sum \
    | cut -d' ' -f1 > /build_hash

USER nobody

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status==200 else 1)"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*", "--timeout-keep-alive", "65"]
