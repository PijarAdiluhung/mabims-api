// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightBlog from 'starlight-blog';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://mabims.dev',
  integrations: [
    sitemap({
      filter: (page) => !page.includes('/404'),
    }),
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
        Head: './src/components/JsonLdHead.astro',
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
        { label: 'Tentang', link: '/about', translations: { en: 'About' } },
        { label: 'Quickstart', link: '/quickstart', translations: { en: 'Quickstart' } },
        {
          label: 'API Reference',
          translations: { en: 'API Reference' },
          items: [
      { label: 'GET /today', link: '/endpoints/today' },
      { label: 'GET /convert & /range', link: '/endpoints/convert-range' },
      { label: 'GET /month & /year', link: '/endpoints/month-year' },
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
