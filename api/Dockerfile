FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MABIMS_EPHEMERIS_DIR=/app/data/ephemeris

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
RUN pip install .

COPY data /app/data
RUN python -c "from skyfield.api import Loader; Loader('/app/data/ephemeris')('de421.bsp')" \
    && mkdir -p /data \
    && chown -R nobody:nogroup /data /app/data/ephemeris

USER nobody

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
