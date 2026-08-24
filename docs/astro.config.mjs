// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://mabims.pixostudio.id',
  integrations: [
    starlight({
      title: 'MABIMS Date Converter API',
      description:
        'Gregorian ⇄ Hijri date conversion following the MABIMS standard used in Singapore, Indonesia and Malaysia.',
      favicon: '/favicons/favicon.ico',
      social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/pixostudio' }],
      customCss: ['./src/custom.css'],
      head: [
        {
          tag: 'link',
          attrs: { rel: 'apple-touch-icon', sizes: '180x180', href: '/favicons/apple-touch-icon.png' },
        },
        {
          tag: 'link',
          attrs: { rel: 'manifest', href: '/favicons/site.webmanifest' },
        },
      ],
      sidebar: [
        { label: 'Quickstart', link: '/quickstart' },
        { label: 'Access & Rate Limits', link: '/access' },
        {
          label: 'API Reference',
          items: [
            { label: 'GET /convert', link: '/endpoints/convert' },
            { label: 'GET /today', link: '/endpoints/today' },
            { label: 'GET /range & /month', link: '/endpoints/range-month' },
            { label: 'GET /meta', link: '/endpoints/meta' },
          ],
        },
        { label: 'Playground', link: '/playground' },
        { label: 'Data Coverage', link: '/data-coverage' },
      ],
    }),
  ],
});
