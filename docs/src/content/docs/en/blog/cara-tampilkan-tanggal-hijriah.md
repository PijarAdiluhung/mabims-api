---
title: "How to Display Hijri Dates with MABIMS Criteria"
description: "Want to show today's Hijri date on your website? Like in a header, footer, or mosque/pesantren widget? Here's the easiest way: use the free mabims.dev API, no API key needed, with data matching MABIMS/Kemenag criteria (not Umm al-Qura which is often 1 day off)."
date: 2026-08-30
tags:
  - Tutorial
  - Hijri
  - MABIMS
  - JavaScript
  - PHP
  - WordPress
excerpt: "Want to show today's Hijri date on your website? Like in a header, footer, or mosque/pesantren widget? Here's the easiest way: use the free mabims.dev API, no API key needed, with data matching MABIMS/Kemenag criteria (not Umm al-Qura which is often 1 day off)."
cover:
  image: ../../../../assets/kalender.jpg
  alt: MABIMS Hijri calendar display
authors:
  - pijar
---

Want to show today's Hijri date on your website? Like in a header, footer, or mosque/pesantren widget? Here's the easiest way: use the free [mabims.dev](https://mabims.dev) API, no API key needed, with data matching MABIMS/Kemenag criteria (not Umm al-Qura which is often 1 day off).

Just call this endpoint:

```
GET https://api.mabims.dev/api/v1/today
```

It returns JSON like this:

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

You only need the `output` part — it already has `day`, `month_name`, and `year` as separate fields, so no string parsing needed.

## Option 1: JavaScript (Vanilla, No Framework)

Most universal. Just drop it into any HTML.

```html
<span id="hijri-date">Loading...</span>

<script>
  fetch('https://api.mabims.dev/api/v1/today')
    .then(res => res.json())
    .then(data => {
      document.getElementById('hijri-date').textContent = data.output.date + ' H'
    })
    .catch(() => {
      document.getElementById('hijri-date').textContent = '-'
    })
</script>
```

Done. The `<span>` will automatically show today's Hijri date, like `1448-03-14 H`.

Want a nicer format with month names instead of numbers? **No manual mapping needed** — the response already provides `day`, `month_name`, and `year` as separate fields:

```js
fetch('https://api.mabims.dev/api/v1/today')
  .then(res => res.json())
  .then(data => {
    const { day, month_name, year } = data.output
    document.getElementById('hijri-date').textContent =
      `${day} ${month_name} ${year} H`
  })
  .catch(() => {
    document.getElementById('hijri-date').textContent = '-'
  })
```

Result: `14 Rabiul Akhir 1448 H`. No string parsing or custom month name arrays needed. This is different from most other Hijri calendar APIs that return raw dates and force you to map month names yourself.

## Option 2: PHP

For PHP-based websites (custom or legacy CMS), use `file_get_contents` or `curl`:

```php
<?php
$response = file_get_contents('https://api.mabims.dev/api/v1/today');
$data = json_decode($response, true);
$hijriDate = $data['output']['date'] ?? '-';
?>

<span><?= htmlspecialchars($hijriDate) ?> H</span>
```

Want month names instead of numbers? The response already provides `day`, `month_name`, and `year` as separate fields:

```php
<?php
$output = $data['output'] ?? [];
$hijriDate = isset($output['day'])
    ? "{$output['day']} {$output['month_name']} {$output['year']} H"
    : '-';
?>

<span><?= htmlspecialchars($hijriDate) ?></span>
```

If your server has `allow_url_fopen` disabled, use cURL instead:

```php
<?php
$ch = curl_init('https://api.mabims.dev/api/v1/today');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 5);
$response = curl_exec($ch);
curl_close($ch);

$data = json_decode($response, true);
$hijriDate = $data['output']['date'] ?? '-';
?>
```

**Tip:** since this is a blocking server-side request, cache the result (e.g., file cache for 1 hour) so you don't hit the API on every page load.

```php
<?php
$cacheFile = __DIR__ . '/hijri-cache.json';
$cacheTime = 3600; // 1 hour

if (file_exists($cacheFile) && (time() - filemtime($cacheFile) < $cacheTime)) {
    $data = json_decode(file_get_contents($cacheFile), true);
} else {
    $response = file_get_contents('https://api.mabims.dev/api/v1/today');
    $data = json_decode($response, true);
    file_put_contents($cacheFile, $response);
}

$hijriDate = $data['output']['date'] ?? '-';
```

## Option 3: WordPress (Shortcode)

If your website runs on WordPress, add this to your theme's `functions.php` (or a custom plugin):

```php
function show_hijri_date() {
    $cache = get_transient('hijri_date_today');
    if ($cache !== false) {
        return $cache;
    }

    $response = wp_remote_get('https://api.mabims.dev/api/v1/today');
    if (is_wp_error($response)) {
        return '-';
    }

    $body = json_decode(wp_remote_retrieve_body($response), true);
    $date = $body['output']['date'] ?? '-';
    $result = esc_html($date) . ' H';

    set_transient('hijri_date_today', $result, HOUR_IN_SECONDS);
    return $result;
}
add_shortcode('hijri_date', 'show_hijri_date');
```

Then use the shortcode `[hijri_date]` in any page, text widget, or block editor. WordPress handles the request via `wp_remote_get` (safer than raw `file_get_contents`), and `set_transient` caches the result for 1 hour so the API isn't called on every page load.

## Bonus: Show a Full Month Calendar (Not Just Today)

If you need more than just today's date — say, a **monthly calendar grid** (e.g., a complete 29-30 day Hijri widget) — use the `/month` endpoint:

```
GET https://api.mabims.dev/api/v1/month?year={Y}&month={M}&calendar=hijri
```

Example, fetch Ramadan 1447 H:

```
GET https://api.mabims.dev/api/v1/month?year=1447&month=9&calendar=hijri
```

Each item in the response contains a Gregorian-Hijri date pair, so you can loop through to build a grid:

```js
fetch('https://api.mabims.dev/api/v1/month?year=1447&month=9&calendar=hijri')
  .then(res => res.json())
  .then(data => {
    const listEl = document.getElementById('hijri-calendar')
    data.items.forEach(item => {
      const li = document.createElement('li')
      li.textContent = `${item.hijri} (${item.gregorian})`
      listEl.appendChild(li)
    })
  })
```

**Key parameters:**
- `year` & `month` — required. `month` is 1–12.
- `calendar` — default `hijri`. Set to `gregorian` if the `year`/`month` you're providing is Gregorian, not Hijri.

Hijri months beyond the official table coverage (e.g., far future dates) are still served automatically via Neo MABIMS computation, as long as they're within the supported range — no special handling needed on your end.

### Need a Full Year at Once?

Instead of calling `/month` 12 times for an annual calendar, the `/year` endpoint returns all months in one request:

```
GET https://api.mabims.dev/api/v1/year?year=1447&calendar=hijri
```

The response is grouped by month (keys `"1"` through `"12"`), each containing an array of days with the same format as `/month`:

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

Perfect if you want to build an annual calendar page with a single fetch, no multiple requests per month.

## Other Languages/Frameworks?

The principle is the same in any language: just HTTP GET to `https://api.mabims.dev/api/v1/today`, parse the JSON, and grab `output.date`.

Full documentation for other endpoints (date conversion, monthly calendars, Islamic events) is at [mabims.dev/quickstart](https://mabims.dev/en/quickstart).

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "How to Display Hijri Dates with MABIMS Criteria",
  "description": "Want to show today's Hijri date on your website? Like in a header, footer, or mosque/pesantren widget? Here's the easiest way: use the free mabims.dev API, no API key needed, with data matching MABIMS/Kemenag criteria (not Umm al-Qura which is often 1 day off).",
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
    "@id": "https://mabims.dev/en/blog/cara-tampilkan-tanggal-hijriah"
  }
}
</script>
