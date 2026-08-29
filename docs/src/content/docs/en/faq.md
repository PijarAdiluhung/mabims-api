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
<summary>Is this API free and does it require an API key?</summary>

Yes, it's free and requires no authentication. Just call the endpoint directly, with no registration or API key needed.

</details>

<details>
<summary>Can it be used directly from the frontend (client-side)?</summary>

Yes. CORS is open, so it can be called directly from the browser on any domain. For rate limit details and fair use policy, see the [Access & Rate Limits](/en/access) page.

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
<summary>Is this API open source?</summary>

Yes, the source code is open on GitHub: [PijarAdiluhung/mabims-api](https://github.com/PijarAdiluhung/mabims-api). Contributions and issue reports are always welcome.

</details>
