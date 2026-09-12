---
title: "Bedah mabims-computed: Apa yang Terjadi di Balik Layar?"
description: "Bedah teknis fallback kalender MABIMS: dari posisi hilal, keputusan 29 atau 30 hari, seed table, sampai alasan ketinggian hilal dihitung secara toposentris sementara elongasinya tetap geosentris."
date: 2026-09-09
tags:
  - MABIMS
  - Astronomi
  - Backend
  - Python
  - Deep Dive
excerpt: "Kalau tanggal yang kamu minta berada di luar tabel Kemenag, MABIMS API tidak menebak secara acak. API menghitung ulang panjang bulan berdasarkan kriteria Neo MABIMS. Tulisan ini membedah mesin di balik source mabims-computed."
cover:
  image: ../../../assets/kalkulator.jpg
  alt: Perhitungan hilal dan kalender MABIMS
authors:
  - pijar
---

Di beberapa bagian dokumentasi MABIMS API, saya menyebut `source: "mabims-computed"` sebagai fallback.

Di tulisan ini kita akan melihat cara kerjanya lebih dekat. `mabims-computed` bukan sekadar "kalau datanya tidak ada, pakai perkiraan". Di baliknya ada mesin kecil yang menghitung awal bulan Hijriah, berjalan maju atau mundur dari sebuah tanggal acuan, menyimpan hasil perhitungan, lalu memberi tahu aplikasi bahwa data yang diterima bukan data resmi Kemenag.

