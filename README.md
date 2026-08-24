# MABIMS Date Converter API

Gregorian ⇄ Hijri date conversion API following the **MABIMS** standard (Singapore, Indonesia, Malaysia). Rebuild of the original Netlify-function prototype as a self-hosted FastAPI service with an Astro/Starlight docs site.

## Status

🚧 **Rewrite in progress** — see [PLAN.md](PLAN.md) for the full plan and milestone tracker.

| Layer | Tech |
|---|---|
| API | FastAPI + Pydantic v2 |
| Docs | Astro + Starlight |
| Hosting | Single VPS via Dokploy, Bunny CDN in front |

## Data

`api/data/calendar_data.json` — precomputed MABIMS lookup table (moon-sighting criteria, not astronomical calculation). Currently covers **2025-01-01 → 2026-12-31**; a Umm al-Qura fallback bridge covers any gap while marked as approximate.

## Development (after M1)

```bash
cd api
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\pytest
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

---

Built by [PIXO Studio](https://pixostudio.id).
