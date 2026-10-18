# Open Video Watermark

[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.12-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-red.svg)](https://flask.palletsprojects.com/)

A Flask web application that embeds invisible watermarks into video files using frequency-domain DCT (Discrete Cosine Transform) techniques. Includes a web UI, a REST API, and real-time processing progress via WebSocket.

## Features

- **Invisible watermarking**: DCT-based frequency-domain embedding; watermarks are not visually apparent
- **Watermark extraction**: Extract previously embedded watermarks via the `/extract` API endpoint
- **Web interface**: Single-page application with drag-and-drop upload and a file manager
- **Real-time progress**: Frame-by-frame processing updates pushed over WebSocket (Socket.IO)
- **Background processing**: A queue-backed worker thread handles encoding without blocking the UI
- **File management**: List, download, and delete processed files from the web UI or API
- **Input validation**: Magic-number MIME checks, extension allow-listing, and OpenCV validation
- **Rate limiting**: Per-endpoint request limits enforced in `security.py`
- **Security headers**: CSP, HSTS, X-Frame-Options, and Referrer-Policy applied via middleware
- **Docker support**: `Dockerfile` and `docker-compose.yml` provided; Nginx reverse-proxy config included

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/fabriziosalmi/open-video-watermark.git
cd open-video-watermark
make setup   # copies .env.example to .env and creates required directories
```

Edit `.env` to set at least `SECRET_KEY`, then start the application:

```bash
make run         # development mode (port 8000)
make production  # production mode with Nginx (port 80)
```

Access the UI at `http://localhost:8000` (development) or `http://localhost` (production).

### Manual installation

**System dependencies (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3-dev python3-pip libgl1-mesa-glx libglib2.0-0
```

**Application setup:**
```bash
git clone https://github.com/fabriziosalmi/open-video-watermark.git
cd open-video-watermark
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # then edit .env
python app.py
```

The server starts on `http://localhost:8000`.

## Usage

### Web interface

1. Open `http://localhost:8000` in a browser.
2. On the **Embed Watermark** tab, drag and drop or select one or more video files.
3. Enter watermark text (up to 50 characters) and choose a strength value (0.05–0.3).
4. Click **Process Videos** and watch the per-file progress bars update in real time.
5. Switch to the **Manage Files** tab to download or delete processed files.

### Watermark strength

| Range | Effect |
|-------|--------|
| 0.05–0.1 | Low — minimal perceptual impact, less robust to re-encoding |
| 0.1–0.2 | Medium — balanced (default: 0.1) |
| 0.2–0.3 | High — more detectable visually, more robust to re-encoding |

### Supported formats

MP4, AVI, MOV, MKV, WMV, FLV, WebM

## Configuration

Copy `.env.example` to `.env` and adjust as needed. All values are optional except `SECRET_KEY` in production.

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | auto-generated | Flask session secret; set explicitly in production |
| `DEBUG` | `false` | Enable Flask debug mode |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Listen port |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins, or `*` |
| `MAX_FILE_SIZE_MB` | `500` | Maximum upload size in MB |
| `MAX_WATERMARK_LENGTH` | `50` | Maximum watermark text length |
| `DEFAULT_STRENGTH` | `0.1` | Default embedding strength |
| `MIN_STRENGTH` | `0.05` | Minimum allowed strength |
| `MAX_STRENGTH` | `0.3` | Maximum allowed strength |
| `BLOCK_SIZE` | `8` | DCT block size |
| `FRAME_SAMPLE_RATE` | `30` | Frame sampling interval used during extraction |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `LOG_FILE` | `logs/app.log` | Log file path |

### Docker volumes

| Host path | Container path | Purpose |
|-----------|---------------|---------|
| `./uploads` | `/app/uploads` | Temporary uploaded files |
| `./processed` | `/app/processed` | Watermarked output files |
| `./logs` | `/app/logs` | Application logs |

## API

Full endpoint documentation with request/response examples is in [API.md](API.md).

Quick reference:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/system/info` | System and application info |
| `GET` | `/metrics` | Processing and storage metrics |
| `POST` | `/upload` | Upload videos for watermarking |
| `GET` | `/status/<task_id>` | Processing status for a task |
| `POST` | `/extract` | Extract watermark from a video |
| `POST` | `/validate` | Validate a video file |
| `POST` | `/estimate-time` | Estimate processing time |
| `GET` | `/files` | List processed files |
| `GET` | `/download/<file_id>` | Download a processed file |
| `DELETE` | `/delete/<file_id>` | Delete a processed file |
| `GET` | `/queue/status` | Processing queue stats |
| `GET` | `/batch-status` | Status of all tasks (latest 10) |

Example — extract a watermark:
```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@watermarked_video.mp4" \
  -F "watermark_length=15"
```

## Project Structure

```
open-video-watermark/
├── app.py                   # Flask application and routes
├── config.py                # Configuration (reads from environment)
├── security.py              # Rate limiting and security middleware
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Multi-container setup
├── nginx.conf               # Nginx reverse-proxy configuration
├── Makefile                 # Development convenience commands
├── .env.example             # Environment variable template
├── watermark/
│   ├── dct_watermark.py     # DCT watermarking algorithm
│   └── video_processor.py   # Video I/O and frame processing
├── static/
│   ├── css/style.css
│   └── js/app.js
├── templates/
│   └── index.html
├── uploads/                 # Runtime: uploaded files (git-ignored)
├── processed/               # Runtime: watermarked files (git-ignored)
├── logs/                    # Runtime: log files (git-ignored)
└── tests/
    └── test_comprehensive.py
```

## Development

### Make commands

```bash
make help        # List all commands
make setup       # Copy .env.example and create runtime directories
make install     # pip install -r requirements.txt
make dev         # Run locally with python app.py
make build       # Build Docker image
make run         # Start containers (development)
make production  # Start containers with Nginx (production profile)
make stop        # Stop containers
make logs        # Tail application logs
make shell       # Open a shell in the running container
make test        # Run tests with pytest and coverage
make lint        # Run flake8
make format      # Run black
make clean       # Remove containers, images, and volumes
```

### Running tests

```bash
make test
# or directly:
pytest -v --cov=watermark tests/
```

## Security

For a production deployment:

- Set a strong `SECRET_KEY` in `.env`:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- Set `CORS_ORIGINS` to your actual domain(s) instead of `*`.
- Run behind a reverse proxy with TLS; the included `nginx.conf` can be used as a starting point.
- Run the container as a non-root user.
- Schedule regular cleanup of the `uploads/` and `processed/` directories.

See [SECURITY.md](SECURITY.md) for more details.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository and create a feature branch.
2. Make changes and add or update tests as appropriate.
3. Run `make lint` and `make test` to verify.
4. Open a pull request.

## License

MIT — see [LICENSE](LICENSE).
