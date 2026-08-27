---
title: "Tutorial Integrasi"
description: "Contoh integrasi API mabims.dev dari yang paling sederhana sampai yang agak proper: JavaScript, Vue, React, sampai mobile."
date: 2026-08-28
tags:
  - Tutorial
  - JavaScript
  - Integrasi
  - Hijriah
excerpt: "Contoh integrasi dari JavaScript vanilla, Vue, React, sampai mobile. Semua tanpa library tambahan."
cover:
  image: ../../../assets/tutorial.jpg
  alt: Tutorial integrasi API
authors:
  - pijar
---

API ini memang saya bikin buat developer, saya nggak mau integrasinya berhenti di dokumentasi yang isinya cuma `GET /today` lalu selesai. Jadi di tulisan ini saya mau kasih contoh dari yang paling sederhana sampai yang agak proper: JavaScript biasa, Vue, React, sampai aplikasi mobile.

## Paling sederhana: JavaScript

Kalau website kamu cuma butuh menampilkan tanggal Hijriah hari ini, sebenarnya sesimpel ini:

```js
const response = await fetch("https://api.mabims.dev/api/v1/today");
const data = await response.json();

console.log(data);
```

Response-nya kira-kira begini:

```json
{
  "input": { "date": "2026-08-28", "calendar": "gregorian", "tz": "Asia/Jakarta" },
  "output": { "date": "1448-03-15", "calendar": "hijri" },
  "source": "mabims",
  "warnings": []
}
```

Kamu tinggal ambil field `output.date` untuk ditampilkan. Formatnya `YYYY-MM-DD`, jadi tinggal di-split:

```js
const [year, month, day] = data.output.date.split("-");
document.querySelector("#hijri-date").textContent = `${day} ${month} ${year} H`;
```

Jadi misalnya di header website kamu ada:

```html
<div id="hijri-date"></div>
```

tinggal panggil fungsi tadi dan tanggal Hijriahnya akan muncul.

Nggak perlu install library. Nggak perlu API key. Nggak perlu bikin server sendiri cuma untuk mengambil tanggal Hijriah.

## Kalau pakai timezone

Ini bagian yang menurut saya penting.

Tanggal Hijriah bukan cuma soal konversi tanggal Masehi → Hijriah. **Timezone juga menentukan "hari ini" itu hari apa.**

Misalnya server kamu berada di Amerika, tapi user kamu kebanyakan di Indonesia. Jangan sampai jam 00:30 WIB dianggap masih tanggal sebelumnya karena server kamu masih berada di hari sebelumnya.

mabims.dev menyediakan timezone override supaya kamu bisa menentukan timezone yang ingin digunakan. Pakai parameter `tz`:

```js
const response = await fetch(
  "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta"
);

const data = await response.json();
```

Untuk aplikasi yang memang targetnya Indonesia, saya biasanya akan eksplisit menggunakan `Asia/Jakarta`, `Asia/Makassar`, atau `Asia/Jayapura` sesuai kebutuhan.

## Di Vue

Kalau kamu pakai Vue, konsepnya sama. Bedanya cuma kita simpan hasil API ke state.

Misalnya dengan Composition API:

```vue
<script setup>
import { ref, onMounted } from "vue";

const hijriDate = ref(null);

onMounted(async () => {
  const response = await fetch(
    "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta"
  );

  hijriDate.value = await response.json();
});
</script>

<template>
  <div v-if="hijriDate">
    {{ hijriDate.output.date }}
  </div>

  <div v-else>
    Memuat tanggal Hijriah...
  </div>
</template>
```

Selesai.

Saya justru menyarankan pendekatan seperti ini daripada memasukkan library kalender Hijriah yang ukurannya jauh lebih besar kalau kebutuhan aplikasi kamu cuma **menampilkan tanggal Hijriah**.

## Di React

Di React juga kurang lebih sama:

```jsx
import { useEffect, useState } from "react";

export default function HijriDate() {
  const [date, setDate] = useState(null);

  useEffect(() => {
    fetch("https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta")
      .then((response) => response.json())
      .then((data) => setDate(data));
  }, []);

  if (!date) {
    return <span>Memuat tanggal Hijriah...</span>;
  }

  return <span>{date.output.date}</span>;
}
```

Tidak ada dependency tambahan.

React tinggal fetch API → simpan hasilnya → render.

## Kalau butuh tanggal tertentu

`/today` cocok kalau yang kamu butuhkan adalah tanggal Hijriah hari ini.

Tapi bagaimana kalau user memilih tanggal dari date picker?

Misalnya user memilih:

> 17 Agustus 2026

Kamu bisa menggunakan endpoint konversi:

```js
const response = await fetch(
  "https://api.mabims.dev/api/v1/convert?date=2026-08-17"
);

const data = await response.json();
```

Ini berguna untuk kalender, form, artikel yang punya tanggal publikasi, atau fitur pencarian tanggal.

