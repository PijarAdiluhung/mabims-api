---
title: Sidang Isbat & Koreksi
description: Ketika hasil Sidang Isbat beda dengan kalender terbit Kemenag, begini cara API menyampaikannya.
---

Kalender terbit Kemenag dihitung lewat kriteria Neo MABIMS, dan selama bertahun-tahun hasilnya selalu sama dengan keputusan Sidang Isbat. Tapi ingat: putusan awal bulan sebenarnya terjadi **malam Sidang Isbat** (rukyat hari ke-29), bukan murni hasil perhitungan. Kalau malam itu keputusannya beda dengan kalender terbit, API mengikuti **keputusan resmi**, dan akan menyampaikannya dengan jelas, agar tidak ada data yang salah.

## Kenapa bisa beda

Kalender terbit adalah prediksi imkanur ru'yah. Yang mengikat adalah keputusan malam pengamatan. Bedanya paling jauh 1 hari, dan dua bulan ikut terdampak:

- Bulan sebelum bulan terkoreksi: panjangnya berubah 29↔30 hari. Ini inti keputusan Isbat.
- Bulan-bulan setelahnya: tanggal mulainya tidak berubah. Sidang Isbat bulan masing-masing yang nanti akan memutuskan jika ada perubahan.

## Seperti apa bentuknya

Semua respons yang menyentuh bulan terkoreksi (atau bulan tepat sebelumnya) membawa warning:

```json
{
  "warnings": [
    "kemenag_override: 1 Syawal 1447 H resmi 2026-03-20 (Sidang Isbat; kalender terbit Kemenag: 2026-03-21, delta -1 hari)."
  ]
}
```

`source` tetap `mabims`, datanya sama, hanya dikoreksi.

`/meta` menyimpan riwayatnya, ringkas dua field:

```json
{
  "table_version": "1-a41d3c9be021",
  "divergences": [
    { "hijri_month": "1447-10", "delta_days": -1 }
  ]
}
```

## Yang tidak berubah

- Hasil kriteria Neo MABIMS (`mabims-computed`, kartu hilal) tetap benar secara astronomi. Koreksi isbat hanya diceritakan lewat warning, tidak mengubah hitungan astronomi.
- Bentuk respons, kode error, dan seluruh endpoint tidak berubah. Yang ditambahkan cuma field dan warning, tanpa breaking change.

## Cara klien menyesuaikan diri

1. Poll `/meta` sehari sekali (cache 5 menit, murah).
2. Simpan `table_version`. Nilai `"none"` artinya belum pernah ada koreksi.
3. Kalau nilainya berubah: baca `divergences[]` untuk tahu bulan mana yang terkoreksi dan bergesernya berapa hari, lalu tarik ulang tanggal di bulan itu dan bulan sebelumnya.
4. Alternatif paling praktis: tangkap prefix `kemenag_override:` di array `warnings[]` dari respons mana pun, lalu tampilkan ke pengguna.

## Riwayat

> Sampai hari ini **belum pernah ada koreksi**, sehingga `divergences[]` kosong dan `table_version` = `"none"`. Halaman ini akan diperbarui begitu ada Sidang Isbat yang mengoreksi kalender terbit.

Catatan teknis soal cara skrip mengoreksi tabel ada di `SIDANG-ISBAT-FLIP.md` di repo.
