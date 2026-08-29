---
title: Akses & Batas Rate
description: Siapa saja yang dapat memanggil API, aturan origin browser, dan perlindungan penyalahgunaan.
---

## Semua reads bersifat publik

Setiap endpoint di `/api/v1/*` bersifat **publik**, tidak perlu API key dan tidak perlu registrasi, untuk memudahkan para developer mengintegrasikannya ke aplikasi / web.

## Akses browser vs server

| Klien | Perilaku |
|---|---|
| Server-side (curl, backend, cron) | Selalu diizinkan, CORS tidak berlaku |
| Browser | Diizinkan dari origin mana pun |

Respons dilayani dengan header CORS yang fleksibel, sehingga aplikasi client-side di domain mana pun dapat memanggil API secara langsung.

:::note[Men-deploy sendiri?]
Self-hoster dapat mengaktifkan kembali daftar origin yang diizinkan melalui variabel environment `ALLOWED_ORIGINS` (origin persis yang dipisah koma, atau `*` untuk publik — default). Aturan berbasis suffix (`ALLOWED_ORIGIN_SUFFIXES`) juga memungkinkan apex + semua subdomain dari sebuah domain.
:::

## Batas rate & caching

- **CDN edge** (Bunny CDN): 4 request/detik per IP secara terus-menerus, burst 24. Ini adalah
  batas rate utama — sebagian besar permintaan tidak pernah mencapai origin.
- **Origin** (FastAPI): 240/menit per IP sebagai cadangan jika CDN dilewati. Endpoint hilal
  (`/hilal/info`, `/hilal/viz`) lebih ketat di origin (60 atau 30/jam) karena komputasi berat,
  namun batas per-endpoint di CDN belum dikonfigurasi.
- Permintaan yang identik dilayani dari cache CDN dan tidak pernah mencapai origin. Dengan
  jutaan permintaan/hari, origin hanya melihat sekitar satu permintaan per lokasi edge per
  sumber daya yang di-cache per hari.
- Respons [`/today`](/endpoints/today) membawa TTL yang kedaluwarsa tepat pada tengah malam
  waktu lokal, sehingga jawaban yang di-cache tidak pernah basi setelah pergantian hari.

## Batas lebih tinggi / penggunaan komersial

Membutuhkan rate yang dijamin, SLA, atau ingin mendukung proyek ini?
Hubungi [halo@pixostudio.id](mailto:halo@pixostudio.id).
