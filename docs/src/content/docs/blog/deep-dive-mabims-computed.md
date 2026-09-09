---
title: "Deep Dive: Sebenarnya Apa yang Terjadi di Balik mabims-computed?"
description: "Bedah teknis fallback kalender MABIMS: dari posisi hilal di Sabang, keputusan 29 atau 30 hari, seed table, sampai kenapa perhitungan geocentric dipertahankan."
date: 2026-09-09
tags:
  - MABIMS
  - Astronomi
  - Backend
  - Python
  - Deep Dive
excerpt: "Kalau tanggal yang kamu minta berada di luar tabel Kemenag, MABIMS API tidak menebak secara acak. Ia menghitung ulang panjang bulan berdasarkan kriteria Neo MABIMS. Tulisan ini membedah mesin di balik source mabims-computed."
cover:
  image: ../../../assets/hilal.jpg
  alt: Perhitungan hilal dan kalender MABIMS
authors:
  - pijar
---

Di MABIMS API ini saya beberapa kali menyebut `source: "mabims-computed"` sebagai fallback.

Di post ini kita akan melihat lebih dalam bagaimana seluk beluknya. `mabims-computed` bukan cuma "kalau data tidak ada, pakai perkiraan". Di baliknya ada mesin kecil yang menghitung kapan bulan Hijriah dimulai, berjalan maju atau mundur dari tanggal anchor, menyimpan hasilnya, dan memberi tahu client kalau hasil yang diterima bukan data resmi Kemenag.

Jadi di tulisan ini saya mau membedah bagian yang biasanya tidak kelihatan dari luar: bagaimana satu bulan diputuskan punya 29 atau 30 hari, kenapa lokasi referensinya Sabang, apa bedanya geocentric dan topocentric, dan kenapa saya memilih tetap memakai geocentric meskipun hasilnya sedikit kontraintuitif.

## Dua jenis data, satu API

MABIMS API punya dua sumber utama:

- `mabims` — tanggal dari kalender publik Kemenag RI.
- `mabims-computed` — tanggal yang dihitung dengan kriteria Neo MABIMS ketika berada di luar cakupan tabel.

Misalnya tanggal yang masih ada di tabel:

```json
{
  "output": {
    "date": "1447-09-01",
    "calendar": "hijri",
    "day": 1,
    "month": 9,
    "month_name": "Ramadhan",
    "year": 1447
  },
  "source": "mabims",
  "warnings": []
}
```

Kalau tanggalnya sudah di luar tabel, bentuk responsnya tetap sama, tapi sumbernya berubah:

```json
{
  "output": {
    "date": "1450-01-01",
    "calendar": "hijri",
    "day": 1,
    "month": 1,
    "month_name": "Muharram",
    "year": 1450
  },
  "source": "mabims-computed",
  "warnings": [
    "Date is outside the curated MABIMS table; computed with the Neo MABIMS criteria (hilal altitude >= 3 deg and elongation >= 6.4 deg at Sabang sunset)."
  ]
}
```

Saya sengaja tidak menyamakan dua sumber ini. Hasil komputasi bisa sangat berguna untuk kalender aplikasi, tetapi tidak boleh dibaca sebagai pengumuman resmi atau pengganti sidang isbat.

## Neo MABIMS dalam dua angka

Versi singkat kriterianya adalah:

```text
tinggi hilal   >= 3.0°
elongasi       >= 6.4°
```

Keduanya harus lolos bersamaan. Tinggi hilal lolos tapi elongasi tidak cukup berarti belum lolos. Sebaliknya juga sama.

Perhitungan dilakukan pada waktu matahari terbenam di Sabang, kurang lebih pada koordinat 5°53′ LU, 95°19′ BT. Sabang dipakai sebagai titik referensi praktis karena merupakan titik paling barat Indonesia. Untuk satu representasi Indonesia, ini masuk akal: wilayah paling barat biasanya mendapat kesempatan melihat hilal paling akhir.

