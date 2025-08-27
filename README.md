# 🎬 Open Video Watermark

[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.12-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-red.svg)](https://flask.palletsprojects.com/)

A robust, professional video watermarking web application that embeds invisible watermarks into video files using advanced frequency-domain DCT techniques. Built with modern web technologies and containerized for easy deployment.

## ✨ Features

### Core Functionality
- **🔒 Invisible Watermarking**: Uses DCT (Discrete Cosine Transform) for robust frequency-domain watermarking (enhanced robustness in v1.0.0)
- **🧪 Watermark Extraction**: Extract embedded watermarks from processed videos via API
- **🌐 Modern Web Interface**: Clean, responsive single-page application with intuitive design
- **⚡ Real-time Progress**: Live updates on video processing with WebSocket communication
- **🔄 Background Processing**: Queue-based video processing to prevent UI blocking
- **📁 File Management**: View, download, and delete processed files with organized interface
- **🛡️ Robust Error Handling**: Graceful handling of invalid files and processing errors

### Advanced Features
- **🎛️ Processing Options**: Customizable watermark strength and advanced settings
- **📊 Progress Tracking**: Detailed progress bars with frame-by-frame updates
- **🧰 Video Validation**: Comprehensive validation endpoint to preflight-check video files
- **📈 Metrics & Monitoring**: Application metrics endpoint and system info for observability
- **🧵 Batch & Queue**: Batch status endpoint for multi-file operations
- **🔐 Security**: Rate limiting, input validation, secure headers, and safe file handling
- **🐳 Docker Ready**: Full containerization with Docker Compose support
- **🚀 Production Ready**: Nginx reverse proxy configuration included
- **📱 Mobile Responsive**: Works seamlessly on desktop and mobile devices

## 🚀 Quick Start

### Docker Deployment (Recommended)

1. **Clone and setup**:
```bash
git clone https://github.com/fabriziosalmi/open-video-watermark.git
cd open-video-watermark
make setup  # Creates .env file and directories
```

2. **Configure environment**:
```bash
# Edit .env file with your settings
cp .env.example .env
nano .env
```

3. **Start the application**:
```bash
# Development mode
make run

# Production mode with Nginx
make production
```

4. **Access the application**:
   - Development: http://localhost:8000
   - Production: http://localhost (port 80)

### Manual Installation

1. **Prerequisites**:
```bash
# Python 3.12+ required
python --version

# Install system dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install python3-dev python3-pip libgl1-mesa-glx libglib2.0-0
```

2. **Setup application**:
```bash
git clone https://github.com/fabriziosalmi/open-video-watermark.git
cd open-video-watermark

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. **Run application**:
```bash
python app.py
# Access at http://localhost:8000
```

## 📖 Usage Guide

### Basic Watermarking

1. **Upload Videos**: 
   - Navigate to the "Embed Watermark" tab
   - Drag & drop or select video files (MP4, AVI, MOV, etc.)
   - Supported formats: MP4, AVI, MOV, MKV, WMV, FLV, WebM

2. **Configure Watermark**:
   - Enter your watermark text (up to 50 characters)
   - Adjust watermark strength (0.05 - 0.3)
   - Configure advanced options (optional)

3. **Process Videos**:
   - Click "Process Videos" to start
   - Monitor real-time progress
   - Receive notifications on completion

4. **Manage Files**:
   - Switch to "Manage Files" tab
   - Download processed videos
   - Delete unwanted files

### Advanced Options

- **Watermark Strength**: Controls embedding intensity
  - Low (0.05-0.1): Subtle, harder to detect
  - Medium (0.1-0.2): Balanced visibility/robustness
  - High (0.2-0.3): Strong, more detectable

- **Block Size**: DCT block size for processing (default: 8x8)
- **Frame Sampling**: Processing frame rate control

## 🐳 Docker Configuration

### Services

- **video-watermark**: Main application container
- **nginx**: Reverse proxy (production profile)

### Environment Variables

```bash
# Security
SECRET_KEY=your-very-secure-secret-key

# Application
FLASK_ENV=production
HOST=0.0.0.0
PORT=8000

# File limits
MAX_CONTENT_LENGTH=524288000  # 500MB
MAX_WATERMARK_LENGTH=50

# Processing
DEFAULT_STRENGTH=0.1
BLOCK_SIZE=8
```

### Volume Mounts

- `./uploads:/app/uploads` - Uploaded videos
- `./processed:/app/processed` - Processed videos  
- `./logs:/app/logs` - Application logs

## 🛠️ Development

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (for containerized development)
- Make (optional, for convenience commands)

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/fabriziosalmi/open-video-watermark.git
cd open-video-watermark

# Setup environment
make setup
make install

# Run in development mode
make dev
```

### Available Make Commands

```bash
make help        # Show all available commands
make build       # Build Docker image
make run         # Run in development
make production  # Run with production setup
make test        # Run tests
make logs        # View application logs
make clean       # Clean Docker resources
```

### Testing

New comprehensive tests are included for v1.0.0.

- Run all tests:
```bash
make test
```

- Run the comprehensive suite directly:
```bash
pytest -q tests/test_comprehensive.py
```

- With coverage:
```bash
pytest --cov=watermark tests/
```

```bash
# Run tests
make test

# With coverage
pytest --cov=watermark tests/

# Manual testing
python test_watermark.py
```

## 📂 Project Structure

```
open-video-watermark/
├── app.py                  # Main Flask application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Multi-container setup
├── nginx.conf             # Nginx configuration
├── Makefile              # Development commands
├── watermark/            # Core watermarking modules
│   ├── __init__.py
│   ├── dct_watermark.py  # DCT watermarking implementation
│   └── video_processor.py # Video processing utilities
├── static/               # Frontend assets
│   ├── css/
│   │   └── style.css    # Application styles
│   └── js/
│       └── app.js       # Frontend JavaScript
├── templates/            # HTML templates
│   └── index.html       # Main application template
├── uploads/             # Uploaded video files
├── processed/           # Processed video files
├── logs/               # Application logs
└── tests/              # Test files
    └── test_watermark.py
```

## 🔧 Technical Details

### Backend Architecture

- **Framework**: Flask 2.3.3 with SocketIO for real-time communication
- **Video Processing**: OpenCV 4.8.1 for frame manipulation
- **Watermarking**: Enhanced DCT-based frequency-domain embedding with redundancy and improved robustness
- **Queue System**: Threading-based background processing
- **File Handling**: Secure upload/download with validation
- **APIs**: New endpoints for extraction, validation, metrics, and batch status

### Frontend Technology

- **UI**: Modern responsive design with CSS Grid/Flexbox
- **JavaScript**: ES6+ with WebSocket support
- **Real-time Updates**: Socket.IO client for live progress
- **File Handling**: Drag & drop interface with preview

### Security Features

- Input validation and sanitization
- Secure filename handling
- Rate limiting (application-level and via Nginx)
- Security headers (CSP, HSTS, X-Frame-Options, Referrer-Policy)
- Content-Type validation (magic number checks)
- File size limits

See SECURITY.md and the new security middleware in security.py.

### Performance Optimizations

- Background video processing
- Efficient DCT implementation
- Memory management for large files
- Progress streaming
- Docker multi-stage builds

## 🔐 Security Considerations

### For Production Deployment

- Set a strong SECRET_KEY and RATE_LIMIT_SALT in your environment.
- Consider setting CORS_ORIGINS to a restricted list.
- Run behind a reverse proxy with SSL/TLS.
- Review API.md for endpoint rate limits and expected payloads.

1. **Change default secret key**:
```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

2. **Configure reverse proxy**:
   - Use the included Nginx configuration
   - Enable SSL/TLS certificates
   - Configure rate limiting

3. **File system security**:
   - Run container as non-root user
   - Mount volumes with appropriate permissions
   - Regular cleanup of processed files

4. **Network security**:
   - Use Docker networks
   - Limit exposed ports
   - Configure firewall rules

## 📊 Performance

### Benchmarks

- **Processing Speed**: ~30 FPS for 1080p video (on modern hardware)
- **Memory Usage**: ~500MB base + ~100MB per concurrent video
- **Storage**: Processed videos ~same size as originals
- **Scalability**: Supports multiple concurrent processing tasks

### System Requirements

**Minimum**:
- CPU: 2 cores, 2.0 GHz
- RAM: 2GB available
- Storage: 10GB for application + video storage
- Network: 100 Mbps for large file uploads

**Recommended**:
- CPU: 4+ cores, 3.0+ GHz  
- RAM: 8GB+ available
- Storage: SSD with 50GB+ free space
- Network: 1 Gbps

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Standards

- Follow PEP 8 for Python code
- Use Black for code formatting
- Add docstrings for new functions
- Include unit tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenCV community for video processing capabilities
- Flask team for the excellent web framework
- Socket.IO for real-time communication
- DCT watermarking research community

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/fabriziosalmi/open-video-watermark/issues)
- **Discussions**: [GitHub Discussions](https://github.com/fabriziosalmi/open-video-watermark/discussions)
- **Security**: Report security issues privately via email

## 📡 API Overview

A full API reference with examples is available in API.md.

Quick examples:

- Extract watermark from a video:
```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@watermarked_video.mp4" \
  -F "watermark_length=15"
```

- Validate a video file:
```bash
curl -X POST http://localhost:8000/validate \
  -F "file=@video.mp4"
```

- Estimate processing time:
```bash
curl -X POST http://localhost:8000/estimate-time \
  -F "file=@video.mp4" \
  -F "watermark_text=My Watermark"
```

## 📝 Changelog

See CHANGELOG.md for a detailed list of changes. Latest release: v1.0.0.

---

**Made with ❤️ for the open source community**
