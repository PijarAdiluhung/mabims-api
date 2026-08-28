---
title: "Kenapa Cari Hilal di Sabang?"
description: "Bedah teknis endpoint /hilal/viz. Astronomi geosentrik, kriteria Neo MABIMS, sampai cara chart PNG-nya dirender dari nol."
date: 2026-08-29
tags:
  - Astronomi
  - Hilal
  - Visualisasi
  - MABIMS
excerpt: "Salah satu endpoint yang paling saya suka di mabims.dev bukan /today atau /convert, tapi /hilal/viz. Endpoint ini generate PNG 720×1280 yang nampilin visualisasi langit senja lengkap dengan posisi bulan, status kelolosan kriteria MABIMS, sampai grafik langit dengan bintang-bintang segala. Deep dive ke behind the scenenya"
cover:
  image: ../../../assets/hilal.jpg
  alt: Visualisasi hilal dari endpoint /hilal/viz
authors:
  - pijar
---

Salah satu endpoint yang paling saya suka di mabims.dev bukan `/today` atau `/convert`, tapi `/hilal/viz`. Endpoint ini generate PNG 720×1280 yang nampilin visualisasi langit senja lengkap dengan posisi bulan, status kelolosan kriteria MABIMS, sampai grafik langit dengan bintang-bintang segala.

Nggak ada API kalender Hijriah lain (setidaknya yang saya temukan) yang punya fitur ini. Jadi tulisan ini bahas gimana cara kerjanya, dari astronomi sampai render pixel.

## Kenapa Sabang?

Ini pertanyaan yang paling sering saya dapat. Jawabannya simpel: **Sabang adalah titik paling barat Indonesia.**

Untuk urusan rukyah (pengamatan hilal), posisi geografis penting, karena semakin barat, maka matahari terbenam semakin mundur. Artinya, kalau hilal tidak memenuhi kriteria di tempat lain, *last chance* nya akan terjadi di Sabang.

Ini bukan aturan resmi MABIMS soal "wajib pakai Sabang", tapi jadi titik acuan praktis yang masuk akal untuk representasi visibilitas hilal se-Indonesia dalam satu titik koordinat.

## Alur Kerjanya

Simplifikasi dari implementasi aslinya kira-kira begini:

```
FUNCTION hilal_viz(month, year):
  sighting = resolve_sighting_evening(year, month)
  observation = observe_sighting_evening(sighting.evening_date)
  alt_ok = observation.moon_alt >= 3.0°
  elong_ok = observation.elongation >= 6.4°
  data = build_chart_data(...)
  img = render_chart(data)
  return PNG
```

### 1. Resolve malam pengamatan

Kalau kamu minta visibilitas untuk bulan Ramadhan, endpoint ini nggak menghitung tanggal 1 Ramadhan itu sendiri, tapi mundur ke **malam ke-29 Sya'ban**, karena itu malam yang sebenarnya diamati untuk menentukan apakah besok sudah masuk Ramadhan atau belum. Ini logika dasar rukyah: kamu mengamati hilal di ujung bulan berjalan, bukan di awal bulan target.

### 2. Hitung astronomi malam itu, dari Sabang

Dua kategori data dihitung:

- **Kriteria geosentrik** — `moon_alt` (altitude/ketinggian bulan), `moon_az` (azimuth), `sun_alt`, dan `elongation` (jarak sudut bulan-matahari). Ini angka-angka yang langsung dibandingkan ke ambang batas MABIMS.
- **Waktu pengamat (observer-clock)** — iluminasi, jam matahari terbenam lokal, dan jam bulan terbenam. Ini yang ditampilkan sebagai info tambahan di kartu bawah. 

### 3. Cek ambang batas Neo MABIMS

```
alt_ok  = moon_alt   >= 3.0°
elong_ok = elongation >= 6.4°
```

Dua syarat ini harus terpenuhi bersamaan. Kalau salah satu gagal, hilal dianggap belum memenuhi kriteria visibilitas, meskipun bulan sudah di atas horizon.

## Contoh Hasil

<img src="/viz.png" alt="Visualisasi hilal dari endpoint /hilal/viz" style="max-width: min(420px, 100%); display: block;" />

Screenshot di atas itu visibilitas untuk 1 Muharram 1448 H (evaluasi malam 29 Dzulhijjah 1447 H, 15 Jun 2026, dari Sabang):

- Altitude bulan +5.0° (lolos, syarat ≥3.0°)
- Elongasi 7.0° (lolos, syarat ≥6.4°)
- Iluminasi 0.2% — sangat tipis, hilal masih sangat muda
- Matahari terbenam 18:53, bulan terbenam 19:11, cuma selisih 18 menit

Status: **TERLIHAT**, meski dengan margin yang nggak terlalu lebar.

## Kenapa Repot-repot Bikin Ini?

Karena angka mentah (`moon_alt: 5.2, elongation: 8.7`) nggak intuitif buat kebanyakan orang, termasuk saya sendiri. Tapi begitu divisualisasikan -> lihat posisi bulan relatif ke horizon, lihat pill hijau/merah, lihat tabel kriteria -> jadi jauh lebih gampang dicerna. Endpoint ini niatnya bukan cuma buat developer yang butuh JSON, tapi juga buat siapa saja yang penasaran "kok bisa sih hilal dibilang terlihat/tidak terlihat" tanpa harus paham astronomi.

Coba sendiri di [playground](/playground/hilal):

```
GET https://api.mabims.dev/api/v1/hilal/viz?month=1&year=1448
```

Ganti `month` dan `year` sesuai bulan Hijriah yang mau dicek. Dokumentasi lengkap parameter ada di [mabims.dev/endpoints/hilal](https://mabims.dev/endpoints/hilal).
