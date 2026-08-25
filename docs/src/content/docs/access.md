---
title: Akses & Batas Rate
description: Siapa yang dapat memanggil API, aturan origin browser, dan perlindungan penyalahgunaan.
---

## Semua pembacaan bersifat publik

Setiap endpoint di `/api/v1/*` bersifat **publik** — tidak perlu kunci, tidak perlu registrasi. Tanggal kalender bukanlah rahasia, dan membatasinya hanya akan mendorong integrator ke sumber data yang lebih buruk.

## Akses browser vs server

| Klien | Perilaku |
|---|---|
| Server-side (curl, backend, cron) | Selalu diizinkan — CORS tidak berlaku |
| Browser | Diizinkan dari origin mana pun |

Respons dilayani dengan header CORS yang fleksibel, sehingga aplikasi client-side di domain mana pun dapat memanggil API secara langsung.

:::note[Men_deploy batasan sendiri?]
Self-hoster dapat mengaktifkan kembali daftar origin yang diizinkan melalui variabel environment `ALLOWED_ORIGINS` (origin persis yang dipisah koma, atau `*` untuk publik — default). Aturan berbasis suffix (`ALLOWED_ORIGIN_SUFFIXES`) juga memungkinkan apex + semua subdomain dari sebuah domain.
:::

## Batas rate & caching

- **Origin** menerapkan batas rate per-IP (default 240/menit, `429` ketika dilebihi) murni sebagai perlindungan penyalahgunaan.
- Di produksi API berada di belakang CDN: permintaan yang identik dilayani di edge dan tidak pernah mencapai origin. Dengan jutaan permintaan/hari, origin hanya melihat sekitar satu permintaan per lokasi edge per sumber daya yang di-cache per hari.
- Respons [`/today`](/endpoints/today) membawa TTL yang kedaluwarsa tepat pada tengah malam waktu lokal, sehingga jawaban yang di-cache tidak pernah basi setelah pergantian hari.

## Batas lebih tinggi / penggunaan komersial

Membutuhkan rate yang dijamin, SLA, atau ingin mendukung proyek ini?
Hubungi [halo@pixostudio.id](mailto:halo@pixostudio.id).
