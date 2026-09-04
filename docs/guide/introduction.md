# Introduction to Open Video Watermark

**Open Video Watermark** is a production-ready web application and developer toolkit that embeds **invisible, imperceptible watermarks** into video files using frequency-domain **Discrete Cosine Transform (DCT)** algorithms.

Designed for content creators, media platforms, and digital rights enforcement, the embedded watermarks are imperceptible to the human eye while remaining recoverable even after compression, transcoding, and filtering.

---

## 🌟 Key Highlights

- **🔒 DCT Frequency-Domain Watermarking**: Embeds watermarks in middle-frequency DCT coefficients of individual video frames.
- **⚡ Real-Time Progress with WebSockets**: Frame-by-frame progress streaming using Flask-SocketIO.
- **🔄 Asynchronous Worker Queue**: Non-blocking encoding via background thread workers.
- **🌐 Dual Interface**: Full-featured Single Page Application (SPA) web UI plus a clean RESTful API.
- **🛡️ Hardened Security**: Magic-byte MIME detection, extension allow-listing, OpenCV frame verification, rate limiting, and strict CSP headers.
- **🐳 Container Ready**: Complete `Dockerfile` and `docker-compose.yml` with Nginx reverse proxy configurations.

---

## 🎯 How It Works: DCT Frequency Domain

Unlike traditional spatial watermarking (which modifies raw pixel values and is easily destroyed or noticed), DCT frequency-domain watermarking operates in the transformed frequency domain:

1. **Frame Extraction**: Each frame of the input video is extracted and converted to the YUV or YCrCb color space.
2. **Block Partitioning**: The luminance (Y) channel is divided into $8 \times 8$ pixel blocks.
3. **Discrete Cosine Transform**: Each $8 \times 8$ block is transformed into 64 orthogonal frequency coefficients.
4. **Mid-Frequency Embedding**: The watermark bit sequence is embedded into selected mid-frequency coefficients, balancing perceptual invisibility with robustness against lossy video compression (e.g. H.264 / AVC).
5. **Inverse DCT (IDCT)**: The spatial frame is reconstructed via IDCT and reassembled into the video stream.

---

## 🚀 Getting Started

To get started right away:
- Follow the [Installation Guide](/guide/installation) for Docker or manual setup.
- Explore the [API Reference](/guide/api) to automate watermarking in your pipeline.
- Read the [Changelog](/guide/changelog) for the latest release notes.
