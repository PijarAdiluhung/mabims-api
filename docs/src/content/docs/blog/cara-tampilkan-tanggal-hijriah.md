---
title: "Cara Menampilkan Tanggal Hijriah Kriteria MABIMS"
description: "Mau nampilin tanggal Hijriah hari ini di website? Misalnya di header, footer, atau widget masjid/pesantren? Ini cara paling gampang: pakai API gratis mabims.dev, tanpa API key, dan datanya sesuai kriteria MABIMS/Kemenag (bukan Umm al-Qura yang sering beda 1 hari)."
date: 2026-08-30
tags:
  - Tutorial
  - Hijriah
  - MABIMS
  - JavaScript
  - PHP
  - WordPress
excerpt: "Mau nampilin tanggal Hijriah hari ini di website? Misalnya di header, footer, atau widget masjid/pesantren? Ini cara paling gampang: pakai API gratis mabims.dev, tanpa API key, dan datanya sesuai kriteria MABIMS/Kemenag (bukan Umm al-Qura yang sering beda 1 hari)."
cover:
  image: ../../../assets/kalender.jpg
  alt: Kalender Hijriah kriteria MABIMS
authors:
  - pijar
---

Mau nampilin tanggal Hijriah hari ini di website? Misalnya di header, footer, atau widget masjid/pesantren? Ini cara paling gampang, pakai API gratis [mabims.dev](https://mabims.dev), tanpa API key, dan datanya sesuai kriteria MABIMS/Kemenag (bukan Umm al-Qura yang sering beda 1 hari).

Cukup panggil endpoint ini:

```
GET https://api.mabims.dev/api/v1/today
```

Responsnya JSON kayak gini:

```json
{
  "input": { "date": "2026-08-24", "calendar": "gregorian", "tz": "Asia/Jakarta" },
  "output": {
    "date": "1448-03-11",
    "calendar": "hijri",
    "day": 11,
    "month": 3,
    "month_name": "Rabiul Akhir",
    "year": 1448
  },
  "source": "mabims",
  "warnings": []
}
```

Yang kamu butuhin cuma bagian `output`, udah ada `day`, `month_name`, dan `year` terpisah, jadi nggak perlu parsing string tanggal sendiri.

## Opsi 1: JavaScript (Vanilla, Tanpa Framework)

Paling universal. Tinggal taruh di HTML manapun.

```html
<span id="tanggal-hijriah">Memuat...</span>

<script>
  fetch('https://api.mabims.dev/api/v1/today')
    .then(res => res.json())
    .then(data => {
      document.getElementById('tanggal-hijriah').textContent = data.output.date + ' H'
    })
    .catch(() => {
      document.getElementById('tanggal-hijriah').textContent = '-'
    })
</script>
```

Selesai. Elemen `<span>` itu bakal otomatis keisi tanggal Hijriah hari ini, misalnya `1448-03-14 H`.

Kalau mau format lebih rapi (nama bulan, bukan angka), kamu **nggak perlu mapping manual** karena response-nya udah nyediain `day`, `month_name`, dan `year` langsung, jadi tinggal dipakai:

```js
fetch('https://api.mabims.dev/api/v1/today')
  .then(res => res.json())
  .then(data => {
    const { day, month_name, year } = data.output
    document.getElementById('tanggal-hijriah').textContent =
      `${day} ${month_name} ${year} H`
  })
  .catch(() => {
    document.getElementById('tanggal-hijriah').textContent = '-'
  })
```

Hasilnya jadi: `14 Rabiul Awal 1448 H`. Gak perlu parsing string atau bikin array nama bulan sendiri. Ini beda dari kebanyakan API kalender Hijriah lain yang biasanya cuma ngasih tanggal mentah dan bikin kamu harus mapping nama bulan sendiri.

## Opsi 2: PHP

Buat website berbasis PHP (custom, atau CMS lawas), pakai `file_get_contents` atau `curl`:

```php
<?php
$response = file_get_contents('https://api.mabims.dev/api/v1/today');
$data = json_decode($response, true);
$tanggalHijriah = $data['output']['date'] ?? '-';
?>

<span><?= htmlspecialchars($tanggalHijriah) ?> H</span>
```

Mau format nama bulan (bukan angka)? Response-nya udah nyediain `day`, `month_name`, `year` langsung, jadi nggak perlu mapping manual:

```php
<?php
$output = $data['output'] ?? [];
$tanggalHijriah = isset($output['day'])
    ? "{$output['day']} {$output['month_name']} {$output['year']} H"
    : '-';
?>

<span><?= htmlspecialchars($tanggalHijriah) ?></span>
```

Kalau server kamu matiin `allow_url_fopen`, pakai cURL sebagai gantinya:

```php
<?php
$ch = curl_init('https://api.mabims.dev/api/v1/today');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 5);
$response = curl_exec($ch);
curl_close($ch);

$data = json_decode($response, true);
$tanggalHijriah = $data['output']['date'] ?? '-';
?>
```

**Tips:** karena ini request server-side yang blocking, sebaiknya di-cache (misal pakai file cache 1 jam) supaya nggak manggil API setiap kali halaman di-load oleh visitor.

```php
<?php
$cacheFile = __DIR__ . '/hijriah-cache.json';
$cacheTime = 3600; // 1 jam

if (file_exists($cacheFile) && (time() - filemtime($cacheFile) < $cacheTime)) {
    $data = json_decode(file_get_contents($cacheFile), true);
} else {
    $response = file_get_contents('https://api.mabims.dev/api/v1/today');
    $data = json_decode($response, true);
    file_put_contents($cacheFile, $response);
}

$tanggalHijriah = $data['output']['date'] ?? '-';
```

## Opsi 3: WordPress (Shortcode)

Kalau website kamu WordPress, tinggal tambahkan ini ke `functions.php` tema (atau plugin custom):

```php
function tampilkan_tanggal_hijriah() {
    $cache = get_transient('tanggal_hijriah_hari_ini');
    if ($cache !== false) {
        return $cache;
    }

    $response = wp_remote_get('https://api.mabims.dev/api/v1/today');
    if (is_wp_error($response)) {
        return '-';
    }

    $body = json_decode(wp_remote_retrieve_body($response), true);
    $tanggal = $body['output']['date'] ?? '-';
    $hasil = esc_html($tanggal) . ' H';

    set_transient('tanggal_hijriah_hari_ini', $hasil, HOUR_IN_SECONDS);
    return $hasil;
}
add_shortcode('tanggal_hijriah', 'tampilkan_tanggal_hijriah');
```

Lalu pakai shortcode `[tanggal_hijriah]` di halaman, widget teks, atau editor blok manapun. WordPress otomatis handle request-nya lewat `wp_remote_get` (lebih aman daripada `file_get_contents` langsung), dan `set_transient` bikin hasilnya ke-cache 1 jam biar nggak manggil API tiap page load.

## Bonus: Nampilin Kalender Sebulan Penuh (Bukan Cuma Hari Ini)

Kalau kamu bukan cuma butuh tanggal hari ini, tapi mau bikin **grid kalender bulanan** (misalnya widget kalender Hijriah lengkap 29-30 hari), pakai endpoint `/month`:

```
GET https://api.mabims.dev/api/v1/month?year={Y}&month={M}&calendar=hijri
```

Contoh, ambil bulan Ramadhan 1447 H:

```
GET https://api.mabims.dev/api/v1/month?year=1447&month=9&calendar=hijri
```

Setiap item dalam responsnya berisi pasangan tanggal Gregorian-Hijriah, jadi tinggal di-loop buat bikin grid:

```js
fetch('https://api.mabims.dev/api/v1/month?year=1447&month=9&calendar=hijri')
  .then(res => res.json())
  .then(data => {
    const listEl = document.getElementById('kalender-bulan')
    data.days.forEach(item => {
      const li = document.createElement('li')
      li.textContent = `${item.hijri} (${item.gregorian})`
      listEl.appendChild(li)
    })
  })
```

**Parameter penting:**
- `year` & `month` — wajib. `month` itu 1–12.
- `calendar` — default `hijri`. Set `gregorian` kalau `year`/`month` yang kamu kasih itu tahun/bulan Masehi, bukan Hijriah.

Bulan Hijriah yang di luar cakupan tabel resmi (misalnya jauh ke tahun-tahun mendatang) tetap dilayani otomatis lewat perhitungan Neo MABIMS, selama masih dalam rentang yang didukung, jadi gak perlu penanganan khusus di sisi kamu deh.

### Butuh Satu Tahun Penuh Sekaligus?

Daripada manggil `/month` 12 kali buat bikin kalender tahunan, ada endpoint `/year` yang langsung ngasih semua bulan sekaligus:

```
GET https://api.mabims.dev/api/v1/year?year=1447&calendar=hijri
```

Respons-nya dikelompokkan per bulan (key `"1"` sampai `"12"`), masing-masing berisi array hari dengan format sama seperti `/month`:

```json
{
  "input": { "year": 1447, "calendar": "hijri" },
  "count": 354,
  "months": {
    "1": [
      { "gregorian": "2025-06-27", "hijri": "1447-01-01", "source": "mabims" }
    ],
    "2": [ "..." ]
  },
  "warnings": []
}
```

Cocok kalau kamu mau bikin halaman kalender tahunan sekali fetch, tanpa harus request berkali-kali per bulan.

## Bahasa/Framework Lain?

Prinsipnya sama di semua bahasa: Cukup HTTP GET ke `https://api.mabims.dev/api/v1/today`, parse JSON, ambil `output.date`. 

Dokumentasi lengkap endpoint lain (konversi tanggal, kalender bulanan, hari besar Islam) ada di [mabims.dev/quickstart](https://mabims.dev/quickstart).

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Cara Menampilkan Tanggal Hijriah Kriteria MABIMS",
  "description": "Mau nampilin tanggal Hijriah hari ini di website? Misalnya di header, footer, atau widget masjid/pesantren? Ini cara paling gampang: pakai API gratis mabims.dev, tanpa API key, dan datanya sesuai kriteria MABIMS/Kemenag (bukan Umm al-Qura yang sering beda 1 hari).",
  "datePublished": "2026-08-30",
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
    "@id": "https://mabims.dev/blog/cara-tampilkan-tanggal-hijriah"
  }
}
</script>
