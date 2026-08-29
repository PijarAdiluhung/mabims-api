---
title: FAQ
description: Pertanyaan yang sering ditanyakan tentang API Kalender MABIMS.
---

## Umum

<details>
<summary>Apa itu MABIMS?</summary>

MABIMS singkatan dari Menteri-menteri Agama Brunei, Indonesia, Malaysia, Singapura. Istilah ini lebih sering dipakai dalam konteks kriteria rukyah yang digunakan Kemenag RI untuk menentukan awal bulan Hijriah, khususnya awal Ramadhan, Syawal, dan Dzulhijjah. Kriteria Neo MABIMS mensyaratkan hilal terlihat minimal 3° dan elongasi minimal 6,4° saat matahari terbenam.

</details>

<details>
<summary>Kenapa tanggal Hijriah di aplikasi saya beda dengan yang diumumkan pemerintah Indonesia?</summary>

Kebanyakan API dan aplikasi kalender Hijriah memakai kriteria Umm al-Qura (Arab Saudi) sebagai default. Karena metode rukyah dan lokasi pengamatannya berbeda, hasilnya bisa selisih ±1 hari dari keputusan resmi Kemenag, terutama untuk awal puasa, Idulfitri, dan Idul Adha.

</details>

<details>
<summary>MABIMS vs Umm al-Qura, mana yang lebih akurat untuk Indonesia?</summary>

Untuk keperluan di Indonesia, MABIMS lebih akurat karena berdasarkan imkan rukyah, sehingga dapat diverifikasi Kemenag RI melalui sidang isbat. Umm al-Qura dirancang untuk kebutuhan Arab Saudi dan tidak merepresentasikan hasil rukyah Indonesia.

</details>

<details>
<summary>Apakah API ini produk resmi Kemenag atau MABIMS?</summary>

Bukan. API ini independen, dibangun menggunakan data tabel publik Kemenag RI sebagai sumber. Untuk kepastian hukum syar'i, tetap rujuk pengumuman resmi Kemenag.

</details>

## Akses & Autentikasi

<details>
<summary>Apakah API ini gratis dan butuh API key?</summary>

Ya, gratis dan tanpa autentikasi. Cukup panggil endpoint langsung, tanpa registrasi atau API key.

</details>

<details>
<summary>Apakah bisa dipakai langsung dari frontend (client-side)?</summary>

Bisa. CORS bersifat terbuka, jadi bisa dipanggil langsung dari browser di domain manapun. Untuk detail rate limit dan kebijakan penggunaan wajar, lihat halaman [Access & Rate Limits](/access).

</details>

## Teknis

<details>
<summary>Apa bedanya <code>source: "mabims"</code> dan <code>source: "mabims-computed"</code>?</summary>

- **`mabims`** — tanggal diambil langsung dari kalender publik Kemenag.
- **`mabims-computed`** — dihitung otomatis dengan kriteria Neo MABIMS karena tanggal berada di luar cakupan tabel publik.

</details>

<details>
<summary>Data-nya sampai tahun berapa?</summary>

Cek info data terbaru di halaman [Data Coverage](/data-coverage). Di luar rentang itu, API menghitung otomatis (fallback) memakai kriteria Neo MABIMS. Responsnya akan menandai `source: "mabims-computed"` dan bukan `"mabims"`.

</details>

<details>
<summary>Zona waktu apa yang dipakai secara default?</summary>

Default-nya **Asia/Jakarta (UTC+7)**, khusus untuk endpoint `/today`. Bisa di-override dengan parameter `tz` memakai zona IANA (mis. `Asia/Kuala_Lumpur`) atau UTC offset (mis. `UTC+8`). Endpoint `/convert` tidak bergantung timezone karena sifatnya konversi tanggal, bukan "hari ini".

</details>

<details>
<summary>Bagaimana cara konversi tanggal Masehi ke Hijriah atau sebaliknya?</summary>

Pakai endpoint `GET /convert?date=YYYY-MM-DD&calendar=gregorian` atau `calendar=hijri` sesuai arah konversi yang diinginkan. Lihat dokumentasi lengkap: [Referensi API /convert](/endpoints/convert).

</details>

<details>
<summary>Bagaimana cara mengecek visibilitas hilal untuk bulan tertentu?</summary>

Gunakan endpoint `/hilal/info` untuk data kriteria, atau `/hilal/viz` untuk grafik visibilitas hilal (720×1280 PNG) yang menampilkan posisi bulan, arah sabit, dan verdict TERLIHAT/TIDAK TERLIHAT — dihitung di titik Sabang.

</details>

## Lainnya

<details>
<summary>Apakah API ini open source?</summary>

Ya, kode sumbernya terbuka di GitHub: [PijarAdiluhung/mabims-api](https://github.com/PijarAdiluhung/mabims-api). Kontribusi dan laporan isu selalu diterima.

</details>

<details>
<summary>Siapa yang membuat mabims.dev?</summary>

mabims.dev dibuat oleh Pijar Sukma Adiluhung, developer asal Indonesia yang juga penghobi astronomi amatir (nggak heran kalau endpoint /hilal/viz digarap detail). Proyek ini lahir dari pengalaman pribadi melihat banyak aplikasi kalender Hijriah di Indonesia pakai kriteria Umm al-Qura yang kurang pas untuk konteks lokal. Kamu bisa lihat proyek lain buatannya di [kajian.malangmengaji.com](https://kajian.malangmengaji.com), atau cek kode sumber mabims.dev di [GitHub](https://github.com/PijarAdiluhung/mabims-api). Bisa juga baca tulisannya di [/blog](/blog).

</details>
