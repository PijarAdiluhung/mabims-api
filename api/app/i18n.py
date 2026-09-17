"""Documentation string catalogue for the OpenAPI / Scalar reference.

Only prose that surfaces in the generated reference lives here: the app
description, tag blurbs, endpoint summaries and descriptions, query-parameter
descriptions, and schema field descriptions. Runtime payloads (warnings, error
messages, response values) stay in English and are deliberately out of scope.

English is kept verbatim as the archive. The Indonesian strings mirror the
vocabulary already used in ``docs/src/content/docs/`` so both surfaces read the
same. Select the language with ``MABIMS_LANG`` (default ``id``).
"""
from __future__ import annotations

import os

LANG = (os.environ.get("MABIMS_LANG") or "id").strip().lower() or "id"

_STRINGS: dict[str, dict[str, str]] = {
    "app.description": {
        "en": (
            "## MABIMS API — Indonesian Hijri Calendar\n\n"
            "Free, open-source API for the Indonesian Hijri calendar.\n"
            "Uses official MABIMS data from "
            "[Kementerian Agama RI](https://kemenag.go.id),\n"
            "not [Umm al-Qura](https://en.wikipedia.org/wiki/Umm_al-Qura_calendar) "
            "(Saudi Arabia's standard).\n\n"
            "### Quick Start\n\n"
            "**Today's date:**\n"
            '```bash\ncurl "https://api.mabims.dev/api/v1/today"\n```\n\n'
            "**Convert a date:**\n"
            '```bash\ncurl "https://api.mabims.dev/api/v1/convert?date=2025-01-03&calendar=gregorian"\n```\n\n'
            "### Endpoints\n\n"
            "| Endpoint | Description |\n|---|---|\n"
            "| `/today` | Today's Hijri date (timezone-aware) |\n"
            "| `/convert` | Single date conversion (Gregorian ↔ Hijri) |\n"
            "| `/range` | Bulk conversion (up to 45 days) |\n"
            "| `/month` | All days in a calendar month |\n"
            "| `/year` | All days in a calendar year |\n"
            "| `/events` | Islamic observances (Ramadan, Eid, 1 Muharram, Maulid) |\n"
            "| `/hilal/info` | Hilal visibility data (JSON) |\n"
            "| `/hilal/viz` | Hilal sky chart (PNG 720×1280) |\n\n"
            "### Coverage\n\n"
            "| Source | Range |\n|---|---|\n"
            "| `mabims` | 2023-01-23 → 2026-12-31 (Kemenag table) |\n"
            "| `mabims-computed` | Up to 2100 (Neo MABIMS criteria) |\n"
            "| `mabims-retro` | 1945-01-01 → 2023-01-22 (requires `retro=true`) |\n\n"
            "### No API key required\n\n"
            "All endpoints are public. CORS is open for browser access."
        ),
        "id": (
            "## API MABIMS: Kalender Hijriah Indonesia\n\n"
            "API gratis dan open-source untuk kalender Hijriah Indonesia.\n"
            "Memakai data resmi MABIMS dari "
            "[Kementerian Agama RI](https://kemenag.go.id),\n"
            "bukan [Umm al-Qura](https://en.wikipedia.org/wiki/Umm_al-Qura_calendar) "
            "(patokan Arab Saudi).\n\n"
            "### Mulai Cepat\n\n"
            "**Tanggal hari ini:**\n"
            '```bash\ncurl "https://api.mabims.dev/api/v1/today"\n```\n\n'
            "**Konversi tanggal:**\n"
            '```bash\ncurl "https://api.mabims.dev/api/v1/convert?date=2025-01-03&calendar=gregorian"\n```\n\n'
            "### Endpoint\n\n"
            "| Endpoint | Fungsi |\n|---|---|\n"
            "| `/today` | Tanggal Hijriah hari ini (timezone-aware) |\n"
            "| `/convert` | Konversi satu tanggal (Masehi ↔ Hijriah) |\n"
            "| `/range` | Konversi massal hingga 45 hari |\n"
            "| `/month` | Semua hari dalam satu bulan |\n"
            "| `/year` | Semua hari dalam satu tahun |\n"
            "| `/events` | Hari besar Islam (Ramadan, Idul Fitri, Idul Adha, 1 Muharram, Maulid Nabi) |\n"
            "| `/hilal/info` | Data visibilitas hilal (JSON) |\n"
            "| `/hilal/viz` | Grafik langit hilal (PNG 720×1280) |\n\n"
            "### Cakupan\n\n"
            "| Sumber | Rentang |\n|---|---|\n"
            "| `mabims` | 2023-01-23 sampai 2026-12-31 (tabel Kemenag) |\n"
            "| `mabims-computed` | Sampai 2100 (kriteria Neo MABIMS) |\n"
            "| `mabims-retro` | 1945-01-01 sampai 2023-01-22 (butuh `retro=true`) |\n\n"
            "### Tidak perlu API key\n\n"
            "Semua endpoint bersifat publik. CORS dibuka untuk akses browser."
        ),
    },
    "tag.today": {
        "en": "Today's Hijri date (timezone-aware)",
        "id": "Tanggal Hijriah hari ini (timezone-aware)",
    },
    "tag.convert": {
        "en": "Single date Gregorian ↔ Hijri conversion",
        "id": "Konversi satu tanggal (Masehi ↔ Hijriah)",
    },
    "tag.range": {
        "en": "Bulk date range conversion (up to 45 days)",
        "id": "Konversi massal rentang tanggal (maksimal 45 hari)",
    },
    "tag.month": {
        "en": "All days in a calendar month",
        "id": "Semua hari dalam satu bulan",
    },
    "tag.year": {
        "en": "All days in a calendar year",
        "id": "Semua hari dalam satu tahun",
    },
    "tag.events": {
        "en": "Islamic observances — Ramadan, Eid, 1 Muharram, Maulid",
        "id": "Hari besar Islam: Ramadan, Idul Fitri, Idul Adha, 1 Muharram, Maulid Nabi",
    },
    "tag.hilal": {
        "en": "Hilal visibility data and sky charts",
        "id": "Data visibilitas hilal dan grafik langit",
    },
    "tag.meta": {
        "en": "Data coverage, computation status, and table version",
        "id": "Cakupan data dan status komputasi",
    },
    "tag.health": {
        "en": "Liveness probes",
        "id": "Probe liveness",
    },
    "healthz.summary": {
        "en": "Liveness probe",
        "id": "Probe liveness",
    },
    "healthz.description": {
        "en": (
            "Liveness probe for uptime monitors. Returns `status`, `version` "
            "and `build_hash`. Never cached (`Cache-Control: no-store`)."
        ),
        "id": (
            "Probe liveness untuk monitor uptime. Mengembalikan `status`, "
            "`version`, dan `build_hash`. Tidak pernah di-cache "
            "(`Cache-Control: no-store`)."
        ),
    },
    "meta.summary": {
        "en": "API metadata",
        "id": "Metadata API",
    },
    "meta.description": {
        "en": (
            "Machine-readable truth about the dataset backing every other "
            "endpoint: data version, Gregorian table coverage, computed-tier "
            "status (`computed_active`, `computed_months`, `method`), hilal "
            "render range, Sidang Isbat corrections (`divergences[]`, "
            "`table_version`) and the docs URL. Poll it daily to detect "
            "table updates and corrections; cacheable for 5 minutes."
        ),
        "id": (
            "Info tentang dataset yang machine-readable di balik semua "
            "endpoint lain: versi data, cakupan tabel Masehi, status tier "
            "komputasi (`computed_active`, `computed_months`, `method`), "
            "rentang render hilal, koreksi Sidang Isbat (`divergences[]`, "
            "`table_version`), dan URL dokumentasi. Poll `/meta` secara harian "
            "untuk mendeteksi pembaruan dan koreksi tabel; dapat di-cache "
            "selama 5 menit."
        ),
    },
    "table.summary": {
        "en": "Full calendar table",
        "id": "Tabel kalender lengkap",
    },
    "table.description": {
        "en": "Returns the complete MABIMS calendar table for offline use.",
        "id": "Mengembalikan tabel kalender MABIMS lengkap untuk dipakai offline.",
    },
    "convert.summary": {
        "en": "Convert a single date",
        "id": "Konversi satu tanggal",
    },
    "convert.description": {
        "en": (
            "Converts one date in the direction implied by `calendar`: "
            "Gregorian → Hijri when `calendar=gregorian`, Hijri → Gregorian "
            "when `calendar=hijri`. Timezone-independent by design — only "
            "/today takes `tz`, because \"today\" depends on where you ask "
            "from. Dates within the curated Kemenag table are authoritative "
            "(`source: mabims`); beyond it they are computed with the Neo "
            "MABIMS criteria (`mabims-computed`), or `mabims-retro` below the "
            "table with `retro=true`."
        ),
        "id": (
            "Mengkonversi satu tanggal dari satu sistem ke sistem yang lain, "
            "dengan arah yang ditentukan secara implisit oleh `calendar`: Masehi "
            "ke Hijriah saat `calendar=gregorian`, Hijriah ke Masehi saat "
            "`calendar=hijri`. Tidak bergantung pada zona waktu berdasarkan "
            "desain; hanya /today yang menerima parameter `tz`, karena \"hari "
            "ini\" tergantung dari mana Anda bertanya. Tanggal di dalam tabel "
            "kurasi Kemenag bersifat otoritatif (`source: mabims`); di luarnya "
            "dihitung dengan kriteria Neo MABIMS (`mabims-computed`), atau "
            "`mabims-retro` di bawah tabel kurasi dengan `retro=true`."
        ),
    },
    "today.summary": {
        "en": "Today's Hijri date",
        "id": "Tanggal Hijriah hari ini",
    },
    "today.description": {
        "en": (
            "Returns the Hijri date for \"now\" in the requested timezone — "
            "the hero endpoint most consumer apps poll. Tuned for it: "
            "responses carry dynamic edge-cache TTLs so a CDN serves nearly "
            "all traffic. Defaults to Asia/Jakarta (UTC+7); accepts any IANA "
            "zone name (`Asia/Kuala_Lumpur`) or UTC offset (`UTC+8`, `+08:00`)"
            ". The Hijri day begins at maghrib, so the date rolls over before "
            "midnight: set `next=true` to also return the Hijri date that "
            "becomes current after this evening's maghrib (`next` object, "
            "with its own `source`) — gate the flip on your own sunset clock, "
            "the API does not compute sunset."
        ),
        "id": (
            "Mengembalikan tanggal Hijriah untuk \"sekarang\" di zona waktu yang "
            "diminta. Ini adalah endpoint utama yang paling sering di-poll oleh "
            "aplikasi consumer, maka telah dioptimalkan. Respons memiliki TTL "
            "edge-cache dinamis sehingga CDN melayani hampir semua traffic. "
            "Default-nya Asia/Jakarta (UTC+7); menerima nama zona IANA "
            "(`Asia/Kuala_Lumpur`) atau UTC offset (`UTC+8`, `+08:00`). Hari "
            "Hijriah dimulai saat magrib, jadi tanggal berganti sebelum tengah "
            "malam: set `next=true` untuk juga mengembalikan tanggal Hijriah "
            "yang mulai berlaku setelah magrib malam ini (objek `next`, dengan "
            "`source` sendiri). API tidak menghitung waktu matahari terbenam, "
            "jadi tentukan momen magrib di sisi klien Anda."
        ),
    },
    "today_on.summary": {
        "en": "Hijri date for a fixed Gregorian date",
        "id": "Tanggal Hijriah untuk tanggal Masehi tertentu",
    },
    "today_on.description": {
        "en": (
            "Same conversion as /today for any given Gregorian date — a "
            "stable resource for cache-forever CDN setups and for replaying "
            "historical days. Immutable endpoint, CDN-cacheable forever "
            "(`max-age=86400`). Date format: `YYYY-MM-DD`. Does not accept "
            "`tz` — conversion is timezone-independent."
        ),
        "id": (
            "Konversi yang sama seperti /today untuk tanggal Masehi tertentu. "
            "Berguna sebagai resource yang stabil dan dapat di-cache selamanya, "
            "serta untuk memutar ulang hari-hari historis. Endpoint immutable, "
            "aman di-cache CDN selamanya (`max-age=86400`). Format tanggal: "
            "`YYYY-MM-DD`. Tidak menerima `tz`, karena konversi tidak bergantung "
            "pada zona waktu."
        ),
    },
    "range.summary": {
        "en": "Bulk date conversion",
        "id": "Konversi massal rentang tanggal",
    },
    "range.description": {
        "en": (
            "Converts every day in an inclusive range, up to 45 days. Each "
            "item carries its own `source` — ranges crossing the table "
            "boundary can mix authoritative (`mabims`) and computed "
            "(`mabims-computed`) data. For `calendar=hijri`, ranges beyond "
            "the public table are served from the Neo MABIMS computed tier "
            "while within the supported range. Responses are immutable per "
            "input and safely cacheable for a full day."
        ),
        "id": (
            "Mengkonversi setiap hari dalam rentang yang diminta, maksimal 45 "
            "hari. Setiap item membawa `source` masing-masing, karena rentang "
            "yang melewati batasan data MABIMS dapat mencampur data publik dan "
            "data komputed. Untuk `calendar=hijri`, rentang dapat melampaui "
            "cakupan tabel publik; bulan Hijriah di luar tabel dilayani dari "
            "perhitungan Neo MABIMS (hingga 2100). Respons bersifat immutable "
            "per input dan dikirim dengan `Cache-Control: max-age=86400`, aman "
            "di-cache di layer mana pun selama satu hari penuh."
        ),
    },
    "events.summary": {
        "en": "Islamic events for a year",
        "id": "Hari besar Islam dalam satu tahun",
    },
    "events.description": {
        "en": (
            "Returns the Islamic observance dates for one calendar year — "
            "1 Muharram, Maulid Nabi, Awal Ramadan, Idul Fitri, Idul Adha — "
            "sorted by Gregorian date. Within the curated table, dates come "
            "straight from the public Kemenag table; beyond coverage they "
            "are computed live with the Neo MABIMS criteria, giving "
            "observance dates years into the future (`source: "
            "`mabims-computed` — check `warnings[]`). For "
            "`calendar=gregorian`, the overlapping Hijri years are estimated "
            "and each event is resolved across them."
        ),
        "id": (
            "Mengembalikan tanggal hari besar Islam untuk satu tahun kalender "
            "(1 Muharram, Maulid Nabi, Awal Ramadan, Idul Fitri, Idul Adha), "
            "diurutkan berdasarkan tanggal Masehi. Di dalam cakupan tabel "
            "MABIMS, tanggal langsung dari tabel publik Kemenag; di luar "
            "cakupan, tanggal dikomputasi secara langsung menggunakan kriteria "
            "Neo MABIMS (`source: mabims-computed`, periksa `warnings[]`), "
            "sehingga Anda bisa mendapatkan tanggal hari besar bertahun-tahun "
            "ke depan. Untuk `calendar=gregorian`, endpoint memperkirakan tahun "
            "Hijriah yang tumpang tindih dengan tahun Masehi yang diminta dan "
            "menyelesaikan setiap event di tahun-tahun tersebut."
        ),
    },
    "month.summary": {
        "en": "All days in a month",
        "id": "Semua hari dalam satu bulan",
    },
    "month.description": {
        "en": (
            "Convenience wrapper resolving a whole month grid. For "
            "`calendar=hijri` the response contains every Gregorian date "
            "onto which that Hijri month maps (29–30 items, same shape as "
            "/range) — exactly what a Hijri month-view needs. Months beyond "
            "the public table are served from the Neo MABIMS computed tier "
            "while within the supported range."
        ),
        "id": (
            "Wrapper praktis untuk mendapatkan satu bulan penuh. Untuk "
            "`calendar=hijri`, respons berisi setiap tanggal Masehi yang "
            "menjadi acuan dari bulan Hijriah tersebut (29 sampai 30 item, "
            "bentuk itemnya sama dengan /range). Bulan Hijriah di luar tabel "
            "publik (mis. tahun mendatang) tetap dilayani dari perhitungan Neo "
            "MABIMS selama masih dalam rentang yang didukung."
        ),
    },
    "year.summary": {
        "en": "All days in a year",
        "id": "Semua hari dalam satu tahun",
    },
    "year.description": {
        "en": (
            "Returns every day across all 12 months of a year — much simpler "
            "than calling /month 12 times. Month keys contain arrays with "
            "the same item shape as /range; `count` is the number of days in "
            "the whole year. Beyond the public table, months are served from "
            "the Neo MABIMS computed tier while within the supported range."
        ),
        "id": (
            "Mengembalikan semua hari dalam 12 bulan sebuah tahun. Lebih "
            "praktis daripada memanggil /month 12 kali. Setiap kunci bulan "
            "berisi array item dengan format yang sama dengan /range; `count` "
            "adalah jumlah hari di seluruh tahun. Untuk `calendar=hijri`, bulan "
            "Hijriah di luar tabel publik tetap dilayani dari perhitungan Neo "
            "MABIMS selama masih dalam rentang yang didukung."
        ),
    },
    "hilal_info.summary": {
        "en": "Hilal visibility data",
        "id": "Data visibilitas hilal",
    },
    "hilal_info.description": {
        "en": (
            "Hilal visibility data for the evening deciding a Hijri month "
            "start — always the 29th of the current month, the night people "
            "actually go looking for the crescent. The Neo MABIMS criteria "
            "(moon altitude ≥ 3.0° topocentric with refraction, elongation ≥ "
            "6.4° geocentric) are evaluated at 25 coastal observation sites "
            "across Indonesia at each site's local sunset: `visible` is true "
            "when met at **any** site, and the passing — or best-margin — "
            "site is reported as `deciding_site` (all values refer to it). "
            "If met nowhere, the month completes 30 days. Rate limit: "
            "60/hour per IP."
        ),
        "id": (
            "Data visibilitas hilal untuk malam yang menentukan awal bulan "
            "Hijriah, yaitu malam ke-29 bulan Hijriah yang sedang berjalan. "
            "Kriteria Neo MABIMS (ketinggian Bulan ≥ 3,0° toposentris dengan "
            "koreksi refraksi, elongasi ≥ 6,4° geosentris) dievaluasi di 25 "
            "titik pengamatan pesisir di seluruh Indonesia saat matahari "
            "terbenam di masing-masing titik: `visible` bernilai true jika "
            "terpenuhi di setidaknya satu titik pengamatan. Titik penentu, "
            "atau titik dengan margin terbaik bila tidak ada yang memenuhi, "
            "dilaporkan lewat `deciding_site`; semua nilai merujuk padanya. "
            "Kalau kriteria tidak terpenuhi di satu pun titik, bulan "
            "digenapkan menjadi 30 hari. Rate limit: 60 permintaan per jam "
            "per IP."
        ),
    },
    "hilal_history.summary": {
        "en": "Hilal history (precomputed)",
        "id": "Riwayat hilal (indeks terhitung)",
    },
    "hilal_history.description": {
        "en": (
            "Per-month hilal summary for a Hijri `YYYY-MM` range, read from "
            "the precomputed index (1444-08 through 1475-12 by default) — a "
            "single cheap lookup that powers a visibility timeline without "
            "one /hilal/info call per month."
        ),
        "id": (
            "Mengembalikan ringkasan hilal per bulan untuk rentang Hijriah "
            "`from` sampai `to` (format `YYYY-MM`, default seluruh indeks "
            "1444-08 sampai 1475-12). Datanya diambil dari indeks terhitung, "
            "sehingga satu permintaan cukup untuk menampilkan seluruh daftar "
            "riwayat tanpa memanggil /hilal/info berkali-kali."
        ),
    },
    "hilal_viz.summary": {
        "en": "Hilal sky chart PNG",
        "id": "Grafik langit hilal PNG",
    },
    "hilal_viz.description": {
        "en": (
            "Renders the \"where to look\" sky chart as a 720×1280 vertical "
            "PNG: sunset sky with the crescent (bright limb facing the sun), "
            "a verdict pill, and a criteria table plus deciding-site row — "
            "the scene, values and times all refer to the same deciding "
            "site. Deterministic per parameter. Add `bare=true` for the "
            "panel-less 1440×1520 web card, `download=true` to receive it as "
            "an attachment. Render cap: Hijri 1444–1475. Rate limit: "
            "30/hour per IP."
        ),
        "id": (
            "Mengembalikan PNG vertikal berukuran 720×1280 yang berisi langit "
            "senja dengan bulan sabit, sisi terang menghadap Matahari; label "
            "status (`MEMENUHI KRITERIA`, `TIDAK MEMENUHI`, `MENDEKATI BATAS`, "
            "atau `DI BAWAH HORIZON`); serta tabel kriteria dan baris "
            "**TITIK PENGAMAT**. Adegan langit, angka kriteria, dan waktu di "
            "dalam grafik semuanya merujuk pada titik penentu yang sama. Untuk "
            "parameter yang sama, outputnya selalu konsisten. Tambahkan "
            "`bare=true` untuk kartu resolusi tinggi 1440×1520 tanpa panel "
            "(header + grafik + logo) yang dipakai sebagai gambar hero di web, "
            "`download=true` untuk menerimanya sebagai attachment. Kap render: "
            "Hijri 1444 sampai 1475. Rate limit: 30 permintaan per jam per IP."
        ),
    },
    "hilal_map.summary": {
        "en": "Hilal visibility map PNG",
        "id": "Peta visibilitas hilal PNG",
    },
    "hilal_map.description": {
        "en": (
            "Renders an archipelago visibility map as a 720×1280 PNG: the "
            "region where the Neo MABIMS criteria are met at local sunset, "
            "the altitude-3°/elongation-6.4° boundary lines, and 95 display "
            "points (green = meets the criteria, gray = does not) with the "
            "deciding point ringed. Uses the same deciding point as "
            "/hilal/viz, so both cards always name the same observer. Add "
            "`bare=true` for the panel-less 1440×1520 web card, "
            "`download=true` to receive it as an attachment. Render cap: "
            "Hijri 1444–1475. Rate limit: 30/hour per IP."
        ),
        "id": (
            "Mengembalikan PNG 720×1280 berisi peta wilayah visibilitas "
            "seluruh Nusantara: area tempat kriteria Neo MABIMS terpenuhi saat "
            "matahari terbenam, garis batas ketinggian 3° dan elongasi 6,4°, "
            "serta 95 titik tampilan (hijau = memenuhi, abu-abu = tidak "
            "memenuhi). Titik penentu dari model 25 titik ditandai dengan "
            "cincin kuning. Tabel pada kartu memakai angka titik penentu yang "
            "sama dengan /hilal/viz, sehingga kedua kartu selalu menyebut "
            "titik pengamat yang sama. Tambahkan `bare=true` untuk kartu "
            "resolusi tinggi 1440×1520 tanpa panel, `download=true` untuk "
            "menerimanya sebagai attachment. Kap render: Hijri 1444 sampai "
            "1475. Rate limit: 30 permintaan per jam per IP."
        ),
    },
    "query.retro": {
        "en": "Set true to allow computed retro dates below the curated table",
        "id": "Buka tanggal retro komputasi di bawah tabel kurasi, ditandai `mabims-retro`",
    },
    "query.next": {
        "en": (
            "Set true to also return the Hijri date that begins at this evening's maghrib "
            "(the next civil day's mapping), so a client can flip the date locally. The API "
            "does not compute sunset — gate on your own prayer-time clock."
        ),
        "id": (
            "Set `true` untuk juga mengembalikan tanggal Hijriah yang mulai berlaku "
            "setelah magrib malam ini (setara pemetaan hari sipil berikutnya). API "
            "tidak menghitung waktu matahari terbenam, jadi tentukan momen magrib di "
            "sisi klien Anda."
        ),
    },
    "query.bare": {
        "en": (
            "Set true to omit the criteria panel and return the high-resolution bare "
            "card (header + graphic + logo) used as the web hero image."
        ),
        "id": (
            "Hanya untuk `viz` dan `map`: menghilangkan panel kriteria dan "
            "mengembalikan kartu resolusi tinggi 1440×1520 (header + grafik + logo) "
            "untuk dipakai sebagai gambar hero di web."
        ),
    },
    "query.download": {
        "en": (
            "Set true to return Content-Disposition: attachment so the browser "
            "downloads the PNG instead of navigating to it."
        ),
        "id": (
            "Hanya untuk `viz` dan `map`: mengirim `Content-Disposition: attachment` "
            "sehingga browser mengunduh PNG alih-alih membukanya. Berguna karena "
            "atribut `download` HTML diabaikan untuk URL lintas-origin."
        ),
    },
    "query.date": {
        "en": "Date in YYYY-MM-DD format (e.g. 2025-01-03 or 1446-07-03)",
        "id": "Tanggal ISO (`YYYY-MM-DD`), misalnya 2025-01-03 atau 1446-07-03",
    },
    "query.calendar": {
        "en": "'gregorian' or 'hijri'",
        "id": "Kalender dari tanggal input: `gregorian` atau `hijri`",
    },
    "query.tz": {
        "en": "IANA timezone (e.g. Asia/Jakarta) or UTC offset (e.g. UTC+8)",
        "id": "Nama zona IANA (`Asia/Kuala_Lumpur`) atau UTC offset (`UTC+8`, `+08:00`)",
    },
    "query.start_date": {
        "en": "Start date in YYYY-MM-DD format",
        "id": "Tanggal mulai ISO (`YYYY-MM-DD`), dengan `start` ≤ `end` dan rentang maks 45 hari",
    },
    "query.end_date": {
        "en": "End date in YYYY-MM-DD format",
        "id": "Tanggal akhir ISO (`YYYY-MM-DD`), dengan `start` ≤ `end` dan rentang maks 45 hari",
    },
    "query.step": {
        "en": "Only 'day' is supported",
        "id": "Hanya `day` yang didukung",
    },
    "query.events_year": {
        "en": "Year (e.g. 2026)",
        "id": "Tahun kalender sesuai `calendar` (Hijriah: 1446, Masehi: 2025)",
    },
    "query.hijri_year": {
        "en": "Year (e.g. 1447)",
        "id": "Tahun Hijriah atau Masehi (mis. 1447)",
    },
    "query.month": {
        "en": "Month 1-12",
        "id": "Bulan 1-12",
    },
    "query.hijri_month": {
        "en": "Hijri month 1-12",
        "id": "Bulan Hijriah target (1-12)",
    },
    "query.hilal_year": {
        "en": "Hijri year (e.g. 1447)",
        "id": "Tahun Hijriah target (mis. 1447)",
    },
    "query.history_from": {
        "en": "Start month YYYY-MM (e.g. 1445-08)",
        "id": "Bulan awal rentang Hijriah `YYYY-MM` (mis. 1445-08)",
    },
    "query.history_to": {
        "en": "End month YYYY-MM (e.g. 1475-12)",
        "id": "Bulan akhir rentang Hijriah `YYYY-MM` (mis. 1475-12)",
    },
    "schema.source": {
        "en": (
            "Data origin: 'mabims' = curated from publicly available Kemenag tables, "
            "'mabims-computed' = Neo MABIMS algorithmic estimates, "
            "'mabims-retro' = Neo MABIMS criteria projected backwards below the curated table"
        ),
        "id": (
            "Asal data: `mabims` = data publik Kemenag, `mabims-computed` = dihitung "
            "dengan kriteria Neo MABIMS, `mabims-retro` = kriteria Neo MABIMS "
            "diproyeksikan ke belakang di bawah tabel kurasi"
        ),
    },
    "schema.warnings": {
        "en": "Non-empty when borderline months, computed fallback, or retro projection applies",
        "id": "Tidak kosong saat berlaku bulan di batas ambang, fallback komputasi, atau proyeksi retro",
    },
    "schema.today.next": {
        "en": (
            "The Hijri date that becomes current after this evening's maghrib (the next "
            "civil day's mapping). Only present when next=true. The API does not compute "
            "sunset — gate on your own prayer-time clock."
        ),
        "id": (
            "Tanggal Hijriah yang berlaku setelah magrib malam ini (setara pemetaan "
            "hari sipil berikutnya). Hanya ada saat `next=true`. API tidak menghitung "
            "waktu matahari terbenam, jadi tentukan momen magrib di sisi klien Anda."
        ),
    },
    "schema.hilal_image_range": {
        "en": (
            "Inclusive [min, max] Hijri years for which the hilal PNG endpoints"
            " (/hilal/viz, /hilal/map) serve images. This is a render cap, not the"
            " data cap: see coverage.forward_ceil for date-conversion limits."
        ),
        "id": (
            "Rentang tahun Hijriah `[min, max]` yang kartu /hilal/viz dan /hilal/map-nya "
            "sudah dibuat lebih dulu. Ini kap render, bukan kap data: lihat "
            "`coverage.forward_ceil` untuk batas konversi tanggal."
        ),
    },
    "schema.divergences": {
        "en": (
            "Sidang Isbat corrections: months whose official start differs from "
            "the published Kemenag calendar, each as {hijri_month, delta_days}. "
            "Empty when the published calendar and the sidang isbat results "
            "fully agree."
        ),
        "id": (
            "Riwayat koreksi Sidang Isbat: setiap entri berisi `hijri_month` (bulan "
            "terkoreksi) dan `delta_days` (geseran dalam hari). Kosong bila kalender "
            "terbit dan hasil Sidang Isbat sepenuhnya sepakat."
        ),
    },
    "schema.table_version": {
        "en": (
            "Version token for the curated-table override history. Changes whenever "
            "a Sidang Isbat correction is applied — poll /meta and diff this to know "
            "when to re-fetch affected dates."
        ),
        "id": (
            "Token versi riwayat koreksi; berubah setiap kali koreksi Sidang Isbat "
            "diterapkan. Bandingkan dengan nilai yang Anda simpan untuk tahu kapan "
            "harus menarik ulang tanggal di bulan terkoreksi."
        ),
    },
    "schema.deciding_site.model": {
        "en": "The coastal observation site whose sunset decided the verdict.",
        "id": "Titik pengamatan pesisir yang menentukan putusan visibilitas.",
    },
    "schema.deciding_site.tz": {
        "en": "IANA timezone used for the site's displayed times",
        "id": "Zona waktu IANA yang dipakai untuk waktu yang ditampilkan di titik pengamatan",
    },
    "schema.hilal_evening.moon_alt_deg": {
        "en": (
            "Topocentric apparent moon altitude (refraction applied) at the "
            "deciding site's local sunset"
        ),
        "id": (
            "Ketinggian Bulan tampak toposentris (sudah dikoreksi refraksi) saat "
            "matahari terbenam di titik penentu"
        ),
    },
    "schema.hilal_evening.moon_az_deg": {
        "en": "Moon azimuth at the deciding site's sunset, degrees from north clockwise",
        "id": "Azimut Bulan saat matahari terbenam di titik penentu, derajat dari utara searah jarum jam",
    },
    "schema.hilal_evening.sun_alt_deg": {
        "en": "Sun altitude at the deciding site's sunset",
        "id": "Ketinggian Matahari saat matahari terbenam di titik penentu",
    },
    "schema.hilal_evening.elongation_deg": {
        "en": "Geocentric moon-sun elongation at the deciding site's local sunset",
        "id": "Elongasi Bulan-Matahari geosentris saat matahari terbenam lokal di titik penentu",
    },
    "schema.hilal_evening.deciding_site": {
        "en": (
            "The coastal observation site whose sunset all reported values describe — "
            "the deciding site when the hilal is seen, otherwise the site that came "
            "closest to the criteria"
        ),
        "id": (
            "Titik pengamatan pesisir yang menjadi acuan semua nilai yang dilaporkan; "
            "titik penentu bila hilal terlihat, jika tidak titik dengan margin terbaik "
            "yang paling mendekati kriteria"
        ),
    },
    "schema.hilal_evening.sites_checked": {
        "en": "Number of coastal observation sites evaluated",
        "id": "Jumlah titik pengamatan pesisir yang dievaluasi",
    },
    "schema.hilal_evening.alt_ok": {
        "en": "Moon altitude >= 3.0 degrees at the deciding site's sunset",
        "id": "Ketinggian Bulan ≥ 3,0 derajat saat matahari terbenam di titik penentu",
    },
    "schema.hilal_evening.elong_ok": {
        "en": "Elongation >= 6.4 degrees at the deciding site's sunset",
        "id": "Elongasi ≥ 6,4 derajat saat matahari terbenam di titik penentu",
    },
    "schema.hilal_evening.visible": {
        "en": (
            "True when the criteria are met at any coastal observation site in "
            "Indonesia — not a claim of actual observation"
        ),
        "id": (
            "Bernilai true jika kriteria terpenuhi di setidaknya satu titik "
            "pengamatan pesisir di Indonesia; bukan klaim pengamatan sesungguhnya"
        ),
    },
    "schema.hilal_history.from": {
        "en": "First Hijri YYYY-MM (inclusive)",
        "id": "Bulan Hijriah awal `YYYY-MM` (inklusif)",
    },
    "schema.hilal_history.to": {
        "en": "Last Hijri YYYY-MM (inclusive)",
        "id": "Bulan Hijriah akhir `YYYY-MM` (inklusif)",
    },
    "schema.hilal_history.range": {
        "en": "Hijri YYYY-MM span covered by the precomputed index",
        "id": "Rentang Hijriah `YYYY-MM` yang dicakup indeks terhitung",
    },
}


def t(key: str) -> str:
    """Return the documentation string for ``key`` in the active language.

    Falls back to English when the active language has no entry, so a missing
    translation degrades to a readable reference instead of raising.
    """
    entry = _STRINGS[key]
    return entry.get(LANG) or entry["en"]


def available() -> list[str]:
    """Languages that have at least one translation in this catalogue."""
    return sorted({lang for entry in _STRINGS.values() for lang in entry})