Misalnya user memilih tanggal 17 Agustus 2026 dan kamu ingin menampilkan versi Hijriahnya. Tinggal kirim tanggal Gregorian tersebut ke API.

## Jangan lupa cek `source`

Ada satu hal yang menurut saya cukup penting ketika mengonsumsi API ini.

Response mabims.dev punya informasi `source`.

Secara sederhana, ada dua kemungkinan:

- `mabims` — tanggal berasal dari tabel resmi Kemenag yang tersedia.
- `mabims-computed` — tanggal dihitung menggunakan kriteria Neo MABIMS sebagai fallback ketika tanggal tersebut berada di luar cakupan tabel.

Kenapa saya expose informasi ini?

Karena saya nggak mau API diam-diam memberikan hasil perhitungan lalu developer mengira itu adalah tanggal yang secara eksplisit tercantum di tabel resmi.

Kalau aplikasi kamu cukup serius soal kalender, kamu bisa menyimpan atau menampilkan informasi tersebut.

```js
if (data.source === "mabims-computed") {
  console.log("Tanggal menggunakan hasil perhitungan Neo MABIMS");
}
```

Dan kalau API mengembalikan `warnings`, sebaiknya jangan dibuang begitu saja.

```js
if (data.warnings?.length) {
  console.warn(data.warnings);
}
```

## Kalau aplikasinya mobile

Kalau kamu bikin aplikasi Android/iOS, prinsipnya sebenarnya sama.

Mau Flutter, React Native, Kotlin, Swift, atau framework lainnya, selama aplikasinya bisa melakukan HTTP request, kamu bisa memanggil API ini.

Misalnya pseudocode-nya:

```text
GET https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta

        ↓

JSON response

        ↓

Simpan ke state

        ↓

Tampilkan:
"1448-03-15"
```

API-nya tidak peduli apakah request datang dari browser, server, atau aplikasi mobile.

## Tapi apakah setiap halaman harus request ke API?

Nah, ini yang mulai masuk ke urusan arsitektur.

Kalau website kamu punya 100 komponen yang semuanya membutuhkan tanggal Hijriah, **jangan setiap komponen melakukan `fetch("/today")` sendiri-sendiri.**

Lebih baik fetch sekali, kemudian hasilnya dipakai bersama.

Di frontend kamu bisa bikin composable/hook/service sendiri.

Misalnya di React:

```js
export async function getHijriToday() {
  const response = await fetch(
    "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta"
  );

  if (!response.ok) {
    throw new Error("Gagal mengambil tanggal Hijriah");
  }

  return response.json();
}
```

Kemudian komponen-komponen lain tinggal menggunakan fungsi tersebut.

Untuk aplikasi yang lebih besar, bahkan bisa kamu cache hasilnya karena tanggal Hijriah tidak berubah setiap beberapa detik.

## Kalau pakai SSR atau backend?

Ini malah lebih menarik.

Kalau kamu menggunakan Next.js, Nuxt, Laravel, Rails, Django, atau backend lainnya, kamu juga bisa memanggil mabims.dev dari server kamu.

Contohnya secara sederhana:

```js
const response = await fetch(
  "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta"
);

const hijriDate = await response.json();
```

Kemudian server kamu yang mengirimkan tanggal tersebut ke browser.

Keuntungannya, tanggal Hijriah bisa sudah tersedia ketika halaman pertama kali dirender.

Tapi kalau kamu melakukan ini, tetap pikirkan caching. Tidak ada gunanya server kamu request tanggal yang sama berkali-kali dalam sehari.

## Jadi kapan sebaiknya pakai API ini?

Menurut saya, kalau kebutuhanmu cuma:

> "Saya ingin menampilkan tanggal Hijriah di website saya."

Jangan bikin sistem kalender sendiri.

Jangan maintain tabel sendiri.

Jangan copy-paste tanggal dari kalender PDF ke database.

Dan jangan berharap library kalender yang default-nya Umm al-Qura otomatis cocok untuk kebutuhan Indonesia.

Cukup:

```text
Website / App
      ↓
mabims.dev
      ↓
Tanggal Hijriah berbasis MABIMS
```

Kalau butuh tanggal hari ini, pakai `/today`.

Kalau butuh konversi tanggal tertentu, pakai `/convert`.

Kalau aplikasinya butuh timezone tertentu, tentukan timezone-nya secara eksplisit.

Dan kalau aplikasimu penting secara administratif atau keagamaan, **tetap perlakukan API sebagai sumber data teknis, bukan pengganti keputusan resmi Kemenag.**

Karena pada akhirnya, alasan saya bikin API ini dari awal juga bukan supaya developer punya "library tanggal Hijriah yang lain".

Saya cuma ingin ketika seorang developer Indonesia menulis:

```js
fetch("https://api.mabims.dev/api/v1/today")
```

dia nggak perlu bertanya lagi:

**"Ini kalendernya pakai standar siapa?"**
