import { defineConfig } from 'vitepress'

// Template VitePress con generazione sitemap automatica e SEO ottimizzato
// Sostituisci i placeholder:
// open-video-watermark: nome esatto del repository GitHub (es. open-bpm)
// Open Video Watermark: Titolo leggibile del progetto (es. OpenBPM)
// Invisible video watermarking in Python using frequency-domain DCT techniques with REST API and Web UI.: Descrizione concisa per SEO e Open Graph
// fabriziosalmi: fabriziosalmi

export default defineConfig({
  title: 'Open Video Watermark',
  description: 'Invisible video watermarking in Python using frequency-domain DCT techniques with REST API and Web UI.',
  base: '/open-video-watermark/',
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: true,

  // SITEMAP AUTOMATICO
  // Genera automaticamente sitemap.xml in fase di build con tutti gli URL indicizzati
  sitemap: {
    hostname: 'https://fabriziosalmi.github.io/open-video-watermark/',
  },

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/open-video-watermark/favicon.svg' }],
    ['link', { rel: 'apple-touch-icon', href: '/open-video-watermark/favicon.svg' }],
    ['link', { rel: 'canonical', href: 'https://fabriziosalmi.github.io/open-video-watermark/' }],
    ['meta', { name: 'theme-color', content: '#10b981' }],
    ['meta', { name: 'color-scheme', content: 'dark light' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'Open Video Watermark' }],
    ['meta', { property: 'og:description', content: 'Invisible video watermarking in Python using frequency-domain DCT techniques with REST API and Web UI.' }],
    ['meta', { property: 'og:url', content: 'https://fabriziosalmi.github.io/open-video-watermark/' }],
    ['meta', { property: 'og:image', content: 'https://fabriziosalmi.github.io/open-video-watermark/favicon.svg' }],
    ['meta', { name: 'twitter:card', content: 'summary' }],
    ['meta', { name: 'twitter:title', content: 'Open Video Watermark' }],
    ['meta', { name: 'twitter:description', content: 'Invisible video watermarking in Python using frequency-domain DCT techniques with REST API and Web UI.' }],
    ['meta', { name: 'twitter:image', content: 'https://fabriziosalmi.github.io/open-video-watermark/favicon.svg' }],
    ['meta', { name: 'robots', content: 'index, follow, max-image-preview:large' }],
    [
      'script',
      { type: 'application/ld+json' },
      JSON.stringify({
        '@context': 'https://schema.org',
        '@graph': [
          {
            '@type': 'SoftwareApplication',
            '@id': 'https://fabriziosalmi.github.io/open-video-watermark/#software',
            name: 'Open Video Watermark',
            operatingSystem: 'Cross-platform',
            applicationCategory: 'DeveloperApplication',
            description: 'Invisible video watermarking in Python using frequency-domain DCT techniques with REST API and Web UI.',
            url: 'https://fabriziosalmi.github.io/open-video-watermark/',
            license: 'https://opensource.org/licenses/MIT',
            codeRepository: 'https://github.com/fabriziosalmi/open-video-watermark',
            author: {
              '@type': 'Person',
              name: 'Fabrizio Salmi',
              url: 'https://github.com/fabriziosalmi',
            },
          },
          {
            '@type': 'WebSite',
            '@id': 'https://fabriziosalmi.github.io/open-video-watermark/#website',
            url: 'https://fabriziosalmi.github.io/open-video-watermark/',
            name: 'Open Video Watermark Documentation',
            description: 'Invisible video watermarking in Python using frequency-domain DCT techniques with REST API and Web UI.',
            publisher: {
              '@type': 'Person',
              name: 'Fabrizio Salmi',
              url: 'https://github.com/fabriziosalmi',
            },
            inLanguage: 'en-US',
          },
        ],
      }),
    ],
  ],

  themeConfig: {
    siteTitle: 'Open Video Watermark',

    nav: [
      { text: 'Guide', link: '/guide/introduction', activeMatch: '/guide/' },
      { text: 'API Reference', link: '/guide/api', activeMatch: '/guide/api' },
      { text: 'Changelog', link: '/guide/changelog' },
      { text: 'GitHub', link: 'https://github.com/fabriziosalmi/open-video-watermark' },
    ],

    sidebar: [
      {
        text: 'Overview & Guide',
        items: [
          { text: 'Introduction', link: '/guide/introduction' },
          { text: 'Installation & Setup', link: '/guide/installation' },
          { text: 'REST API Reference', link: '/guide/api' },
          { text: 'Changelog', link: '/guide/changelog' },
        ],
      },
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/fabriziosalmi/open-video-watermark' },
    ],

    search: {
      provider: 'local',
      options: {
        detailedView: true,
      },
    },

    outline: {
      level: [2, 3],
      label: 'On this page',
    },

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © Fabrizio Salmi',
    },

    docFooter: {
      prev: 'Previous',
      next: 'Next',
    },
  },

  markdown: {
    theme: {
      light: 'github-light',
      dark: 'github-dark',
    },
  },
})
