---
title: "Tanggal Hijriah, Sekarang Offline: Memperkenalkan mabims-hijri"
description: "Kenapa saya bikin JavaScript SDK offline-first untuk MABIMS, dan kapan pakai SDK vs REST API."
date: 2026-09-01
tags:
  - SDK
  - JavaScript
  - TypeScript
  - Hijriah
  - Offline
excerpt: "Kalau kamu cuma butuh tanggal Hijriah hari ini di website, REST API sudah cukup. Tapi kalau aplikasimu harus jalan offline, atau kamu capek manage rate limits? Kenalan sama mabims-hijri."
cover:
  image: ../../../assets/app.jpg
  alt: mabims-hijri SDK
authors:
  - pijar
---

Kalau kamu cuma butuh tanggal Hijriah hari ini di website, [REST API](https://mabims.dev/blog/cara-pakai-mabims-api) sudah cukup. Tinggal `fetch`, parse JSON, selesai.

Tapi setelah bikin beberapa pakai API itu, saya selalu nemu masalah yang sama:

- **Setiap load page nge-hit API.** Padahal tanggal Hijriah nggak berubah tiap beberapa detik.
- **Rate limits oke, tapi tetap ada batasnya.** Kalau site-mu lagi traffic naik, atau banyak component yang fetch tanggal yang sama...
- **Offline nggak ada.** Bikin PWA atau mobile app? Nggak ada tanggal Hijriah tanpa koneksi internet.
- **Caching jadi urusanmu.** Kamu harus bikin caching layer sendiri, handle data stale, dan tentuin TTL-nya.

Makanya saya bikin **[mabims-hijri](https://www.npmjs.com/package/mabims-hijri)**, paket npm offline-first yang bundle data MABIMS 2024-2026 langsung di dalamnya.

## Apa yang dilakukan

```
Bundled MABIMS (2024-2026)  -->  Local cache  -->  Live API (fallback)
     ~70KB, built-in              TTL 24h          only when out of range
```

1. Data MABIMS 2024-2026 di-bundle langsung di dalam package (~70KB)
2. Kalau online, SDK cek `/meta` buat data yang lebih baru dan auto-sync
3. Kalau tanggal di luar range bundle, fallback ke live API
4. Semua operasi `today()`, `convert()`, dan `range()` jalan tanpa internet

Nggak perlu API key. Nggak perlu registrasi. Tinggal `npm install`.

## Quick start

```bash
npm install mabims-hijri
```

```typescript
import { today, convert } from 'mabims-hijri';

// Tanggal Hijriah hari ini, jalan offline
const date = await today();
console.log(`${date.output.day} ${date.output.month_name} ${date.output.year} H`);

// Konversi tanggal tertentu
const ramadhan = await convert('2026-02-19');
console.log(ramadhan.output.month_name); // 'Ramadhan'
```

Gitu aja. Nggak perlu base URL, nggak perlu headers, nggak perlu fetch wrapper. Datanya sudah ada di dalam app.

## SDK vs REST API: Kapan pakai yang mana?

Saya masih ngerasa REST API itu pilihan yang tepat buat banyak kasus. Ini cara saya membedakannya:

**Pakai REST API kalau:**
- Kamu butuh hilal sky chart (`/hilal/viz`)
- Kamu butuh data di luar 2024-2026 dan nggak mau bundle
- Kamu bikin server-side integration di mana kamu manage caching sendiri
- Kamu mau pakai OpenAPI spec lengkap dan code generation

**Pakai SDK kalau:**
- Kamu cuma butuh tanggal hari ini, konversi, atau events di app JS/TS
- Kamu mau support offline (PWA, mobile app, jaringan nggak stabil)
- Kamu mau zero-config, nggak perlu fetch wrapper, nggak perlu caching logic
- Kamu capek manage rate limits buat data yang sama

Contohnya, di React app:

```tsx
import { useState, useEffect } from 'react';
import { today, type HijriDate } from 'mabims-hijri';

function HijriDate() {
  const [date, setDate] = useState<HijriDate | null>(null);

  useEffect(() => {
    today().then((res) => setDate(res.output));
  }, []);

  if (!date) return <span>Loading...</span>;
  return <span>{date.day} {date.month_name} {date.year} H</span>;
}
```

Nggak perlu manage API URL. Nggak perlu debug loading state. Tinggal import dan pakai.

## Isi SDK-nya

| Fungsi | Fungsinya |
|--------|-----------|
| `today()` | Tanggal Hijriah hari ini, timezone-aware |
| `convert(date)` | Konversi satu tanggal, dua arah |
| `range(start, end)` | Konversi bulk (maks 45 hari) |
| `month(year, month)` | Semua hari dalam satu bulan |
| `year(year)` | Semua hari dalam satu tahun (12 bulan) |
| `events(year)` | Hari besar Islam (Ramadhan, Idul Fitri, dll.) |
| `hilal.info(month, year)` | Data visibilitas hilal |

Semua ini jalan offline selama tanggal masih di dalam range yang di-bundle.

## Catatan untuk React Native

Kalau kamu bikin React Native app, kamu perlu set storage adapter biar caching-nya persisten:

```typescript
import { setStorageAdapter } from 'mabims-hijri';
import AsyncStorage from '@react-native-async-storage/async-storage';

class RNStorage implements StorageAdapter {
  private prefix = 'mabims_';
  async get(key: string) { return AsyncStorage.getItem(this.prefix + key); }
  async set(key: string, value: string) { await AsyncStorage.setItem(this.prefix + key, value); }
  async has(key: string) { return (await AsyncStorage.getItem(this.prefix + key)) !== null; }
}

setStorageAdapter(new RNStorage());
```

Tanpa ini, cache reset tiap kali app restart.

## Intinya

Kalau kebutuhan Hijriah di app-mu cuma "tampilin tanggal hari ini di header," jangan bikin caching layer, jangan bikin fetch wrapper, dan jangan pusing soal rate limits.

```bash
npm install mabims-hijri
```

Satu import, satu fungsi, selesai, online atau offline.

Dokumentasi lengkap ada di [mabims.dev/sdk](https://mabims.dev/sdk/). Source code di GitHub: [PijarAdiluhung/mabims-hijri](https://github.com/PijarAdiluhung/mabims-hijri).

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Kenalan sama mabims-hijri: Tanggal Hijriah, Sekarang Offline",
  "description": "Kenapa saya bikin JavaScript SDK offline-first untuk MABIMS, dan kapan pakai SDK vs REST API.",
  "datePublished": "2026-08-31",
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
    "@id": "https://mabims.dev/blog/introducing-mabims-hijri-sdk"
  }
}
</script>
