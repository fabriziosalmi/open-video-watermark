# Open Video Watermark - Installation & Usage Guide

## 🎯 Project Overview

The **Open Video Watermark** application is a robust, self-contained web application that embeds invisible watermarks into video files using advanced DCT (Discrete Cosine Transform) frequency-domain techniques. The watermarks are designed to be resilient to compression and re-encoding.

### ✨ Key Features

- **🔒 Invisible Watermarking**: Uses DCT frequency-domain embedding for robust, invisible watermarks
- **🌐 Modern Web Interface**: Clean, responsive single-page application with real-time updates
- **⚡ Real-time Progress**: Live WebSocket updates showing frame-by-frame processing progress
- **🔄 Background Processing**: Queue-based video processing prevents UI blocking
- **📁 File Management**: Complete file lifecycle management (upload, process, download, delete)
- **🛡️ Error Handling**: Comprehensive error handling and user feedback
- **📱 Responsive Design**: Works seamlessly on desktop and mobile devices

## 🏗️ Architecture

### Backend (Python Flask)
- **Flask**: Web framework with SocketIO for real-time communication
- **DCT Watermarking**: Frequency-domain embedding in video frames
- **OpenCV**: Video processing and computer vision operations
- **Background Workers**: Threaded processing queue for video operations

### Frontend (Modern JavaScript)
- **Vanilla JavaScript**: No external framework dependencies
- **WebSocket Communication**: Real-time progress updates
- **Modern CSS**: Responsive design with CSS Grid and Flexbox
- **Progressive Enhancement**: Works with and without JavaScript

### Watermarking Technology
- **DCT Transform**: Embeds data in frequency domain coefficients
- **Block-based Processing**: 8x8 pixel block processing for robustness
- **Compression Resistant**: Survives JPEG/video compression
- **Configurable Strength**: Balance between invisibility and robustness

## 🔧 Installation

### Method 1: Automated Setup (Recommended)

```bash
# Clone or download the project
cd open-video-watermark

# Run the automated setup and start script
./run.sh
```

The script will:
- Check Python installation
- Create virtual environment
- Install dependencies
- Run tests (optional)
- Start the application

### Method 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests (optional)
python test_watermark.py

# Start application
python app.py
```

### System Requirements

- **Python 3.8+**
- **OpenCV dependencies** (automatically installed via pip)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)
- **Minimum 4GB RAM** (for video processing)
- **Storage space** for uploaded and processed videos

## 🔐 Security Configuration

### Environment Variables

Before running the application, especially in production, you must configure environment variables:

1. **Copy the environment template**:
```bash
cp .env.example .env
```

2. **Generate a secure secret key**:
```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env
```

3. **Edit the .env file** and update these critical settings:
```bash
# Security - REQUIRED for production
SECRET_KEY=your-generated-secret-key-here
DEBUG=false
CORS_ORIGINS=https://yourdomain.com  # Replace * with actual domains

# File paths (use absolute paths for production)
UPLOAD_FOLDER=/app/uploads
PROCESSED_FOLDER=/app/processed

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### File Validation

The application now includes multiple layers of file validation:
- **Extension checking**: Validates file extensions
- **Magic number validation**: Uses python-magic to verify file types
- **OpenCV validation**: Ensures files are readable video formats

Install system dependencies for magic number detection:

**Ubuntu/Debian**:
```bash
sudo apt-get install libmagic1
```

**macOS**:
```bash
brew install libmagic
```

**CentOS/RHEL**:
```bash
sudo yum install file-devel
```

## 📝 Logging

The application now includes comprehensive logging:

- **Console logging**: Real-time feedback during development
- **File logging**: Persistent logs in `logs/app.log`
- **Structured logging**: Includes timestamps, log levels, and context
- **Error tracking**: Full stack traces for debugging

Log levels available: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

View logs in real-time:
```bash
tail -f logs/app.log
```

## 🚀 Usage

### Starting the Application

1. **Run the startup script**:
   ```bash
   ./run.sh
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

### Embedding Watermarks

1. **Switch to "Embed Watermark" tab**
2. **Upload videos**: Click to select or drag-and-drop video files
   - Supported formats: MP4, AVI, MOV, MKV, WMV, FLV, WebM
   - Maximum file size: 500MB per file
3. **Enter watermark text**: Up to 50 characters
4. **Adjust embedding strength**: 
   - Lower (0.05-0.1): More invisible, less robust
   - Higher (0.2-0.3): More robust, potentially visible
5. **Click "Start Processing"**
6. **Monitor progress**: Real-time updates show frame-by-frame progress

### Managing Files

1. **Switch to "Manage Files" tab**
2. **View processed files**: See all watermarked videos
3. **Download files**: Click download button for any processed video
4. **Delete files**: Remove files from server storage
5. **Refresh list**: Update the file list manually

## 🧪 Testing

### Run All Tests
```bash
python test_watermark.py
```

### Create Demo Video
```bash
python create_demo.py --duration 5 --output test_video.mp4
```

### Test Individual Components
```bash
# Test just setup
./run.sh --setup

