---
title: FAQ
description: Frequently asked questions about the MABIMS Calendar API.
---

## General

<details>
<summary>What is MABIMS?</summary>

MABIMS is the rukyah criterion (Ministers of Religious Affairs of Brunei, Indonesia, Malaysia, Singapore) used by Indonesia's Ministry of Religious Affairs (Kemenag RI) to determine the start of the Hijriah month — specifically the beginning of Ramadan, Shawwal, and Dhul Hijjah. The Neo MABIMS criterion requires the hilal to be visible at least 3° with an elongation of at least 6.4° at sunset.

</details>

<details>
<summary>Why is the Hijriah date in my app different from the Indonesian government announcement?</summary>

Most Hijriah calendar APIs and apps use the Umm al-Qura (Saudi Arabia) criterion as the default. Because the rukyah method and observation location differ, the result can be ±1 day off from Kemenag's official decision — especially for the start of fasting, Eid al-Fitr, and Eid al-Adha.

</details>

<details>
<summary>MABIMS vs Umm al-Qura — which is more accurate for Indonesia?</summary>

For use in Indonesia, MABIMS is more accurate because it follows Kemenag RI's official decision through the isbat session, not Saudi authority. Umm al-Qura is designed for Saudi Arabia's needs and does not represent Indonesia's rukyah/hisab results.

</details>

<details>
<summary>Is this API an official product of Kemenag or MABIMS?</summary>

No. This API is independent, built by PIXO Studio using publicly available Kemenag RI table data as its source. For legal certainty in Islamic law, always refer to official Kemenag announcements.

</details>

## Access & Authentication

<details>
<summary>What is mabims.dev?</summary>

mabims.dev is a free open-source API for the Indonesian Hijri calendar. It provides today's Hijri date, date conversion, monthly and yearly calendars, hilal visibility data, and Islamic event dates — all based on official MABIMS data from Indonesia's Ministry of Religious Affairs (Kemenag RI). See the [About](/en/about) page for details.

</details>

<details>
<summary>Is this API free and does it require an API key?</summary>

Yes, it's free and requires no authentication. Just call the endpoint directly, with no registration or API key needed.

</details>

<details>
<summary>Can it be used directly from the frontend (client-side)?</summary>

Yes. CORS is open, so it can be called directly from the browser on any domain. For rate limit details and fair use policy, see the [Access & Rate Limits](/en/quickstart#access--rate-limits) section in Quickstart.

</details>

## Technical

<details>
<summary>What's the difference between <code>source: "mabims"</code> and <code>source: "mabims-computed"</code>?</summary>

- **`mabims`** — date taken directly from Kemenag's publicly available table.
- **`mabims-computed`** — automatically calculated using Neo MABIMS criteria because the date falls outside the table's coverage (before 2024 or after 2026).

</details>

<details>
<summary>How far ahead does the data go?</summary>

Official table data is available for 2024–2026. Outside that range, the API calculates automatically (fallback) using Neo MABIMS criteria up to the year 2053 — the response will tag `source: "mabims-computed"` instead of `"mabims"`.

</details>

<details>
<summary>What timezone is used by default?</summary>

**Asia/Jakarta (UTC+7)** by default, specifically for the `/today` endpoint. You can override it with the `tz` parameter using an IANA zone (e.g. `Asia/Kuala_Lumpur`) or a UTC offset (e.g. `UTC+8`). The `/convert` endpoint is timezone-independent since it's a date conversion, not "what day is it".

</details>

<details>
<summary>How do I convert between Gregorian and Hijri dates?</summary>

Use `GET /convert?date=YYYY-MM-DD&calendar=gregorian` or `calendar=hijri` depending on the conversion direction. Full documentation: [API Reference /convert & /range](/en/endpoints/convert-range).

</details>

<details>
<summary>How do I check hilal visibility for a given month?</summary>

Use the `/hilal/info` endpoint for criterion data, or `/hilal/viz` for a hilal visibility chart (720×1280 PNG) showing moon position, crescent direction, and VISIBLE/NOT VISIBLE verdict — calculated at Sabang point.

</details>

## Other

<details>
<summary>How do I display a Hijri date on a website?</summary>

Call the `GET /today` endpoint for today's date, then use the `day`, `month_name`, and `year` fields from the JSON response. Quick example:

```javascript
const res = await fetch("https://api.mabims.dev/api/v1/today");
const data = await res.json();
const { day, month_name, year } = data.output;
document.getElementById("hijri").textContent = `${day} ${month_name} ${year} H`;
```

For converting a specific date, use `GET /convert?date=YYYY-MM-DD&calendar=gregorian`. See the [Quickstart](/en/quickstart) for a full guide.

</details>

<details>
<summary>What programming languages are supported?</summary>

Since MABIMS.dev is a standard REST API, it works with any programming language — JavaScript, PHP, Python, Dart, Swift, Kotlin, or even cURL directly from the terminal. No special libraries needed, just call the endpoint.

</details>

<details>
<summary>Does the data match official Kemenag announcements?</summary>

Data tagged `source: "mabims"` comes directly from Kemenag RI's public tables, so it matches official announcements. For dates beyond table coverage, `source: "mabims-computed"` uses Neo MABIMS criteria which may differ from isbat session decisions since it's an astronomical estimate.

</details>

<details>
<summary>When is the start of Ramadan?</summary>

Use the `GET /events?year=2026&calendar=gregorian` endpoint to get the Ramadan start date. Data comes from Kemenag's official tables for available years, or is calculated using Neo MABIMS criteria for years beyond table coverage.

</details>

<details>
<summary>Why are Hijri dates different on Google?</summary>

Google and most calendar apps use Umm al-Qura (Saudi Arabia's standard), not MABIMS (Indonesia's standard). Because the observation location and rukyah method differ, results can be ±1 day off from Kemenag's official decisions.

</details>

<details>
<summary>What's the difference between hisab and rukyah?</summary>

**Hisab** is the astronomical calculation to determine the moon's position. **Rukyah** is the direct visual observation of the hilal (crescent moon). Neo MABIMS criteria combine both: using hisab calculations (moon altitude ≥ 3°, elongation ≥ 6.4°) that represent whether the hilal can be visually observed in Sabang.

</details>

<details>
<summary>Is this API open source?</summary>

Yes, the source code is open on GitHub: [PijarAdiluhung/mabims-api](https://github.com/PijarAdiluhung/mabims-api). Contributions and issue reports are always welcome.

</details>
