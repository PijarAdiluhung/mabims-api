// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightBlog from 'starlight-blog';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://mabims.dev',
  integrations: [
    sitemap(),
    starlight({
      title: 'API Kalender MABIMS',
      description:
        'API konversi tanggal Hijriah resmi MABIMS untuk Indonesia. Data Kemenag, bukan Umm al-Qura.',
      favicon: '/favicons/favicon.ico',
      logo: {
        src: './public/mabims-long.png',
        alt: 'mabims.dev',
        replacesTitle: true,
      },
      social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/PijarAdiluhung/mabims-api' }],
      customCss: ['./src/custom.css'],
      components: {
        Footer: './src/components/CustomFooter.astro',
      },
      locales: {
        root: { label: 'Bahasa Indonesia', lang: 'id' },
        en: { label: 'English', lang: 'en' },
      },
      head: [
        {
          tag: 'link',
          attrs: { rel: 'apple-touch-icon', sizes: '180x180', href: '/favicons/apple-touch-icon.png' },
        },
        {
          tag: 'link',
          attrs: { rel: 'manifest', href: '/favicons/site.webmanifest' },
        },
        {
          tag: 'link',
          attrs: {
            rel: 'preconnect',
            href: 'https://fonts.googleapis.com',
          },
        },
        {
          tag: 'link',
          attrs: {
            rel: 'preconnect',
            href: 'https://fonts.gstatic.com',
            crossorigin: '',
          },
        },
        {
          tag: 'link',
          attrs: {
            rel: 'stylesheet',
            href: 'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap',
          },
        },
        {
          tag: 'meta',
          attrs: { name: 'theme-color', content: '#23262f' },
        },
        {
          tag: 'meta',
          attrs: { name: 'twitter:card', content: 'summary_large_image' },
        },
        {
          tag: 'meta',
          attrs: { name: 'twitter:image', content: 'https://mabims.dev/og-image.png' },
        },
        {
          tag: 'script',
          content: `
            (function() {
              var base = 'https://mabims.dev';
              var path = window.location.pathname.replace(/\\/$/, '') || '/';
              var segments = path.split('/').filter(Boolean);

              // BreadcrumbList schema
              var nameMap = {
                quickstart: 'Quickstart', access: 'Access & Rate Limits',
                endpoints: 'API Reference', today: 'GET /today', convert: 'GET /convert',
                'range-month': 'GET /range & /month', year: 'GET /year', events: 'GET /events',
                hilal: 'GET /hilal', meta: 'GET /meta', playground: 'Playground',
                converter: 'Konverter', kalender: 'Kalender', 'data-coverage': 'Data Coverage',
                migration: 'Migration', faq: 'FAQ', changelog: 'Changelog', blog: 'Blog'
              };
              var crumbs = [{ name: 'Home', url: base }];
              var current = '';
              for (var i = 0; i < segments.length; i++) {
                var seg = segments[i];
                if (i === 0 && (seg === 'en' || seg === 'id')) { current += '/' + seg; continue; }
                current += '/' + seg;
                var name = nameMap[seg] || seg.charAt(0).toUpperCase() + seg.slice(1).replace(/-/g, ' ');
                crumbs.push({ name: name, url: base + current });
              }
              var bcSchema = {
                '@context': 'https://schema.org',
                '@type': 'BreadcrumbList',
                itemListElement: crumbs.map(function(c, idx) {
                  return { '@type': 'ListItem', position: idx + 1, name: c.name, item: c.url };
                })
              };
              var el = document.createElement('script');
              el.type = 'application/ld+json';
              el.text = JSON.stringify(bcSchema);
              document.head.appendChild(el);

              // FAQPage schema (only on FAQ pages)
              if (path === '/faq' || path === '/en/faq') {
                var isEn = path.indexOf('/en/') === 0;
                var faqData = isEn ? [
                  { q: 'What is MABIMS?', a: 'MABIMS is the rukyah criterion (Ministers of Religious Affairs of Brunei, Indonesia, Malaysia, Singapore) used by Indonesia\'s Ministry of Religious Affairs (Kemenag RI) to determine the start of the Hijriah month. The Neo MABIMS criterion requires the hilal to be visible at least 3 degrees with an elongation of at least 6.4 degrees at sunset.' },
                  { q: 'Why is the Hijriah date in my app different from the Indonesian government announcement?', a: 'Most Hijriah calendar APIs and apps use the Umm al-Qura (Saudi Arabia) criterion as the default. Because the rukyah method and observation location differ, the result can be plus or minus 1 day off from Kemenag\'s official decision.' },
                  { q: 'MABIMS vs Umm al-Qura - which is more accurate for Indonesia?', a: 'For use in Indonesia, MABIMS is more accurate because it follows Kemenag RI\'s official decision through the isbat session, not Saudi authority. Umm al-Qura is designed for Saudi Arabia\'s needs and does not represent Indonesia\'s rukyah/hisab results.' },
                  { q: 'Is this API an official product of Kemenag or MABIMS?', a: 'No. This API is independent, built by PIXO Studio using official Kemenag RI table data as its source. For legal certainty in Islamic law, always refer to official Kemenag announcements.' },
                  { q: 'Is this API free and does it require an API key?', a: 'Yes, it is free and requires no authentication. Just call the endpoint directly, with no registration or API key needed.' },
                  { q: 'Can it be used directly from the frontend?', a: 'Yes. CORS is open, so it can be called directly from the browser on any domain. For rate limit details and fair use policy, see the Access and Rate Limits page.' },
                  { q: 'What is the difference between source mabims and source mabims-computed?', a: 'mabims - date taken directly from Kemenag\'s official table. mabims-computed - automatically calculated using Neo MABIMS criteria because the date falls outside the official table\'s coverage.' },
                  { q: 'How far ahead does the data go?', a: 'Official table data is available for 2024 to 2026. Outside that range, the API calculates automatically using Neo MABIMS criteria up to the year 2053.' },
                  { q: 'What timezone is used by default?', a: 'Asia/Jakarta (UTC+7) by default, specifically for the /today endpoint. You can override it with the tz parameter using an IANA zone or a UTC offset.' },
                  { q: 'How do I convert between Gregorian and Hijri dates?', a: 'Use GET /convert?date=YYYY-MM-DD and calendar=gregorian or calendar=hijri depending on the conversion direction.' },
                  { q: 'How do I check hilal visibility for a given month?', a: 'Use the /hilal/info endpoint for criterion data, or /hilal/viz for a hilal visibility chart showing moon position, crescent direction, and VISIBLE/NOT VISIBLE verdict.' },
                  { q: 'Is this API open source?', a: 'Yes, the source code is open on GitHub: PijarAdiluhung/mabims-api. Contributions and issue reports are always welcome.' }
                ] : [
                  { q: 'Apa itu MABIMS?', a: 'MABIMS singkatan dari Menteri-menteri Agama Brunei, Indonesia, Malaysia, Singapura. Istilah ini lebih sering dipakai dalam konteks kriteria rukyah yang digunakan Kemenag RI untuk menentukan awal bulan Hijriah. Kriteria Neo MABIMS mensyaratkan hilal terlihat minimal 3 derajat dan elongasi minimal 6,4 derajat saat matahari terbenam.' },
                  { q: 'Kenapa tanggal Hijriah di aplikasi saya beda dengan yang diumumkan pemerintah Indonesia?', a: 'Kebanyakan API dan aplikasi kalender Hijriah memakai kriteria Umm al-Qura (Arab Saudi) sebagai default. Karena metode rukyah dan lokasi pengamatannya berbeda, hasilnya bisa selisih plus minus 1 hari dari keputusan resmi Kemenag.' },
                  { q: 'MABIMS vs Umm al-Qura, mana yang lebih akurat untuk Indonesia?', a: 'Untuk keperluan di Indonesia, MABIMS lebih akurat karena berdasarkan imkan rukyah, sehingga dapat diverifikasi Kemenag RI melalui sidang isbat. Umm al-Qura dirancang untuk kebutuhan Arab Saudi dan tidak merepresentasikan hasil rukyah Indonesia.' },
                  { q: 'Apakah API ini produk resmi Kemenag atau MABIMS?', a: 'Bukan. API ini independen, dibangun menggunakan data tabel resmi Kemenag RI sebagai sumber. Untuk kepastian hukum syar\'i, tetap rujuk pengumuman resmi Kemenag.' },
                  { q: 'Apakah API ini gratis dan butuh API key?', a: 'Ya, gratis dan tanpa autentikasi. Cukup panggil endpoint langsung, tanpa registrasi atau API key.' },
                  { q: 'Apakah bisa dipakai langsung dari frontend?', a: 'Bisa. CORS bersifat terbuka, jadi bisa dipanggil langsung dari browser di domain manapun. Untuk detail rate limit dan kebijakan penggunaan wajar, lihat halaman Access & Rate Limits.' },
                  { q: 'Apa bedanya source mabims dan source mabims-computed?', a: 'mabims - tanggal diambil langsung dari kalender resmi Kemenag. mabims-computed - dihitung otomatis dengan kriteria Neo MABIMS karena tanggal berada di luar cakupan tabel resmi.' },
                  { q: 'Data-nya sampai tahun berapa?', a: 'Cek info data terbaru di halaman Data Coverage. Di luar rentang itu, API menghitung otomatis (fallback) memakai kriteria Neo MABIMS.' },
                  { q: 'Zona waktu apa yang dipakai secara default?', a: 'Default-nya Asia/Jakarta (UTC+7), khusus untuk endpoint /today. Bisa di-override dengan parameter tz memakai zona IANA atau UTC offset.' },
                  { q: 'Bagaimana cara konversi tanggal Masehi ke Hijriah atau sebaliknya?', a: 'Pakai endpoint GET /convert?date=YYYY-MM-DD&calendar=gregorian atau calendar=hijri sesuai arah konversi yang diinginkan.' },
                  { q: 'Bagaimana cara mengecek visibilitas hilal untuk bulan tertentu?', a: 'Gunakan endpoint /hilal/info untuk data kriteria, atau /hilal/viz untuk grafik visibilitas hilal yang menampilkan posisi bulan, arah sabit, dan verdict TERLIHAT/TIDAK TERLIHAT.' },
                  { q: 'Apakah API ini open source?', a: 'Ya, kode sumbernya terbuka di GitHub: PijarAdiluhung/mabims-api. Kontribusi dan laporan isu selalu diterima.' }
                ];
                var faqSchema = {
                  '@context': 'https://schema.org',
                  '@type': 'FAQPage',
                  mainEntity: faqData.map(function(f) {
                    return {
                      '@type': 'Question',
                      name: f.q,
                      acceptedAnswer: { '@type': 'Answer', text: f.a }
                    };
                  })
                };
                var faqEl = document.createElement('script');
                faqEl.type = 'application/ld+json';
                faqEl.text = JSON.stringify(faqSchema);
                document.head.appendChild(faqEl);
              }
            })();
          `,
        },
      ],
      plugins: [
        starlightBlog({
          title: 'Blog',
          navigation: 'none',
          recentPostCount: 5,
          authors: {
            pijar: {
              name: 'Pijar Adiluhung',
              title: 'Developer',
              picture: '/favicons/android-chrome-512x512.png',
            },
          },
        }),
      ],
      sidebar: [
        { label: 'Quickstart', link: '/quickstart', translations: { en: 'Quickstart' } },
        { label: 'Access & Rate Limits', link: '/access', translations: { en: 'Access & Rate Limits' } },
        {
          label: 'API Reference',
          translations: { en: 'API Reference' },
          items: [
            { label: 'GET /today', link: '/endpoints/today' },
            { label: 'GET /convert', link: '/endpoints/convert' },
            { label: 'GET /range & /month', link: '/endpoints/range-month' },
            { label: 'GET /year', link: '/endpoints/year' },
            { label: 'GET /events', link: '/endpoints/events' },
            { label: 'GET /hilal', link: '/endpoints/hilal' },
            { label: 'GET /meta', link: '/endpoints/meta' },
          ],
        },
        {
          label: 'Playground',
          translations: { en: 'Playground' },
          items: [
            { label: 'Konverter', link: '/playground/converter', translations: { en: 'Converter' } },
            { label: 'Kalender', link: '/playground/kalender', translations: { en: 'Calendar' } },
            { label: 'Hilal', link: '/playground/hilal', translations: { en: 'Hilal' } },
          ],
        },
        { label: 'Data Coverage', link: '/data-coverage', translations: { en: 'Data Coverage' } },
        { label: 'Migration dari Aladhan', link: '/migration', translations: { en: 'Migration from Aladhan' } },
        { label: 'FAQ - Pertanyaan', link: '/faq', translations: { en: 'FAQ' } },
        { label: 'Changelog', link: '/changelog' },
        {
          label: 'Legal',
          translations: { en: 'Legal' },
          collapsed: true,
          items: [
            { label: 'Ketentuan', link: '/terms', translations: { en: 'Terms' } },
            { label: 'Privasi', link: '/privacy', translations: { en: 'Privacy' } },
            { label: 'Sumber Data', link: '/data-sources', translations: { en: 'Data Sources' } },
            { label: 'Disclaimer', link: '/disclaimer' },
          ],
        },
      ],
    }),
  ],
});