# Test functionality only
./run.sh --test
```

## ⚙️ Configuration

### Environment Variables (.env)
```env
SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
HOST=0.0.0.0
PORT=5000
MAX_CONTENT_LENGTH=524288000  # 500MB
UPLOAD_FOLDER=uploads
PROCESSED_FOLDER=processed
```

### Application Settings (config.py)
- **Watermarking parameters**: Strength, block size
- **File upload limits**: Size, types, watermark length
- **UI settings**: Default tab, toast duration
- **Processing settings**: Progress intervals, sample rates

## 📁 Project Structure

```
open-video-watermark/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── run.sh                 # Automated setup script
├── test_watermark.py      # Test suite
├── create_demo.py         # Demo video creator
├── README.md              # Documentation
├── .env                   # Environment variables
├── .gitignore             # Git ignore rules
├── watermark/             # Core watermarking modules
│   ├── __init__.py
│   ├── dct_watermark.py   # DCT watermarking implementation
│   └── video_processor.py # Video processing utilities
├── templates/             # HTML templates
│   └── index.html         # Main application template
├── static/                # Frontend assets
│   ├── css/
│   │   └── style.css      # Modern CSS styles
│   └── js/
│       └── app.js         # Frontend JavaScript
├── uploads/               # Temporary upload storage
└── processed/             # Processed video storage
    └── registry.json      # File metadata registry
```

## 🔬 Technical Details

### Watermarking Algorithm

1. **Frame Extraction**: Extract frames from input video
2. **Block Division**: Divide each frame into 8x8 pixel blocks
3. **DCT Transform**: Apply Discrete Cosine Transform to each block
4. **Coefficient Modification**: Modify mid-frequency coefficients based on watermark bits
5. **Inverse DCT**: Transform back to spatial domain
6. **Frame Reconstruction**: Reconstruct watermarked video

### Real-time Communication

- **WebSocket Connection**: Persistent connection for progress updates
- **Room-based Updates**: Each processing task has its own update channel
- **Progress Callbacks**: Frame-by-frame progress reporting
- **Status Management**: Queue, processing, completed, error states

### File Management

- **Secure Upload**: Filename sanitization and validation
- **Registry System**: JSON-based metadata storage
- **Automatic Cleanup**: Temporary file removal after processing
- **Download Security**: Secure file serving with proper headers

## 🛠️ Development

### Adding New Video Formats

1. Update `ALLOWED_EXTENSIONS` in `config.py`
2. Test with `VideoProcessor.validate_video_file()`
3. Verify OpenCV codec support

### Modifying Watermarking Algorithm

1. Edit `DCTWatermark` class in `watermark/dct_watermark.py`
2. Adjust block size, coefficient positions, or embedding strength
3. Run tests to verify changes

### Customizing UI

1. Modify styles in `static/css/style.css`
2. Update templates in `templates/index.html`
3. Extend functionality in `static/js/app.js`

## 🚨 Troubleshooting

### Common Issues

**Environment Configuration**:
```bash
# Missing .env file
cp .env.example .env
# Edit .env with your settings
```

**python-magic Installation Problems**:
```bash
# Ubuntu/Debian
sudo apt-get install libmagic1 python3-magic
pip install python-magic

# macOS
brew install libmagic
pip install python-magic

# If still having issues, try:
pip install python-magic-bin
```

**OpenCV Installation Problems**:
```bash
pip install --upgrade pip
pip install opencv-python-headless
```

**Permission Errors**:
```bash
chmod +x run.sh
sudo chown -R $USER:$USER .
# Create log directory
mkdir -p logs
chmod 755 logs
```

**CORS Issues**:
- Update `CORS_ORIGINS` in .env file
- For development: `CORS_ORIGINS=*`  
- For production: `CORS_ORIGINS=https://yourdomain.com`

**File Upload Failures**:
- Check file format is supported (mp4, avi, mov, mkv, wmv, flv, webm)
- Verify file is not corrupted
- Check `MAX_FILE_SIZE_MB` setting
- Review logs: `tail -f logs/app.log`

**Port Already in Use**:
- Change `PORT` in `.env` file
- Or kill existing process: `lsof -ti:8000 | xargs kill`

**Large File Upload Issues**:
- Check `MAX_CONTENT_LENGTH` setting
- Verify disk space availability
- Monitor browser network timeouts

### Debug Mode

Enable detailed logging:
```bash
# In .env file
DEBUG=True
LOG_LEVEL=DEBUG

# Then restart the application
python app.py
```

### Checking Logs

View application logs:
```bash
# Real-time log monitoring
tail -f logs/app.log

# View recent errors
grep ERROR logs/app.log | tail -20

# View all logs from today
grep "$(date +%Y-%m-%d)" logs/app.log
```

### Performance Optimization

- Reduce video resolution before processing
- Adjust `PROGRESS_UPDATE_INTERVAL` for fewer updates
- Use SSD storage for better I/O performance

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check this documentation
2. Run the test suite: `python test_watermark.py`
3. Review application logs
4. Create an issue with detailed error information

---

**Happy Watermarking! 🎬✨**