Ini bukan berarti aturan resmi MABIMS berbunyi "semua orang wajib melihat dari Sabang". Sabang adalah titik referensi yang saya gunakan untuk mesin komputasi ini.

## Dari hilal ke panjang bulan

Perhitungan kalendernya sebenarnya bisa diringkas menjadi fungsi kecil:

```python
def month_length(month_start):
    result = criteria_on_day29(month_start)
    return 29 if result.visible else 30
```

`criteria_on_day29()` mengevaluasi matahari terbenam pada malam ke-29 bulan berjalan. Kalau dua kriteria terpenuhi, bulan selesai setelah 29 hari. Kalau tidak, bulan berjalan menjadi 30 hari.

Dengan kata lain, untuk menentukan awal Ramadhan, yang diperiksa bukan malam pertama Ramadhan. Yang diperiksa adalah malam ke-29 Sya'ban. Kalau hilalnya memenuhi kriteria, besoknya 1 Ramadhan. Kalau tidak, Sya'ban digenapkan menjadi 30 hari.

Alur sederhananya kira-kira seperti ini:

```text
awal bulan Hijriah yang diketahui
             ↓
evaluasi sunset pada malam ke-29
             ↓
altitude >= 3° dan elongation >= 6.4°?
          ↙                      ↘
       ya                        tidak
   bulan 29 hari              bulan 30 hari
          ↓                      ↓
   awal bulan berikutnya = start + panjang bulan
```

Karena setiap bulan berikutnya dimulai dari akhir bulan sebelumnya, mesin ini bisa membangun kalender secara berantai.

## Bukan konversi aritmetika biasa

Kalender Hijriah tabular biasanya bisa dihitung dengan pola aritmetika: bulan-bulan punya susunan panjang tertentu, lalu siklus tahun kabisat menentukan posisi 29 dan 30 hari.

`mabims-computed` tidak bekerja seperti itu. Panjang bulan ditentukan satu per satu dari kondisi astronomis pada malam ke-29. Jadi mesin ini lebih mirip linked list daripada rumus satu baris:

```text
1449-01-01
   └─ cek hilal → 29 atau 30 hari
       └─ 1449-02-01
           └─ cek hilal → 29 atau 30 hari
               └─ 1449-03-01
```

Konsekuensinya, kita butuh satu titik awal yang dipercaya. Di aplikasi, titik itu berasal dari batas tabel resmi Kemenag RI. Untuk tanggal sesudah tabel, mesin berjalan maju dari anchor tersebut.

## Bisa berjalan mundur juga

Untuk tanggal sebelum kalender resmi, API tidak langsung mengizinkan komputasi. Request perlu menyertakan `retro=true`.

Alasannya sederhana: kriteria Neo MABIMS baru diperkenalkan pada 2022. Kalau kita memproyeksikan kriteria itu ke tahun 1990, hasilnya bukan data historis resmi. Itu adalah rekonstruksi menggunakan aturan masa kini.

Karena itu ada sumber ketiga:

```text
source: "mabims-retro"
```

Label ini berarti hasilnya dihitung mundur menggunakan kriteria yang sama, bukan diambil dari tabel resmi masa lalu. API juga memberi warning supaya perbedaan status ini tidak hilang di sisi client.

Secara internal, berjalan mundur sedikit lebih rumit daripada maju. Kalau kita tahu tanggal 1 bulan berikutnya, kita perlu mengecek sunset pada h-31 hari untuk menentukan apakah bulan sebelumnya panjangnya 29 atau 30 hari. Setelah itu tanggal awal bulan sebelumnya bisa ditentukan.

## Bagian yang bikin saya harus investigasi ulang

Awalnya saya mengira pertanyaannya sederhana: untuk menghitung kriteria hilal, seharusnya pakai koordinat pengamat di permukaan bumi atau posisi dari pusat bumi?

Istilahnya:

