---
title: "Tabel MABIMS 2027 Sudah Masuk, Cakupan API Sampai Akhir 2027"
description: "Tabel resmi Kemenag untuk 2027 sudah masuk ke MABIMS API. Cakupan tabel kini mencapai 31 Desember 2027 dan seluruh awal bulan 2027 cocok dengan hitungan Neo MABIMS."
date: 2026-11-16
tags:
  - MABIMS
  - Kalender
  - Kemenag
  - Data
excerpt: "Kalender resmi Kemenag untuk 2027 sudah masuk ke MABIMS API. Cakupan tabel kini mencapai 31 Desember 2027 dan seluruh awal bulan 2027 cocok dengan hitungan Neo MABIMS."
cover:
  image: ../../../assets/kalender-2027.png
  alt: Kalender MABIMS 2027
authors:
  - pijar
---

MABIMS API kini menyajikan tanggal Hijriah dari kalender resmi Kementerian Agama RI sampai **31 Desember 2027**. Sebelumnya tabel berhenti di 31 Desember 2026. Perluasan ini menambah 13 awal bulan, dari Sya'ban 1448 sampai Sya'ban 1449.

## Cakupan baru dalam angka

| Keterangan | Sebelum | Sesudah |
|---|---|---|
| Awal cakupan | 23 Januari 2023 | 23 Januari 2023 |
| Akhir cakupan | 31 Desember 2026 | 31 Desember 2027 |
| Jumlah hari | 1.439 | 1.804 |

Penambahan ini juga terlihat di `hilal_index.json`. Tiga belas bulan yang sebelumnya dilayani dari perhitungan kini memakai data tabel, sehingga balasan `/hilal/history` untuk rentang tersebut tidak lagi membawa peringatan di luar tabel.

## Tidak ada selisih dengan hitungan Neo MABIMS

Sebelum masuk ke tabel, ketiga belas awal bulan itu dibandingkan dengan prediksi mesin Neo MABIMS yang sudah dipakai API untuk tanggal di luar tabel. Hasilnya, semuanya sama persis. Selisih nol hari untuk seluruh bulan.

Pemeriksaan dilanjutkan dengan validator yang menguji panjang setiap bulan terhadap kriteria hilal di 25 titik pengamatan pesisir. Dari 61 batas bulan, semuanya lolos. Tidak ada bulan yang gagal dan tidak ada bulan yang marginnya tipis, yaitu di bawah 0,25 derajat.

Karena tidak ada perbedaan, `divergences.json` tetap kosong. Berkas itu hanya mencatat koreksi Sidang Isbat, bukan selisih antara tabel dan hitungan.

## Apa artinya saat memanggil API

Selama tanggal berada di dalam tabel, kolom `source` bernilai `mabims`. Contoh untuk awal Sya'ban 1448:

```bash
curl "https://api.mabims.dev/api/v1/convert?date=2027-01-09&calendar=gregorian"
```

```json
{
  "input": { "date": "2027-01-09", "calendar": "gregorian", "tz": null },
  "output": {
    "date": "1448-08-01",
    "calendar": "hijri",
    "day": 1,
    "month": 8,
    "month_name": "Sya'ban",
    "year": 1448,
    "weekday": "Sabtu"
  },
  "source": "mabims",
  "warnings": []
}
```

Tanggal 1 Januari 2028 sudah berada di luar tabel. API tetap menjawab, tetapi `source` berubah menjadi `mabims-computed` dan balasan menyertakan peringatan. Artinya, tanggal tersebut dihitung dengan kriteria Neo MABIMS, bukan diambil dari tabel resmi.

| Tanggal | Hasil | Sumber |
|---|---|---|
| 9 Januari 2027 | 1 Sya'ban 1448 | `mabims` |
| 29 Desember 2027 | 1 Sya'ban 1449 | `mabims` |
| 1 Januari 2028 | 4 Sya'ban 1449 | `mabims-computed` |

## Catatan untuk bulan terakhir

Bulan 1449-08 baru tercatat tiga hari, yaitu 29 sampai 31 Desember 2027. Panjang bulan itu belum bisa diverifikasi karena awal bulan berikutnya, 1449-09, baru masuk tabel bersama data 2028. Sampai saat itu, hari-hari setelah 31 Desember 2027 tetap dilayani dari perhitungan.

## Penutup

Dengan perluasan ini, pengguna API mendapat tanggal resmi Kemenag sampai akhir 2027. Batas cakupan selalu bisa dicek di `GET /api/v1/meta` atau halaman [Cakupan Data](/data-coverage/). Kalau aplikasi kamu menampilkan tanggal setelah 31 Desember 2027, tetap periksa kolom `source` agar pengguna tahu bahwa tanggal tersebut masih merupakan hasil perhitungan.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Tabel MABIMS 2027 Sudah Masuk, Cakupan API Sampai Akhir 2027",
  "description": "Tabel resmi Kemenag untuk 2027 sudah masuk ke MABIMS API. Cakupan tabel kini mencapai 31 Desember 2027 dan seluruh awal bulan 2027 cocok dengan hitungan Neo MABIMS.",
  "datePublished": "2026-11-16",
  "author": {
    "@type": "Person",
    "name": "Pijar Adiluhung",
    "url": "https://pixostudio.id"
  },
  "publisher": {
    "@type": "Organization",
    "name": "mabims.dev",
    "logo": {
      "@type": "ImageObject",
      "url": "https://mabims.dev/mabims-long.png"
    }
  },
  "image": "https://mabims.dev/og-image.png",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://mabims.dev/blog/tabel-mabims-2027"
  }
}
</script>
