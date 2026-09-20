---
title: "Kenapa Tanggal Hijriah Berganti Saat Maghrib (dan Cara Menanganinya)"
description: "Jam 18:30 tanggal Masehi masih hari yang sama, tapi tanggal Hijriah sudah lompat ke besok. Ini penjelasan kenapa hari Hijriah dimulai saat maghrib, dan cara memakai parameter next=true di GET /today supaya aplikasimu nggak salah tampil."
date: 2026-09-19
tags:
  - Tutorial
  - Hijriah
  - MABIMS
  - JavaScript
  - maghrib
excerpt: "Jam 18:30 tanggal Masehi masih hari yang sama, tapi tanggal Hijriah sudah lompat ke besok. Ini penjelasan kenapa hari Hijriah dimulai saat maghrib, dan cara memakai parameter next=true di GET /today supaya aplikasimu nggak salah tampil."
cover:
  image: ../../../assets/maghrib.jpg
  alt: Langit senja saat maghrib
authors:
  - pijar
---

Ini bagian yang sering luput dari developer yang bikin fitur tanggal Hijriah. Kita terbiasa dengan pola "ganti hari jam 00:00", jadi refleks kita ya ambil tanggal hari ini, tampilkan, selesai. Padahal buat kalender Hijriah, itu setengah benar.

