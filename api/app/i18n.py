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
            "## MABIMS API\n\n"
            "MABIMS.dev is an unofficial, free, open-source API for the "
            "Indonesian Hijri calendar. Get today's Hijri date, date conversion, "
            "monthly and yearly calendars, hilal visibility, and Islamic events "
            "based on official MABIMS data from Kementerian Agama RI.\n\n"
            "This page is a **playground** to try the endpoints interactively. "
            "For quickstart guides and full documentation, visit "
            "[mabims.dev/quickstart](https://mabims.dev/quickstart)."
        ),
        "id": (
            "## MABIMS API\n\n"
            "MABIMS.dev adalah API unofficial, gratis, dan open-source untuk "
            "kalender Hijriah Indonesia. Ambil tanggal Hijriah hari ini, "
            "konversi tanggal, kalender bulanan dan tahunan, data visibilitas "
            "hilal, serta hari besar Islam berdasarkan data resmi MABIMS dari "
            "Kementerian Agama RI.\n\n"
            "Halaman ini adalah **playground** untuk mencoba endpoint secara "
            "interaktif. Untuk panduan awal dan dokumentasi lengkap, kunjungi "
            "[mabims.dev/quickstart](https://mabims.dev/quickstart)."
        ),
    },
    "app.basics": {
        "en": (
            "\n\n## API-wide behavior\n\n"
            "- **No authentication** — every endpoint is public; rate limits are per IP.\n"
            "- **HEAD works on every endpoint** with the same headers and no body.\n"
            "- **ETag revalidation** — every 200 response carries an `ETag`; send "
            "`If-None-Match` with it (weak comparison, or `*`) and the origin replies "
            "**304 Not Modified** with the same `Cache-Control` and `ETag` headers.\n"
            "- **Uniform error envelope** — every error (validation, 404, 429, …) is "
            "`{\"error\": {\"code\": \"...\", \"message\": \"...\"}}`; 429s include a "
            "`Retry-After` header in seconds.\n"
            "- **Values are case-insensitive** where spelled (`calendar=hijri`, "
            "`retro=true`); boolean flags also accept `1`/`0`.\n"
            "- **CORS is open** — all origins are allowed. Self-hosters can restrict "
            "via `ALLOWED_ORIGINS`; restricted origins get 403 `forbidden_origin`."
        ),
        "id": (
            "\n\n## Perilaku lintas-endpoint\n\n"
            "- **Tanpa autentikasi** — semua endpoint publik; pembatasan laju per IP.\n"
            "- **HEAD tersedia di setiap endpoint** dengan header yang sama, tanpa body.\n"
            "- **Revalidasi ETag** — setiap respons 200 membawa `ETag`; kirim "
            "`If-None-Match` dengannya (perbandingan lemah, atau `*`) dan origin "
            "menjawab **304 Not Modified** dengan `Cache-Control` dan `ETag` yang sama.\n"
            "- **Amplop error seragam** — setiap error (validasi, 404, 429, …) berbentuk "
            "`{\"error\": {\"code\": \"...\", \"message\": \"...\"}}`; 429 menyertakan "
            "header `Retry-After` dalam detik.\n"
            "- **Nilai tidak peka huruf besar/kecil** untuk nilai bertuliskan "
            "(`calendar=hijri`, `retro=true`); flag boolean menerima `1`/`0`.\n"
            "- **CORS terbuka** — semua origin diizinkan. Self-hoster bisa membatasi "
            "lewat `ALLOWED_ORIGINS`; origin terlarang mendapat 403 `forbidden_origin`."
        ),
    },
    "tag.today": {
        "en": "Today's Hijri date",
        "id": "Tanggal Hijriah hari ini",
    },
    "tag.convert": {
        "en": "Single date conversion (Gregorian/Hijri)",
        "id": "Konversi satu tanggal (Masehi/Hijriah)",
    },
    "tag.range": {
        "en": "Bulk date range conversion (up to 45 days)",
        "id": "Konversi massal rentang tanggal (maksimal 45 hari)",
    },
    "tag.month": {
        "en": "All days in a calendar month",
        "id": "Semua hari dalam satu bulan",
    },
    "tag.months": {
        "en": "Hijri month names",
        "id": "Nama bulan Hijriah",
    },
    "tag.year": {
        "en": "All days in a calendar year",
        "id": "Semua hari dalam satu tahun",
    },
    "tag.events": {
        "en": "Islamic observances: Ramadan, Eid, 1 Muharram, Maulid",
        "id": "Hari besar Islam: Ramadan, Idul Fitri, Idul Adha, 1 Muharram, Maulid Nabi",
    },
    "tag.hilal": {
        "en": "Hilal visibility data and sky charts",
        "id": "Data visibilitas hilal dan grafik langit",
    },
    "tag.meta": {
        "en": "Data coverage, computation status, and table version",
        "id": "Cakupan data, status komputasi, dan versi tabel",
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
            "Liveness probe for uptime monitors. Never cached."
        ),
        "id": (
            "Probe liveness untuk monitor uptime. Tidak pernah di-cache."
        ),
    },
    "meta.summary": {
        "en": "API metadata",
        "id": "Metadata API",
    },
    "meta.description": {
        "en": (
            "Machine-readable dataset info: data version, table coverage, "
            "computed-tier status, hilal render range, and Sidang Isbat "
            "corrections."
        ),
        "id": (
            "Info dataset yang machine-readable: versi data, cakupan "
            "tabel, status tier komputasi, rentang render hilal, dan "
            "koreksi Sidang Isbat."
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
            "Gregorian to Hijri when `calendar=gregorian`, Hijri to Gregorian "
            "when `calendar=hijri`. Timezone-independent."
        ),
        "id": (
            "Mengkonversi satu tanggal Masehi ke Hijriah saat "
            "`calendar=gregorian`, dan Hijriah ke Masehi saat "
            "`calendar=hijri`. Tidak bergantung pada zona waktu."
        ),
    },
    "today.summary": {
        "en": "Today's Hijri date",
        "id": "Tanggal Hijriah hari ini",
    },
    "today.description": {
        "en": (
            "Returns the Hijri date for today in the requested timezone."
        ),
        "id": (
            "Mengembalikan tanggal Hijriah untuk hari ini di zona waktu yang diminta."
        ),
    },
    "today_on.summary": {
        "en": "Hijri date for a fixed Gregorian date",
        "id": "Tanggal Hijriah untuk tanggal Masehi tertentu",
    },
    "today_on.description": {
        "en": (
            "Same as /today but for a fixed Gregorian date. Immutable, "
            "CDN-cacheable forever. Does not accept `tz`."
        ),
        "id": (
            "Sama seperti /today tapi untuk tanggal Masehi tertentu. "
            "Immutable, aman di-cache CDN selamanya. Tidak menerima `tz`."
        ),
    },
    "range.summary": {
        "en": "Bulk date conversion",
        "id": "Konversi massal rentang tanggal",
    },
    "range.description": {
        "en": (
            "Converts every day in an inclusive range, up to 45 days. "
            "Immutable, cacheable for a full day."
        ),
        "id": (
            "Mengkonversi setiap hari dalam rentang tanggal "
            "(maksimal 45 hari). Immutable, aman di-cache selama "
            "satu hari penuh."
        ),
    },
    "events.summary": {
        "en": "Islamic events for a year",
        "id": "Hari besar Islam dalam satu tahun",
    },
    "events.description": {
        "en": (
            "Returns Islamic observance dates for a year. Base events (1 Muharram, "
            "Maulid Nabi, Awal Ramadan, Idul Fitri, Idul Adha) are always included; "
            "add `include=extra` for tier-2 observances (Isra Mi'raj, Nuzulul Quran, "
            "Arafah, Tasu'a, Asyura, Tasyrik), `include=ayyamul_bidh` for the white "
            "days (13-15 of every Hijri month), individual slugs to cherry-pick, "
            "or `all` for everything."
        ),
        "id": (
            "Mengembalikan tanggal hari penting Islam untuk satu tahun. Event dasar "
            "(1 Muharram, Maulid Nabi, Awal Ramadan, Idul Fitri, Idul Adha) selalu "
            "tersedia; tambahkan `include=extra` untuk peringatan tingkat dua "
            "(Isra Mi'raj, Nuzulul Quran, Arafah, Tasu'a, Asyura, Tasyrik), "
            "`include=ayyamul_bidh` untuk puasa hari putih (13-15 setiap bulan "
            "Hijriah), slug individual untuk memilih satu per satu, atau `all` "
            "untuk semuanya."
        ),
    },
    "month.summary": {
        "en": "All days in a month",
        "id": "Semua hari dalam satu bulan",
    },
    "months.summary": {
        "en": "List Hijri month names",
        "id": "Daftar nama bulan Hijriah",
    },
    "months.description": {
        "en": (
            "Returns the 12 Hijri month names with their numbers. "
            "Static, cacheable — use this to populate UI dropdowns."
        ),
        "id": (
            "Mengembalikan 12 nama bulan Hijriah beserta nomornya. "
            "Statis, dapat di-cache — gunakan ini untuk mengisi dropdown UI."
        ),
    },
    "month.description": {
        "en": (
            "Returns all days in a month. For `calendar=hijri`, each item "
            "is the Gregorian date that Hijri day falls on."
        ),
        "id": (
            "Mengembalikan semua hari dalam satu bulan. Untuk `calendar=hijri`, "
            "setiap item berisi tanggal Masehi yang menjadi acuan hari Hijriah "
            "tersebut."
        ),
    },
    "year.summary": {
        "en": "All days in a year",
        "id": "Semua hari dalam satu tahun",
    },
    "year.description": {
        "en": (
            "Returns all days across 12 months of a year."
        ),
        "id": (
            "Mengembalikan semua hari dalam 1 tahun "
            "(total 12 bulan baik Hijriah maupun Masehi)."
        ),
    },
    "hilal_info.summary": {
        "en": "Hilal visibility data",
        "id": "Data visibilitas hilal",
    },
    "hilal_info.description": {
        "en": (
            "Hilal visibility data for the evening deciding a Hijri month "
            "start. The Neo MABIMS criteria are evaluated at 25 coastal "
            "sites at local sunset."
        ),
        "id": (
            "Data visibilitas hilal untuk malam penentu awal bulan "
            "Hijriah. Kriteria Neo MABIMS dievaluasi di 25 titik "
            "pesisir saat matahari terbenam."
        ),
    },
    "hilal_history.summary": {
        "en": "Hilal history (precomputed)",
        "id": "Riwayat hilal (indeks terhitung)",
    },
    "hilal_history.description": {
        "en": (
            "Per-month hilal summary for a Hijri YYYY-MM range."
        ),
        "id": (
            "Ringkasan hilal per bulan untuk rentang Hijriah YYYY-MM."
        ),
    },
    "hilal_viz.summary": {
        "en": "Hilal sky chart PNG",
        "id": "Grafik langit hilal PNG",
    },
    "hilal_viz.description": {
        "en": (
            "Renders a 720x1280 sky chart PNG showing where to look for the "
            "hilal. Add `bare=true` for the panel-less web card, "
            "`download=true` to receive as attachment."
        ),
        "id": (
            "Mengembalikan PNG 720x1280 grafik langit senja untuk "
            "melihat hilal. Tambahkan `bare=true` untuk kartu tanpa "
            "panel, `download=true` untuk menerimanya sebagai attachment."
        ),
    },
    "hilal_map.summary": {
        "en": "Hilal visibility map PNG",
        "id": "Peta visibilitas hilal PNG",
    },
    "hilal_map.description": {
        "en": (
            "Renders a 720x1280 archipelago visibility map PNG. "
            "Add `bare=true` for the panel-less web card, "
            "`download=true` to receive as attachment."
        ),
        "id": (
            "Mengembalikan PNG 720x1280 peta visibilitas Nusantara. "
            "Tambahkan `bare=true` untuk kartu tanpa panel, "
            "`download=true` untuk menerimanya sebagai attachment."
        ),
    },
    "query.retro": {
        "en": (
            "Set true to allow computed retro dates below the curated table "
            "(from 1945-01-01). Boolean: `true`/`false` (case-insensitive), "
            "also accepts `1`/`0`; other values are rejected with 400 "
            "`invalid_retro`."
        ),
        "id": (
            "Set `true` untuk membuka tanggal retro komputasi di bawah "
            "tabel kurasi (dari 1945-01-01 sampai 2022-12-31), "
            "ditandai `mabims-retro`. Boolean: `true`/`false` (tidak peka "
            "huruf besar/kecil), juga menerima `1`/`0`; nilai lain ditolak "
            "dengan 400 `invalid_retro`."
        ),
    },
    "query.next": {
        "en": (
            "Set true to also return the Hijri date that begins after this "
            "evening's maghrib (the next civil day's mapping), as `next` with "
            "its own `source`. The API does not compute sunset, so gate the "
            "flip on your own prayer-time clock. Boolean: `true`/`false` "
            "(case-insensitive), also accepts `1`/`0`; other values are "
            "rejected with 400 `invalid_next`."
        ),
        "id": (
            "Jika di-set `true`, maka API akan mengembalikan juga objek "
            "`next` dengan `source` sendiri. Fungsinya untuk menunjukkan "
            "tanggal Hijriah setelah magrib malam ini. Kenapa? Karena hari "
            "Hijriah dimulai saat magrib, bukan tengah malam. API tidak "
            "menghitung waktu matahari terbenam, jadi tentukan momen magrib "
            "di sisi klien Anda. Boolean: `true`/`false` (tidak peka huruf "
            "besar/kecil), juga menerima `1`/`0`; nilai lain ditolak dengan "
            "400 `invalid_next`."
        ),
    },
    "query.bare": {
        "en": (
            "Set true to omit the criteria panel and return the high-resolution bare "
            "card (header + graphic + logo) used as the web hero image. Boolean: "
            "`true`/`false` (case-insensitive), also accepts `1`/`0`; other values "
            "are rejected with 400 `invalid_bare`."
        ),
        "id": (
            "Hanya untuk `viz` dan `map`: menghilangkan panel kriteria dan "
            "mengembalikan kartu resolusi tinggi 1440×1520 (header + grafik + logo) "
            "untuk dipakai sebagai gambar hero di web. Boolean: `true`/`false` "
            "(tidak peka huruf besar/kecil), juga menerima `1`/`0`; nilai lain "
            "ditolak dengan 400 `invalid_bare`."
        ),
    },
    "query.download": {
        "en": (
            "Set true to return Content-Disposition: attachment so the browser "
            "downloads the PNG instead of navigating to it. Boolean: "
            "`true`/`false` (case-insensitive), also accepts `1`/`0`; other "
            "values are rejected with 400 `invalid_download`."
        ),
        "id": (
            "Hanya untuk `viz` dan `map`: mengirim `Content-Disposition: attachment` "
            "sehingga browser mengunduh PNG alih-alih membukanya. Berguna karena "
            "atribut `download` HTML diabaikan untuk URL lintas-origin. Boolean: "
            "`true`/`false` (tidak peka huruf besar/kecil), juga menerima `1`/`0`; "
            "nilai lain ditolak dengan 400 `invalid_download`."
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
        "en": (
            "IANA timezone (e.g. `Asia/Jakarta`) or UTC offset (e.g. `+08:00`). "
            "Default is `Asia/Jakarta` (UTC+7). Only used by `/today`."
        ),
        "id": (
            "Zona waktu IANA (mis. `Asia/Jakarta`) atau UTC offset (mis. `+08:00`). "
            "Default `Asia/Jakarta` (UTC+7). Hanya dipakai oleh `/today`."
        ),
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
    "query.events_include": {
        "en": (
            "Optional extras, comma-separated: `extra` (tier-2 observances), "
            "`ayyamul_bidh`, individual slugs (isra_miraj, nuzulul_quran, arafah, "
            "tasua, asyura, tasyrik), or `all`. Base events are always included; "
            "invalid values are rejected with 400 `invalid_include`."
        ),
        "id": (
            "Tambahan opsional, dipisah koma: `extra` (peringatan tingkat dua), "
            "`ayyamul_bidh`, slug individual (isra_miraj, nuzulul_quran, arafah, "
            "tasua, asyura, tasyrik), atau `all`. Event dasar selalu disertakan; "
            "nilai tidak dikenal ditolak dengan 400 `invalid_include`."
        ),
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
            "The Hijri date that becomes current after this evening's maghrib. "
            "Only present when next=true."
        ),
        "id": (
            "Tanggal Hijriah yang berlaku setelah magrib malam ini. "
            "Hanya ada saat `next=true`."
        ),
    },
    "schema.event_date_range": {
        "en": (
            "Inclusive span of a multi-day event (day..day_end in Hijri). "
            "null for single-day events."
        ),
        "id": (
            "Rentang event multi-hari (day..day_end dalam Hijriah). "
            "null untuk event satu hari."
        ),
    },
    "schema.events_input.include": {
        "en": (
            "echo of the include query parameter; null when unset (base events only)"
        ),
        "id": (
            "gema dari query `include`; null saat tidak diisi (event dasar saja)"
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
            "Version token for the curated-table override history. Changes "
            "whenever a Sidang Isbat correction is applied."
        ),
        "id": (
            "Token versi riwayat koreksi. Berubah setiap kali koreksi "
            "Sidang Isbat diterapkan."
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
            "The coastal observation site whose sunset all reported values "
            "describe, the deciding site or the one closest to the criteria"
        ),
        "id": (
            "Titik pengamatan pesisir yang menjadi acuan semua nilai, "
            "titik penentu atau yang paling mendekati kriteria"
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
            "True when the criteria are met at any coastal site in Indonesia, "
            "not a claim of actual observation"
        ),
        "id": (
            "Bernilai true jika kriteria terpenuhi di setidaknya satu titik "
            "pesisir di Indonesia, bukan klaim pengamatan sesungguhnya"
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
