---
title: "Siapa yang Pakai MABIMS API? Kenalan Yuk"
description: "MABIMS API dipakai sekitar 3.000 perangkat tiap hari dan hampir semuanya tidak saya kenal. Kalau kamu salah satunya, mampir sebentar ya."
date: 2026-11-28
tags:
  - Cerita
  - MABIMS
  - Komunitas
  - Open Source
excerpt: "Kemarin API ini menerima sekitar 10.000 permintaan dari sekitar 3.300 perangkat. Tidak ada satu pun yang saya tahu namanya. Bukan karena malas mencari, tapi karena MABIMS API memang sengaja dibuat tanpa kunci dan tanpa pendaftaran. Jadi saya baca log CDN-nya, dan hasilnya cukup lucu."
cover:
  image: ../../../assets/thank-you.jpg
  alt: Ilustrasi ucapan terima kasih untuk pengguna MABIMS API
authors:
  - pijar
---

Kemarin API ini menerima sekitar 10.000 permintaan dari sekitar 3.300 perangkat. Tidak ada satu pun yang saya tahu namanya.

MABIMS API memang sengaja dibuat tanpa kunci, tanpa pendaftaran, tanpa akun. Siapa pun bisa langsung memanggil endpoint-nya. Enak buat yang mau coba, tapi efek sampingnya saya juga tidak pernah tahu siapa yang pakai.

Karena penasaran, saya menghabiskan weekend saya untuk membaca log CDN-nya. Hasilnya lucu.

## Yang kelihatan dari log

Sekitar 87% trafik datang dari satu aplikasi Android yang tidak saya kenal.

Biasanya aplikasi Android mengirim identitasnya di User-Agent. Yang saya terima hanya ini:

```text
Dalvik/2.1.0 (Linux; U; Android 16; SM-A065F Build/BP2A.250605.031.A3)
```

Itu User-Agent bawaan Android, bukan nama aplikasi. Jadi ada sekitar 3.000 HP yang memakai API ini tiap hari dan saya tidak tahu aplikasi apa yang sedang saya lihat ini.

Selain itu ada aplikasi Flutter yang rajin membuka `/month` dan `/year`. Ada juga satu layar yang sepertinya TV di suatu tempat, minta `/today` tiap jam dan hampir selalu dapat `304`. Ada beberapa situs yang kelihatan jelas dari header Referer. Sisanya crawler dan bot pemantau uptime.

Yang paling ramai justru jam subuh. Antara pukul 04.00 dan 06.00 WIB trafik naik tajam, lalu turun lagi menjelang tengah malam. Untuk aplikasi kalender Hijriah, pola seperti itu masuk akal sekali.

## Kenapa saya ingin tahu siapa

Ada tiga alasan, dan tidak satupun soal menagih imbalan.

**Pertama, saya ingin bilang terima kasih.** Zaman ini, membuat API semakin mudah, tapi membuat API yang benar-benar bermanfaat? Itu masih tetap sulit. Kalau ada orang yang benar-benar memakainya untuk produk nyata, saya ingin tahu dan ingin mengucapkan terima kasih langsung.

**Kedua, saya ingin bisa memberi kabar sebelum ada perubahan.** Kalau nanti bentuk respons berubah, atau ada pembatasan baru, atau ada data yang perlu dikoreksi, saya tidak punya cara menghubungi kamu. Yang saya punya cuma log, dan itu hilang setelah tiga hari.

**Ketiga, kadang ada masalah yang bukan di sisi saya tapi saya tidak bisa memberi tahu.** Minggu ini ada satu klien yang mengirim `?date=` ke `/events`. Endpoint itu menerima `year`, jadi permintaannya ditolak terus, sekitar 150 kali sehari. Mungkin itu situs kamu, dan mungkin kamu belum sadar.

## Kalau mau, ini cara kenalan

Buka issue di [GitHub mabims-api](https://github.com/PijarAdiluhung/mabims-api/issues) dan sebutkan nama project serta link-nya (Sekalian leave a star ya, hehe).

Tidak perlu menjelaskan kode kamu. Nama project dan satu link sudah cukup. Kalau nanti sudah terkumpul beberapa, saya buatkan halaman "Dipakai oleh" supaya orang lain juga bisa lihat contoh pemakaiannya, sekaligus jadi bahan belajar buat yang baru mulai.

## Kalau tetap mau anonim

Tidak apa-apa. Betul-betul tidak apa-apa.

API ini tetap gratis, tetap tanpa kunci, dan tetap tidak akan minta identitas. Saya cuma penasaran, bukan menagih. Kalau kamu lebih nyaman diam, silakan pakai terus seperti biasa. Tidak ada yang berubah.

Tapi kalau kamu sempat mampir, satu komentar saja sudah cukup bikin saya senang.

Terima kasih sudah memakai MABIMS API. Barakallahu fiikum.

Pijar, out.
