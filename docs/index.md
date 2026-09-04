---
layout: home
title: Open Video Watermark — Invisible DCT Video Watermarking in Python
titleTemplate: false

hero:
  name: "Open Video Watermark"
  text: "Invisible video watermarking using frequency-domain DCT."
  tagline: "Embed imperceptible, compression-resilient watermarks into video files. Features a responsive web UI, REST API, and real-time WebSocket progress updates."
  actions:
    - theme: brand
      text: Get Started
      link: /guide/introduction
    - theme: alt
      text: Installation & Docker
      link: /guide/installation
    - theme: alt
      text: REST API Reference
      link: /guide/api

features:
  - icon: 🔒
    title: Invisible DCT Watermarking
    details: Embeds data into mid-frequency Discrete Cosine Transform coefficients, imperceptible to viewers but resilient to re-encoding.
  - icon: ⚡
    title: Real-Time WebSockets
    details: Live frame-by-frame progress pushed straight to the browser UI via Flask-SocketIO without polling.
  - icon: 🔄
    title: Non-Blocking Background Queue
    details: Dedicated worker threads handle intensive video transcoding while keeping the HTTP server responsive.
  - icon: 🌐
    title: REST API & Web UI
    details: Full single-page web interface with drag-and-drop file upload plus automated REST endpoints for programmatic pipelines.
  - icon: 🛡️
    title: Enterprise Security
    details: Strict CSP headers, rate-limiting middleware, magic-number MIME validation, and OpenCV integrity verification.
  - icon: 🐳
    title: Docker & Nginx Production
    details: Pre-configured multi-container stack with Nginx reverse proxy, static caching, and environment configuration.
---
