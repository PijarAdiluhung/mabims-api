# Mabims Date Converter API

API for Gregorian-to-Hijri and Hijri-to-Gregorian date conversion using the **MABIMS** standard (widely adopted in Singapore, Indonesia, and Malaysia).

## Features

- Convert Gregorian dates to Hijri (Islamic) dates and vice versa
- MABIMS standard compliance for Southeast Asian regions
- Lightweight, JSON-based responses
- Deployed as a serverless function on Netlify
- Local Express server for development

## Tech Stack

- **Runtime:** Node.js
- **Framework:** Express (local) / Netlify Functions (production)
- **Data:** Precomputed JSON lookup table
- **Deployment:** Netlify

## API Usage

### Endpoint

```
GET /api/lookup?date=YYYY-MM-DD&source={gregorian|hijri}
```

Or for today's date:

```
GET /api/lookup?source=today
```

### Example

```bash
curl "https://mabims-api.netlify.app/lookup?date=2025-01-03&source=gregorian"
```

### Response

```json
{
  "success": true,
  "input_data": { "date": "2025-01-03", "type": "GREGORIAN" },
  "output_data": { "date": "1446-07-03", "type": "HIJRI" },
  "message": "Conversion successful."
}
```

## Local Development

```bash
npm install
npm start
```

Server runs at `http://localhost:3000`.

## Deployment

The project is configured for deployment on Netlify via `netlify.toml`. The serverless function is located in `netlify/functions/lookup.js`.

## Status

Currently validated and accurate for dates in **2025–2026**. API access is invite-only for whitelisted domains.

## Contact

For partnership and API access inquiries: [halo@pixostudio.id](mailto:halo@pixostudio.id)

---

Built by [PIXO Studio](https://pixostudio.id).