Di tulisan ini kita bahas dua hal: kenapa hari Hijriah dimulai saat maghrib, dan bagaimana parameter `next=true` di [GET /today](https://mabims.dev/endpoints/today) bisa bantu kamu menanganinya tanpa ribet.

## Kenapa hari Hijriah dimulai saat maghrib?

Kalender Masehi itu harinya dihitung dari satu tengah malam ke tengah malam berikutnya, murni konvensi. Semacam kesepakatan bersama negara-negara dunia gitu.

Kalender Hijriah beda. Dia kalender bulan, dan awal bulannya ditentukan lewat **pengamatan hilal**, bulan sabit tipis pertama yang muncul setelah bulan baru. Hilal itu hanya bisa dilihat (atau dihitung kriterianya) **saat matahari terbenam**, di ufuk barat, sebentar setelah maghrib.

Jadi logikanya begini:

```text
matahari terbenam (maghrib)
        ↓
hilal diamati / kriterianya diperiksa
        ↓
kalau memenuhi, bulan baru dimulai
        ↓
hari pertama bulan baru dimulai SEKARANG, bukan nunggu tengah malam
```

Karena penentuan bulan baru terjadi di maghrib, wajar kalau batas pergantian hari-nya juga ikut di maghrib. Hari Hijriah berjalan dari maghrib ke maghrib.

Kalau kamu pernah baca [deep dive mabims-computed](/blog/deep-dive-mabims-computed), ini nyambung. Kriteria Neo MABIMS (ketinggian hilal minimal 3° dan elongasi minimal 6,4°) diperiksa **saat matahari terbenam**. Titik waktu yang sama itulah yang jadi patokan pergantian hari.

## Contoh yang paling gampang: malam pertama Ramadan

Ini contoh yang semua orang Indonesia pernah alami.

Misalnya 1 Ramadan jatuh pada hari Rabu menurut penanggalan Masehi. Kapan tarawih pertama? **Selasa malam.**

Kok bisa? Karena Selasa sore setelah maghrib, tanggal Hijriah sudah masuk 1 Ramadan. Malamnya sudah malam Ramadan, jadi tarawih dan sahur-nya ikut. Baru besoknya, hari Rabu, kita puasa hari pertama (ini juga alasan kenapa Sabtu malam disebut malam Minggu).

Jadi di Selasa jam 19:00, kalender Masehi bilang "Selasa", tapi kalender Hijriah sudah bilang "1 Ramadan". Dua-duanya benar, cuma batas harinya beda.

Hal yang sama berlaku untuk malam Jumat, malam 1 Muharram, malam Idul Fitri (malam takbiran), dan seterusnya. Semua "malam" itu sebenarnya sudah bagian dari hari berikutnya.

## Masalahnya buat developer

Sekarang bayangkan kamu bikin widget tanggal Hijriah di website masjid. Kamu panggil `/today` seperti biasa:

```bash
curl "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta"
```

Responsnya:

```json
{
  "input": { "date": "2026-08-24", "calendar": "gregorian", "tz": "Asia/Jakarta" },
  "output": { "date": "1448-03-11", "calendar": "hijri", "day": 11, "month": 3, "month_name": "Rabiul Akhir", "year": 1448, "weekday": "Senin" },
  "source": "mabims",
  "warnings": []
}
```

Ini benar untuk siang hari. Tapi jam 18:30 WIB, jamaah yang buka website itu secara syar'i sudah masuk tanggal 12 Rabiul Akhir, sementara widget kamu masih nampilin 11. Baru jam 00:00 nanti widget-nya "menyusul".

Selisih ±5 sampai 6 jam itu kelihatannya kecil, tapi buat website masjid, pesantren, atau aplikasi pengingat puasa (puasa Ayyamul Bidh, Senin Kamis, Asyura, dan sebagainya), tanggalnya bisa bikin bingung. Apalagi kalau malam itu memang malam yang penting.

## Solusinya: `next=true`

Makanya `/today` punya parameter `next`. Cara pakainya:

```bash
curl "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta&next=true"
```

Responsnya sekarang punya satu objek tambahan bernama `next`:

```json
{
  "input": { "date": "2026-08-24", "calendar": "gregorian", "tz": "Asia/Jakarta" },
  "output": { "date": "1448-03-11", "calendar": "hijri", "day": 11, "month": 3, "month_name": "Rabiul Akhir", "year": 1448, "weekday": "Senin" },
  "next": { "date": "1448-03-12", "calendar": "hijri", "day": 12, "month": 3, "month_name": "Rabiul Akhir", "year": 1448, "source": "mabims" },
  "source": "mabims",
  "warnings": []
}
```

Artinya:

- `output` = tanggal Hijriah **sekarang** (sebelum maghrib).
- `next` = tanggal Hijriah yang berlaku **setelah maghrib malam ini**.

Jadi satu kali request, kamu dapat dua-duanya. Tinggal pilih mana yang ditampilkan tergantung sekarang sudah lewat maghrib atau belum.

Tanpa `next=true`, field `next` nggak muncul sama sekali dan respons-nya sama persis seperti sebelumnya. Jadi kode lama kamu aman, nggak ada yang rusak.

## Satu hal penting: API nggak menghitung waktu maghrib

Ini bagian yang perlu kamu baca baik-baik.

**API ini nggak tahu jam berapa maghrib di tempatmu.** Dia cuma ngasih dua kandidat tanggal, `output` dan `next`. Kapan harus pindah dari yang pertama ke yang kedua, itu urusan sisi klien.

Ini masuk akal kalau dipikir-pikir: waktu maghrib bergantung pada lokasi yang spesifik (kota, bahkan koordinat), dan berubah tiap hari. maghrib di Jakarta, Malang, Makassar, dan Jayapura beda-beda. Jadi API tetap fokus di hal yang dia kuasai, yaitu tanggal Hijriah, dan waktu maghrib kamu ambil dari sumber jadwal sholat yang sesuai lokasi pengguna kamu.

Sumbernya bebas: library jadwal sholat, API jadwal sholat, atau data jadwal yang sudah kamu punya di aplikasi (kalau aplikasimu memang sudah menampilkan waktu sholat, tinggal pakai waktu maghrib yang sama).

## Contoh implementasi JavaScript

```js
async function ambilTanggalHijriah(waktumaghrib) {
  const res = await fetch(
    "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta&next=true"
  );
  const data = await res.json();

  // waktumaghrib adalah objek Date untuk maghrib hari ini di lokasi user
  const sudahmaghrib = new Date() >= waktumaghrib;

  return sudahmaghrib ? data.next : data.output;
}
```

Lalu tinggal ditampilkan seperti biasa:

```js
const waktumaghrib = ambilWaktumaghribHariIni(); // dari sumber jadwal sholat kamu
const tanggal = await ambilTanggalHijriah(waktumaghrib);

const { day, month_name, year } = tanggal;
document.querySelector("#hijri-date").textContent =
  `${day} ${month_name} ${year} H`;
```

Sebelum maghrib tampil `11 Rabiul Akhir 1448 H`, setelah maghrib otomatis jadi `12 Rabiul Akhir 1448 H`.

Sisi bagusnya, kamu nggak perlu request ulang saat maghrib tiba. Data `output` dan `next` sudah ada dari awal, jadi cukup satu kali fetch, lalu bandingkan dengan jam saat ini (misalnya pakai `setInterval` atau cek tiap kali komponen dirender).

## Bagaimana kalau lewat tengah malam?

Setelah jam 00:00, kalender Masehi ganti hari, dan `/today` otomatis mengembalikan `output` yang sudah berisi tanggal Hijriah baru. Nilainya sama dengan `next` yang kemarin kamu ambil malam sebelumnya.

Jadi `next=true` itu relevan di jendela waktu **maghrib sampai tengah malam**. Di luar jendela itu, `output` saja sudah cukup. Nggak masalah kalau kamu tetap selalu kirim `next=true`, hasilnya tetap konsisten.

## Timezone dan maghrib itu satu paket

Kalau kamu baca [tutorial integrasi](/blog/cara-pakai-mabims-api), saya sudah bahas soal parameter `tz`. Di sini timezone jadi makin penting.

`next=true` selalu dihitung relatif terhadap "hari ini" di timezone yang kamu kirim. Jadi kalau user kamu di Makassar, kirim `tz=Asia/Makassar`. Kalau di Jayapura, kirim `tz=Asia/Jayapura`. Kalau tidak diisi, bawaannya `Asia/Jakarta`.

Kolom `input.tz` di respons akan menampilkan zona waktu yang dipakai, jadi kamu bisa memastikan API menghitung di zona yang benar.

## Jangan lupa cek `next.source`

Objek `next` punya field `source` sendiri, terpisah dari `source` utama. Kenapa?

Karena tanggal besok bisa saja berada di luar tabel resmi Kemenag walaupun tanggal hari ini masih di dalam tabel. Misalnya hari ini adalah hari terakhir yang tercakup tabel. Maka `source` utama `mabims`, tapi `next.source` bisa jadi `mabims-computed`.

```js
if (data.next?.source === "mabims-computed") {
  console.warn("Tanggal setelah maghrib dihitung dengan kriteria Neo MABIMS, bukan tabel resmi.");
}
```

Ini sejalan dengan prinsip yang sama di API ini: saya nggak mau hasil perhitungan diam-diam tampil seolah-olah data resmi. Kalau kamu mau tahu lebih lanjut soal bedanya, ada di [deep dive mabims-computed](/blog/deep-dive-mabims-computed).

## Soal cache

`/today` di-cache di edge sampai tengah malam lokal. Ini aman untuk `next=true` karena `output` dan `next` sama-sama berlaku sepanjang hari itu. Pergantian dari `output` ke `next` terjadi di sisi klien, bukan di server, jadi cache nggak akan bikin tanggal "nyangkut".

Tapi ada satu jebakan kalau kamu bikin cache sendiri di sisi server (misalnya di WordPress atau PHP seperti di [tutorial sebelumnya](/blog/cara-tampilkan-tanggal-hijriah)):

> **Jangan simpan hasil akhir yang sudah dipilih.** Simpan respons mentahnya (`output` dan `next`), lalu tentukan mana yang tampil setiap kali halaman dirender.

Kalau kamu cache string `"11 Rabiul Akhir 1448 H"` selama 1 jam, widget kamu bisa tetap nampilin tanggal lama sampai 1 jam setelah maghrib lewat. Kalau yang kamu cache respons JSON-nya, dan pilihan `output` vs `next` dilakukan saat render, tanggalnya tetap tepat waktu.

## Error yang mungkin muncul

Parameter `next` menerima `true`/`false` (tidak peka huruf besar/kecil) dan `1`/`0`. Kalau kamu kirim nilai lain, misalnya `next=yes`, API akan menjawab:

```json
{
  "error": {
    "code": "invalid_next",
    "message": "..."
  }
}
```

dengan HTTP status `400`. Jadi kalau tiba-tiba widget kamu kosong setelah menambah parameter ini, cek dulu nilainya.

## Ringkasan

1. Hari Hijriah dimulai saat **maghrib**, bukan tengah malam, karena bulan baru ditentukan lewat hilal yang diperiksa saat matahari terbenam.
2. Akibatnya, dari maghrib sampai tengah malam, tanggal Hijriah sudah "besok" padahal tanggal Masehi masih hari yang sama.
3. Pakai `?next=true` di `GET /today` untuk mendapatkan objek `next`, yaitu tanggal Hijriah yang berlaku setelah maghrib malam ini.
4. **API tidak menghitung waktu maghrib.** Kamu yang menentukan kapan berpindah dari `output` ke `next`, pakai waktu maghrib sesuai lokasi pengguna.
5. Kirim `tz` yang sesuai, cek `next.source`, dan kalau kamu bikin cache sendiri, simpan respons mentah, bukan hasil akhirnya.

Coba sekarang:

```bash
curl "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta&next=true"
```

Dokumentasi lengkap endpoint ini ada di [mabims.dev/endpoints/today](https://mabims.dev/endpoints/today). Pengguna non-developer bisa langsung melihat efek pergantian saat maghrib lewat [kalender Hijriah MABIMS](/kalender-hijriah/). Kalau ada kasus yang belum tertangani atau kamu nemu tanggal yang terasa janggal, silakan buka issue di [GitHub](https://github.com/PijarAdiluhung/mabims-api).

Semoga widget tanggal Hijriah kamu nggak pernah lagi telat sehari :)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Kenapa Tanggal Hijriah Berganti Saat maghrib (dan Cara Menanganinya Pakai next=true)",
  "description": "Jam 18:30 tanggal Masehi masih hari yang sama, tapi tanggal Hijriah sudah lompat ke besok. Ini bukan bug. Ini penjelasan kenapa hari Hijriah dimulai saat maghrib, dan cara memakai parameter next=true di GET /today supaya aplikasimu nggak salah tampil.",
  "datePublished": "2026-09-19",
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
    "@id": "https://mabims.dev/blog/kenapa-tanggal-hijriah-berganti-saat-maghrib"
  }
}
</script>