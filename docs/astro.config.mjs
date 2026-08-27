// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://mabims.dev',
  integrations: [
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
      ],
      sidebar: [
        { label: 'Quickstart', link: '/quickstart', translations: { en: 'Quickstart' } },
        { label: 'Access & Rate Limits', link: '/access', translations: { en: 'Access & Rate Limits' } },
        {
          label: 'API Reference',
          translations: { en: 'API Reference' },
          items: [
            { label: 'GET /convert', link: '/endpoints/convert' },
            { label: 'GET /today', link: '/endpoints/today' },
            { label: 'GET /range & /month', link: '/endpoints/range-month' },
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
            { label: 'Hilal', link: '/playground/hilal', translations: { en: 'Hilal' } },
          ],
        },
        { label: 'Data Coverage', link: '/data-coverage', translations: { en: 'Data Coverage' } },
        { label: 'FAQ', link: '/faq', translations: { en: 'FAQ' } },
      ],
    }),
  ],
});
