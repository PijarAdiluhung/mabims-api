---
title: "Cerita di Balik MABIMS API"
description: "Dari website Kemenag yang tanggalnya kacau, viral, sampai akhirnya dihapus... ini cerita kenapa mabims.dev dibuat."
date: 2026-08-27
tags:
  - Cerita
  - MABIMS
  - Kemenag
  - Hijriah
excerpt: "Dulu, website Kemenag pernah menampilkan tanggal Hijriah di halamannya. Banyak orang termasuk saya sendiri terbiasa mengandalkannya. Tinggal buka website, lihat pojok atas, jadi tahu deh sekarang tanggal berapa Hijriah. Sampai suatu hari, ada postingan viral...."
featured: true
cover:
  image: ../../../assets/eclipse.jpg
  alt: Gerhana bulan
authors:
  - pijar
---

Ada cerita lucu (dan sedikit menyedihkan) di balik mabims.dev.

Dulu, website Kemenag pernah menampilkan tanggal Hijriah di halamannya. Banyak orang termasuk saya sendiri terbiasa mengandalkannya. Tinggal buka website, lihat pojok atas, jadi tahu deh sekarang tanggal berapa Hijriah.

Sampai suatu hari, ada postingan viral. Kalender keluaran Kemenag bilang tanggal 30, tapi website Kemenag bilang udah masuk tanggal 1 bulan berikutnya. Selisih sehari.

Postingan itu itu nyebar. Rame. Orang-orang mempertanyakan kenapa situs resmi bisa beda sama kalendernya yang dikeluarkan sendiri.

## Solusinya? Dihapus aja

Saat itu saya nggak tahu detail di baliknya, apakah itu bug, salah kalkulasi, atau apa. Yang saya tahu, ujung-ujungnya elegan sekali: **tanggal Hijriah di website itu dihapus**. Bukan diperbaiki, dihapus. Masalah selesai sih iya... tapi kayak gimana gitu.

## Beberapa tahun kemudian, saya jadi junior dev

Waktu saya mulai kerja sebagai developer, saya baru ngerti apa yang mungkin terjadi. Kalau mau nampilin kalender Hijriah di web, cara paling gampang ya tinggal pasang library atau panggil API pihak ketiga. Dan hampir semua library/API kalender Hijriah yang gampang ditemukan itu defaultnya pakai kriteria **Umm al-Qura**, kalender resmi Arab Saudi.

Masuk akal kalau itu yang dipakai. Dokumentasinya lengkap, gampang diintegrasikan, gratis. Tapi Umm al-Qura itu dirancang untuk kebutuhan Arab Saudi, bukan hasil rukyah atau sidang isbat Kemenag RI. Makanya bisa beda ±1 hari dari yang diumumkan di Indonesia, persis kejadian yang bikin viral itu.

Jadi kemungkinan besar itu bukan "bug" dalam arti kesalahan kode. Itu bug karena pakai sumber data yang salah untuk konteks Indonesia.

## Isi gap-nya

Setelah nyadar itu, saya mikir: kalau developer lain di Indonesia mau bikin aplikasi yang nampilin kalender Hijriah dan pengen datanya sesuai keputusan Kemenag (bukan Saudi), opsinya dikit banget. Kebanyakan harus scraping manual atau maintain tabel sendiri (spoiler: developer =/= ahli astronomi).

Makanya saya bikin **mabims.dev**: API kalender Hijriah yang sumbernya dari kalender resmi Kemenag RI, pakai kriteria Neo MABIMS untuk fallback di luar cakupan. Gratis, tanpa API key, tinggal panggil endpoint.

Realistisnya... saya nggak tahu bakal banyak yang pakai atau nggak. Tapi minimal ada satu aplikasi yang pasti pakai: [kajian.malangmengaji.com](https://kajian.malangmengaji.com), yang saya bangun juga. Kalau nggak ada developer lain yang butuh, ya sudah... API ini akan tetap jalan buat aplikasi saya sendiri.

Tapi kalau kamu develop aplikasi yang butuh kalender Hijriah yang akurat buat Indonesia, silakan pakai. Gratis, open source, dan mudah-mudahan nggak akan pernah perlu dihapus karena ketauan salah tanggal :)

---

**Coba sekarang:**

```bash
curl "https://api.mabims.dev/api/v1/today"
```

Dokumentasi lengkap ada di [mabims.dev/quickstart](https://mabims.dev/quickstart).

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Cerita di Balik MABIMS API",
  "description": "Dari website Kemenag yang tanggalnya kacau, viral, sampai akhirnya dihapus... ini cerita kenapa mabims.dev dibuat.",
  "datePublished": "2026-08-27",
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
    "@id": "https://mabims.dev/blog/kenapa-saya-bikin-mabims-dev"
  }
}
</script>
