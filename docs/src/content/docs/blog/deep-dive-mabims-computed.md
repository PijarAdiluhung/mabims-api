---
title: "Deep Dive: Di Balik mabims-computed"
description: "Bedah teknis fallback kalender MABIMS: dari posisi hilal, keputusan 29 atau 30 hari, seed table, sampai kenapa altitudnya toposentris tapi elongasinya geosentris."
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

Jadi di tulisan ini saya mau membedah bagian yang biasanya tidak kelihatan dari luar: bagaimana satu bulan diputuskan punya 29 atau 30 hari, kenapa altitudnya toposentris tapi elongasinya geosentris, dan kenapa kriterianya dievaluasi di 25 titik pengamatan pesisir.

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
    "Date is outside the curated MABIMS table; computed with the Neo MABIMS criteria (moon altitude >= 3 deg and elongation >= 6.4 deg at local sunset, seen anywhere across the coastal observation sites of Indonesia)."
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

Keduanya harus lolos bersamaan, dan cukup lolos di **satu titik manapun**. Tinggi hilal lolos tapi elongasi tidak cukup berarti belum lolos. Sebaliknya juga sama.

Kriteria ini dievaluasi pada waktu matahari terbenam **lokal di masing-masing titik pengamatan** — saat ini **25 titik pesisir** dari Sabang sampai Rote (daftarnya terbuka di `api/data/hilal_sites.json`). Pola menariknya: untuk bulan-bulan yang "aman", hampir selalu titik paling barat yang memutuskan, karena semakin barat, matahari terbenam semakin mundur dan hilal semakin tinggi di atas horizon saat senja. Tapi ada bulan-bulan dengan deklinasi bulan selatan di mana arc selatan (selatan Jawa sampai Nusa Tenggara) yang menang. Itu sebabnya titik-titik selatan ikut masuk daftar.

Dan ini bukan jimat "wajib Sabang" — ini persis logika rukyah Kemenag: hilal terlihat di wilayah Indonesia, bulan baru dimulai. Respons API bahkan melaporkan titik yang memutuskan lewat `deciding_site`.

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

Secara intuisi, topocentric memang lebih benar untuk pengamatan hilal — manusia mengamati dari permukaan bumi. Setelah saya validasi ulang dari ujung ke ujung: intuisi itu benar. Mesin di atas akhirnya menemukan bentuk yang pas: ketinggian hilal dihitung **topocentric** (terkoreksi refraksi) di **25 titik pengamatan pesisir** dari Sabang sampai Rote, sementara elongasi tetap **geocentric** sesuai konvensi hisab Indonesia — dan kriteria cukup terpenuhi di satu titik manapun. Hasilnya tetap 48/48 terhadap tabel kurasi: semua penjelasan di atas soal keputusan 29/30 hari tidak berubah, yang berubah hanyalah "di mana" dan "bingkai hitung"-nya.

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
3. Kriteria dievaluasi pada sunset lokal masing-masing dari 25 titik pengamatan pesisir; cukup terpenuhi di satu titik manapun.
4. Dua ambang, altitude 3° dan elongasi 6,4°, harus lolos bersamaan.
5. Altitud dihitung toposentris (dengan refraksi), elongasi tetap geosentris — modelnya tervalidasi 48/48 terhadap tabel kurasi.
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
  "description": "Bedah teknis fallback kalender MABIMS: dari posisi hilal, keputusan 29 atau 30 hari, seed table, sampai kenapa altitudnya toposentris tapi elongasinya geosentris.",
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