Saya akan membahas bagian-bagian yang biasanya tidak terlihat dari luar: bagaimana mesin menentukan sebuah bulan memiliki 29 atau 30 hari, mengapa ketinggian hilal dihitung secara [toposentris](https://en.wikipedia.org/wiki/Horizontal_coordinate_system) sementara elongasi tetap [geosentris](https://en.wikipedia.org/wiki/Barycentric_coordinates_(astronomy)), dan mengapa kriteria tersebut diperiksa di 25 titik pengamatan pesisir.

## Dua jenis data, satu API

MABIMS API memiliki dua sumber data utama:

- `mabims` — tanggal dari kalender publik Kemenag RI.
- `mabims-computed` — tanggal yang dihitung menggunakan kriteria Neo MABIMS ketika tanggal tersebut berada di luar cakupan tabel.

Contoh tanggal yang masih tersedia di dalam tabel:

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

Kalau tanggal yang diminta sudah berada di luar tabel, bentuk responsnya tetap sama. Yang berubah adalah sumber datanya:

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

Kedua sumber ini sengaja dibedakan. Hasil perhitungan tetap berguna untuk kalender aplikasi, tetapi tidak boleh dianggap sebagai pengumuman resmi atau pengganti sidang isbat.

## Neo MABIMS dalam dua angka

Versi singkat kriteria [Neo MABIMS](https://mui.or.id/baca/berita/mengenal-kriteria-hilal-mabims-standard-penentuan-awal-bulan-hijriyah-pemerintah-indonesia) adalah:

```text
ketinggian hilal >= 3.0°
elongasi         >= 6.4°
```

Kedua syarat tersebut harus terpenuhi secara bersamaan, dan cukup terpenuhi di **satu titik pengamatan saja**. Kalo cuma ketinggian hilal yang memenuhi syarat, tetapi elongasinya belum cukup = kriterianya belum terpenuhi. Begitu juga sebaliknya. (Lihat juga liputan [ANTARA](https://www.antaranews.com/berita/5484670/perkembangan-kriteria-mabims-dalam-penentuan-awal-bulan-hijriah) dan [Jurnal Al-Marshad](https://jurnal.umsu.ac.id/index.php/almarshad/article/download/17139/11526) tentang kriteria ini.)

Kriteria ini diperiksa saat **matahari terbenam di masing-masing titik pengamatan**. Saat ini ada **25 titik pengamatan pesisir** dari Sabang sampai Rote; daftar lengkapnya tersedia di [`api/data/hilal_sites.json`](https://github.com/PijarAdiluhung/mabims-api/blob/main/api/data/hilal_sites.json). Polanya menarik: pada bulan-bulan yang kondisinya cukup aman, titik paling barat hampir selalu menjadi penentu. Semakin ke barat, matahari terbenam semakin lambat, sehingga hilal berada lebih tinggi di atas horizon saat senja. Namun, pada bulan-bulan ketika deklinasi Bulan berada di selatan, jalur titik-titik di selatan, dari Jawa bagian selatan sampai Nusa Tenggara, bisa menjadi penentu. Itu sebabnya titik-titik selatan juga perlu diperiksa.

Ini bukan berarti Sabang selalu menjadi patokan. Logikanya sama dengan rukyah Kemenag: selama hilal terlihat di wilayah Indonesia, bulan baru dimulai. API bahkan melaporkan titik yang menjadi penentu melalui field `deciding_site`.

## Dari hilal ke panjang bulan

Perhitungan panjang bulan sebenarnya bisa diringkas dalam fungsi kecil:

```python
def month_length(month_start):
    result = criteria_on_day29(month_start)
    return 29 if result.visible else 30
```

`criteria_on_day29()` memeriksa kondisi saat matahari terbenam pada malam ke-29 bulan yang sedang berjalan. Kalau kedua kriteria terpenuhi, bulan tersebut selesai setelah 29 hari. Kalau tidak, bulan digenapkan menjadi 30 hari.

Artinya, untuk menentukan awal Ramadan, yang diperiksa bukan malam pertama Ramadan. Yang diperiksa adalah malam ke-29 Sya'ban. Kalau hilal memenuhi kriteria, hari berikutnya adalah 1 Ramadan. Kalau tidak, Sya'ban berlangsung selama 30 hari.

Alurnya kira-kira seperti ini:

```text
awal bulan Hijriah yang sudah diketahui
                 ↓
periksa matahari terbenam pada malam ke-29
                 ↓
ketinggian >= 3° dan elongasi >= 6.4°?
             ↙                         ↘
           ya                          tidak
       bulan 29 hari                bulan 30 hari
             ↓                          ↓
   awal bulan berikutnya = awal + panjang bulan
```

Karena setiap bulan dimulai setelah bulan sebelumnya berakhir, mesin ini dapat menyusun kalender secara berantai.

## Bukan konversi aritmetika biasa

[Kalender Hijriah tabular](https://en.wikipedia.org/wiki/Tabular_Islamic_calendar) biasanya dapat dihitung dengan pola aritmetika: setiap bulan memiliki susunan 29 dan 30 hari tertentu, lalu siklus tahun kabisat menentukan penempatannya.

`mabims-computed` tidak bekerja seperti itu. Panjang bulan ditentukan satu per satu berdasarkan kondisi astronomis pada malam ke-29. Jadi, cara kerjanya lebih mirip linked list daripada rumus satu baris:

```text
1449-01-01
   └─ periksa hilal → 29 atau 30 hari
       └─ 1449-02-01
           └─ periksa hilal → 29 atau 30 hari
               └─ 1449-03-01
```

Konsekuensinya, mesin ini membutuhkan satu titik awal yang tepercaya. Di aplikasi, titik tersebut berasal dari batas tabel resmi Kemenag RI. Untuk tanggal setelah batas tabel, mesin berjalan maju dari tanggal acuan itu.

## Bisa berjalan mundur juga

Untuk tanggal sebelum kalender resmi, API tidak langsung mengizinkan perhitungan. Request harus menyertakan `retro=true`.

Alasannya sederhana: kriteria Neo MABIMS baru diperkenalkan pada 2022. Kalau kriteria tersebut diterapkan ke tahun 1990, hasilnya bukan data historis resmi. Hasil itu adalah rekonstruksi menggunakan aturan yang berlaku sekarang.

Karena itu, ada sumber data ketiga:

```text
source: "mabims-retro"
```

Label ini berarti tanggal tersebut dihitung mundur menggunakan kriteria yang sama, bukan diambil dari tabel resmi masa lalu. API juga memberikan warning agar perbedaan status ini tidak hilang ketika respons diteruskan ke aplikasi.

Secara internal, berjalan mundur sedikit lebih rumit daripada berjalan maju. Kalau kita mengetahui tanggal 1 bulan berikutnya, kita perlu memeriksa waktu matahari terbenam pada hari ke-31 sebelumnya untuk menentukan apakah bulan sebelumnya memiliki 29 atau 30 hari. Setelah itu, awal bulan sebelumnya bisa ditentukan.

## Bagian yang membuat saya harus menyelidiki ulang

Awalnya saya mengira pertanyaannya sederhana: untuk menghitung kriteria hilal, sebaiknya kita memakai koordinat pengamat di permukaan Bumi atau posisi yang dihitung dari pusat Bumi?

Istilahnya:

- **[Toposentris](https://en.wikipedia.org/wiki/Horizontal_coordinate_system)** — dilihat dari permukaan Bumi, dengan memperhitungkan posisi pengamat dan paralaks Bulan.
- **[Geosentris](https://en.wikipedia.org/wiki/Barycentric_coordinates_(astronomy))** — dilihat dari pusat Bumi.

Secara intuisi, pendekatan toposentris memang lebih masuk akal untuk pengamatan hilal karena manusia mengamati dari permukaan Bumi. Setelah saya validasi ulang dari awal sampai akhir, intuisi itu ternyata benar. Mesin ini menggunakan ketinggian hilal **secara toposentris** (dengan koreksi [refraksi atmosfer](https://en.wikipedia.org/wiki/Atmospheric_refraction)) di **25 titik pengamatan pesisir** dari Sabang sampai Rote. Elongasi tetap dihitung **secara geosentris**, sesuai konvensi hisab Indonesia. Kriteria cukup terpenuhi di satu titik mana pun.

## Kondisi borderline itu nyata

Kembali ke perhitungannya. Memenuhi kriteria bukan berarti posisinya jauh di atas ambang batas.

Misalnya hasilnya seperti ini:

```text
altitude  = 3.12°
elongation = 7.01°
```

Secara boolean, hasil tersebut memenuhi kriteria. Namun, jarak terdekatnya dari ambang batas ketinggian hanya 0,12°. Karena itu, provider menyimpan margin terkecil:

```python
margin = min(
    altitude - 3.0,
    elongation - 6.4,
)
```

Kalau margin tersebut positif tetapi kurang dari 0,25°, bulan ditandai sebagai borderline. Informasi ini dimasukkan ke `warnings[]` agar aplikasi tidak menganggap hasil yang sangat dekat dengan ambang batas sebagai sesuatu yang sepenuhnya pasti.

Catatan penting: borderline bukan berarti hasilnya otomatis salah. Artinya, perubahan kecil pada lokasi, metode, data [ephemeris](https://ssd.jpl.nasa.gov/planets/eph_export.html), atau cara menafsirkan kriteria dapat memengaruhi hasil.

## Kapan `mabims-computed` boleh digunakan?

Menurut saya, `mabims-computed` cocok digunakan untuk:

- kalender aplikasi yang membutuhkan cakupan tahun lebih panjang;
- pratinjau tanggal hari besar di masa depan;
- fitur konversi tanggal yang belum memiliki tabel resmi;
- riset, eksperimen, dan visualisasi hilal;
- fallback teknis ketika data resmi belum tersedia.

Jangan memperlakukannya sebagai:

- pengumuman resmi awal Ramadan atau Idul Fitri;
- pengganti [sidang isbat](https://en.wikipedia.org/wiki/Moon_sighting);
- bukti bahwa hilal benar-benar diamati di lokasi tertentu;
- satu-satunya sumber untuk mengambil keputusan administratif atau keagamaan.

Di sisi aplikasi, setidaknya selalu periksa dua field berikut:

```js
if (data.source === "mabims-computed") {
  console.warn("Tanggal ini adalah estimasi algoritmik, bukan data resmi.");
}

if (data.warnings?.length) {
  console.warn(data.warnings);
}
```

## Intinya

`mabims-computed` adalah sebuah kompromi yang dibuat secara sadar:

1. Tabel resmi digunakan selama datanya tersedia.
2. Di luar cakupan tabel, panjang bulan dihitung berdasarkan kriteria Neo MABIMS.
3. Kriteria diperiksa saat matahari terbenam di masing-masing dari 25 titik pengamatan pesisir; cukup satu titik yang memenuhi syarat.
4. Dua ambang, yaitu ketinggian 3° dan elongasi 6,4°, harus terpenuhi secara bersamaan.
5. Ketinggian hilal dihitung secara toposentris dengan koreksi refraksi, sedangkan elongasi tetap geosentris. Model ini tervalidasi 48 dari 48 kasus terhadap tabel kurasi.
6. Hasilnya diberi label dan warning agar tidak disalahartikan sebagai data resmi.

Kalau kamu hanya memanggil `/today`, semua kerumitan ini memang tidak perlu terlihat. Namun, saat kamu meminta kalender untuk tahun 2050 atau bertanya mengapa satu bulan memiliki 29 hari sementara bulan lainnya 30 hari, inilah proses yang berlangsung di balik layar.

Coba sendiri:

```bash
curl "https://api.mabims.dev/api/v1/events?year=2050&calendar=gregorian"
```

Perhatikan field `source` dan `warnings` pada responsnya. Dokumentasi endpoint dan status cakupan data tersedia di [mabims.dev/data-sources](https://mabims.dev/data-sources).

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Bedah mabims-computed: Apa yang Terjadi di Balik Layar?",
  "description": "Bedah teknis fallback kalender MABIMS: dari posisi hilal, keputusan 29 atau 30 hari, seed table, sampai alasan ketinggian hilal dihitung secara toposentris sementara elongasinya tetap geosentris.",
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