- **Topocentric** — dilihat dari permukaan bumi, memperhitungkan posisi observer dan paralaks bulan.
- **Geocentric** — dilihat dari pusat bumi.

Secara intuisi, topocentric terdengar lebih benar untuk pengamatan hilal karena manusia memang mengamati dari permukaan bumi. Tapi masalahnya tidak berhenti di situ... Ada alasan lain kenapa saya pakai geocentric di API ini. Ah tapi mungkin deep divenya menyusul di lain hari (stay tuned!).

## Borderline itu nyata

Kembali ke topik. Lolos kriteria bukan berarti posisinya jauh di atas ambang.

Misalnya hasilnya:

```text
altitude  = 3.12°
elongation = 7.01°
```

Secara boolean, ini lolos. Tapi margin terdekatnya hanya 0,12° dari ambang altitude. Karena itu provider menyimpan margin terkecil:

```python
margin = min(
    altitude - 3.0,
    elongation - 6.4,
)
```

Kalau margin positif tapi kurang dari 0,25°, bulan ditandai borderline. Informasi ini ikut masuk ke `warnings[]` agar aplikasi tidak memperlakukan hasil yang sangat dekat ambang sebagai sesuatu yang pasti.

Catatan penting: borderline bukan berarti hasilnya otomatis salah. Ia hanya berarti perubahan kecil pada lokasi, metode, data ephemeris, atau interpretasi kriteria bisa memengaruhi hasil.

## Jadi kapan `mabims-computed` boleh dipakai?

Menurut saya, cocok untuk:

- kalender aplikasi yang membutuhkan cakupan tahun lebih panjang;
- preview tanggal hari besar di masa depan;
- fitur konversi tanggal yang tidak punya tabel resmi;
- riset, eksperimen, dan visualisasi hilal;
- fallback teknis ketika data resmi belum tersedia.

Jangan perlakukan sebagai:

- pengumuman resmi awal Ramadhan atau Idul Fitri;
- pengganti sidang isbat;
- bukti observasi hilal di lokasi tertentu;
- sumber tunggal untuk keputusan administratif atau keagamaan.

Di sisi client, minimal selalu cek dua field ini:

```js
if (data.source === "mabims-computed") {
  console.warn("Tanggal ini adalah estimasi algoritmik, bukan data resmi.");
}

if (data.warnings?.length) {
  console.warn(data.warnings);
}
```

## Intinya

`mabims-computed` adalah kompromi yang cukup sadar:

1. Tabel resmi dipakai kalau tersedia.
2. Di luar tabel, panjang bulan dihitung dari kriteria Neo MABIMS.
3. Perhitungan dilakukan pada sunset di Sabang.
4. Dua ambang, altitude 3° dan elongasi 6,4°, harus lolos bersamaan.
5. Geocentric dipertahankan karena paling cocok dengan keputusan kalender kurasi yang divalidasi.
6. Hasil diberi label dan warning supaya tidak disalahpahami sebagai data resmi.

Kalau kamu cuma memanggil `/today`, semua kerumitan ini memang tidak perlu kelihatan. Tapi saat kamu meminta kalender tahun 2050, atau bertanya kenapa satu bulan punya 29 hari dan bulan lain 30 hari, inilah yang terjadi di belakang layar.

Coba sendiri:

```bash
curl "https://api.mabims.dev/api/v1/events?year=2050&calendar=gregorian"
```

Perhatikan field `source` dan `warnings` pada responsnya. Dokumentasi endpoint dan status cakupan data ada di [mabims.dev/data-sources](https://mabims.dev/data-sources).

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Deep Dive: Sebenarnya Apa yang Terjadi di Balik mabims-computed?",
  "description": "Bedah teknis fallback kalender MABIMS: dari posisi hilal di Sabang, keputusan 29 atau 30 hari, seed table, sampai kenapa perhitungan geocentric dipertahankan.",
  "datePublished": "2026-09-09",
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
    "@id": "https://mabims.dev/blog/deep-dive-mabims-computed"
  }
}
</script>
