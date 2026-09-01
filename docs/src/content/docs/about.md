---
title: Tentang MABIMS.dev
description: API open-source gratis untuk kalender Hijriah Indonesia berdasarkan data resmi MABIMS Kementerian Agama RI.
---

## Apa itu MABIMS.dev?

MABIMS.dev adalah API open-source unofficial gratis yang menyediakan ekosistem kalender Hijriah untuk Indonesia. API ini menggunakan data resmi MABIMS yang diterbitkan oleh Kementerian Agama Republik Indonesia, bukan Umm al-Qura (standar Arab Saudi).

## Untuk Siapa?

- **Developer** yang membangun aplikasi web atau mobile dengan fitur kalender Hijriah
- **Aplikasi masjid dan pesantren** yang perlu menampilkan tanggal puasa, Idul Fitri, dan Idul Adha sesuai pengumuman Kemenag
- **Sekolah dan universitas Islam** yang mengintegrasikan kalender Hijriah ke sistem akademik
- **Siapapun** yang butuh tanggal Hijri Indonesia yang akurat

## Mengapa MABIMS, Bukan Umm al-Qura?

Hampir semua API dan library kalender Hijriah menggunakan Umm al-Qura sebagai default. Umm al-Qura adalah kalender resmi Arab Saudi yang dirancang untuk kebutuhan di sana, bukan untuk Indonesia.

Karena metode rukyah dan lokasi pengamatannya berbeda, hasilnya bisa selisih ±1 hari dari keputusan resmi Kemenag — terutama untuk awal Ramadhan, Idul Fitri, dan Idul Adha. MABIMS.dev menggunakan data tabel publik Kemenag RI dan kriteria Neo MABIMS (ketinggian hilal ≥ 3°, elongasi ≥ 6,4° di Sabang saat matahari terbenam) untuk tanggal di luar cakupan tabel.

## Dibandingkan dengan Alternatif

Untuk konteks Indonesia, MABIMS.dev lebih akurat dari Umm al-Qura (standar Saudi yang bisa selisih ±1 hari) dan Aladhan API (yang juga default ke Umm al-Qura). MABIMS.dev menggunakan data resmi Kemenag RI, bukan data dari otoritas negara lain.

Jika Anda saat ini menggunakan Aladhan API, lihat panduan [Migration dari Aladhan](/migration) untuk perbandingan format respons dan contoh kode migrasi.

## Repository

Kode sumber tersedia di [github.com/PijarAdiluhung/mabims-api](https://github.com/PijarAdiluhung/mabims-api). Kontribusi diterima melalui pull request.

## Lisensi

MABIMS.dev dilisensikan di bawah [MIT License](https://github.com/PijarAdiluhung/mabims-api/blob/main/LICENSE).

## Kontak

Untuk pertanyaan, dukungan teknis, atau kerja sama komersial:
- Email: [halo@pixostudio.id](mailto:halo@pixostudio.id)
- GitHub: [PijarAdiluhung/mabims-api](https://github.com/PijarAdiluhung/mabims-api)
