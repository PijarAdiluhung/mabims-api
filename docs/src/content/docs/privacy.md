---
title: Kebijakan Privasi
description: Bagaimana API MABIMS menangani data Anda — tidak ada tracking, tidak ada cookie.
---

## Tanpa Pelacakan

API ini **tidak menggunakan** cookie, fingerprinting, analytics, atau pelacakan pengguna apa pun. Tidak ada akun pengguna, tidak ada data yang dikumpulkan secara aktif.

## Log Server

Seperti layanan web pada umumnya, log akses standar dicatat oleh server (VPS dan CDN):

| Data | Tujuan | Penyimpanan |
|---|---|---|
| Alamat IP | Identifikasi untuk batas rate dan debugging | Diputar secara otomatis, dihapus dalam hitungan hari |
| Timestamp | Debugging dan audit | Diputar secara otomatis |
| User-Agent | Identifikasi klien (opsional) | Diputar secara otomatis |

Log ini **tidak digunakan** untuk pelacakan, profil pengguna, atau tujuan selain operasional teknis.

## Pembatasan Rate

Batas rate diterapkan berdasarkan alamat IP (240 permintaan/menit). IP hanya digunakan untuk mencegah penyalahgunaan dan tidak disimpan secara permanen.

## CDN

Bunny CDN digunakan untuk caching. Node edge CDN dapat memproses alamat IP Anda sesuai dengan [kebijakan privasi Bunny CDN](https://bunny.net/privacy-policy/). Cache bersifat publik — semua klien menerima respons yang sama untuk parameter yang sama.

## Tidak Ada Penyimpanan Data

API bersifat stateless:
- Tidak ada body request yang disimpan
- Tidak ada session yang dilacak
- Tidak ada data pengguna yang direkam

## Hubungi

Untuk pertanyaan mengenai privasi, hubungi [halo@pixostudio.id](mailto:halo@pixostudio.id).
