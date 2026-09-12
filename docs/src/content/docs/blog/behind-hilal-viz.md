---
title: "Di Mana Cari Hilal?"
description: "Bedah teknis endpoint /hilal/viz. Kriteria Neo MABIMS di titik-titik pengamatan pesisir, titik penentu, sampai cara chart PNG-nya dirender dari nol."
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

Nggak ada API kalender Hijriah lain (setidaknya yang saya temukan) yang punya fitur ini. Jadi tulisan ini bahas gimana cara kerjanya, dari [astronomi](https://en.wikipedia.org/wiki/Astronomy) sampai render pixel.

## Di Mana Cari [Hilal](https://en.wikipedia.org/wiki/Hilal)?

Nah ini pertanyaan yang sering muncul: **Di mana kita mengevaluasi kriteria hilal Neo MABMIS?**

Kriteria [Neo MABIMS](https://mui.or.id/baca/berita/mengenal-kriteria-hilal-mabims-standard-penentuan-awal-bulan-hijriyah-pemerintah-indonesia) (ketinggian hilal ≥ 3°, elongasi ≥ 6,4°) itu namanya juga kriteria rukyah, ia harus dievaluasi **dari suatu titik di permukaan bumi**. Dan Indonesia itu luas. Jadi harusnya gak cuma milih satu titik; API ngecek **25 titik pengamatan pesisir** dari Sabang sampai Rote, dan kriteria dianggap terpenuhi kalau lolos **di satu titik manapun**, sama seperti logika rukyah Kemenag: hilal terlihat di wilayah Indonesia, bulan baru dimulai. (Lihat juga [Jurnal Astroislamica](https://journal.uinsuna.ac.id/index.php/ASTROISLAMICA/article/view/2735) tentang perspektif Maqāṣid al-Syarī'ah terhadap kriteria ini.)

Pola menariknya: untuk bulan-bulan yang "aman", hampir selalu titik paling barat yang memutuskan. Semakin barat, matahari terbenam semakin mundur, jadi hilalnya semakin tinggi di atas horizon saat senja. Sabang dan pesisir barat Aceh jadi *last chance* sekaligus *first win*. Tapi ada bulan-bulan dengan deklinasi bulan selatan di mana arc selatan (selatan Jawa sampai Nusa Tenggara) yang menang. Data historis 1970–2050 menunjukkan titik-titik Jawa (Ujung Kulon, Pangandaran) ikut memutuskan beberapa bulan. Makanya titik-titik selatan itu ada di daftar, bukan pajangan.

Bila kriteria terpenuhi, API melaporkan titik yang memutuskan lewat field `deciding_site` di `/hilal/info`, dan grafiknya menampilkan baris **TITIK PENGAMAT**.

## Alur Kerjanya

Simplifikasi dari implementasi aslinya kira-kira begini:

```
FUNCTION hilal_viz(month, year):
  sighting = resolve_sighting_evening(year, month)
  ms = sighting_on_date(sighting.evening_date)     # 25 titik, satu panggilan
  chosen = ms.deciding_site or ms.best_site        # titik penentu (atau terdekat)
  alt_ok = chosen.alt_refracted >= 3.0°
  elong_ok = chosen.elongation >= 6.4°
  data = build_chart_data(..., decider=chosen)
  img = render_chart(data)
  return PNG
```

### 1. Resolve malam pengamatan

Kalau kamu minta visibilitas untuk bulan Ramadhan, endpoint ini nggak menghitung tanggal 1 Ramadhan itu sendiri, tapi mundur ke **malam ke-29 Sya'ban**, karena itu malam yang sebenarnya diamati untuk menentukan apakah besok sudah masuk Ramadhan atau belum. Ini logika dasar rukyah: kamu mengamati hilal di ujung bulan berjalan, bukan di awal bulan target.

### 2. Hitung astronomi malam itu, di titik penentu

Dua kategori data dihitung:

- **Kriteria** — `moon_alt` (ketinggian bulan *[toposentris](https://en.wikipedia.org/wiki/Horizontal_coordinate_system)*, terkoreksi refraksi), `moon_az` (azimut), `sun_alt`, dan `elongation` (jarak sudut bulan-matahari, *[geosentris](https://en.wikipedia.org/wiki/Barycentric_coordinates_(astronomy))* sesuai konvensi hisab Indonesia). Ini angka-angka yang langsung dibandingkan ke ambang batas MABIMS — semuanya milik **satu titik yang sama**, jadi adegan langit, tabel kriteria, dan verdict nggak bisa saling kontradiksi.
- **Waktu pengamat (observer-clock)** — iluminasi, jam matahari terbenam, dan jam bulan terbenam, semuanya di titik penentu dan ditampilkan dalam zona waktu lokal titik itu (WIB atau WITA).

### 3. Cek ambang batas Neo MABIMS

```
alt_ok   = moon_alt_refracted >= 3.0°
elong_ok = elongation         >= 6.4°
```

Dua syarat ini harus terpenuhi bersamaan, minimal di satu titik. Kalau di titik manapun nggak ada yang lolos, hilal dianggap belum memenuhi kriteria visibilitas, meskipun bulan sudah di atas horizon di beberapa titik.

## Contoh Hasil

<img src="/viz.png" alt="Visualisasi hilal dari endpoint /hilal/viz" style="max-width: min(420px, 100%); display: block;" />

Screenshot di atas itu visibilitas untuk 1 Dzulqa'dah 1447 H (evaluasi malam 29 Syawal 1447 H, 18 Apr 2026, titik pengamatan Sabang):

- Altitude bulan +10.4° (lolos, syarat ≥3.0°)
- Elongasi 14.5° (lolos, syarat ≥6.4°)
- Iluminasi 1.4% — sabit masih ramping tapi udah jelas
- Matahari terbenam 18:46, bulan terbenam 19:31 — selisih 45 menit, jendela pengamatan nyaman

Status: **MEMENUHI KRITERIA**, dan kali ini marginnya jauh di atas ambang. Bandingin sama bulan-bulan borderline (misal 1446-08 yang lolos dengan margin 0,006°) — di grafiknya sabitnya nyaris nggak kelihatan, dan verdict-nya "MENDEKATI BATAS". Grafik ini nggak bohong.

## Kenapa Repot-repot Bikin Ini?

Karena angka mentah (`moon_alt: 10.4, elongation: 14.5`) nggak intuitif buat kebanyakan orang, termasuk saya sendiri. Tapi begitu divisualisasikan -> lihat posisi bulan relatif ke horizon, lihat pill hijau/merah, lihat tabel kriteria -> jadi jauh lebih gampang dicerna. Endpoint ini niatnya bukan cuma buat developer yang butuh JSON, tapi juga buat siapa saja yang penasaran "kok bisa sih hilal dibilang terlihat/tidak terlihat" tanpa harus paham astronomi.

Coba sendiri di [playground](/playground/hilal):

```
GET https://api.mabims.dev/api/v1/hilal/viz?month=1&year=1448
```

Ganti `month` dan `year` sesuai bulan Hijriah yang mau dicek. Dokumentasi lengkap parameter ada di [mabims.dev/endpoints/hilal](https://mabims.dev/endpoints/hilal).

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Di Mana Cari Hilal?",
  "description": "Bedah teknis endpoint /hilal/viz. Kriteria Neo MABIMS di titik-titik pengamatan pesisir, titik penentu, sampai cara chart PNG-nya dirender dari nol.",
  "datePublished": "2026-08-29",
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
    "@id": "https://mabims.dev/blog/behind-hilal-viz"
  }
}
</script>
