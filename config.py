# Open Video Watermark Configuration

## Application Settings
APP_NAME = "Open Video Watermark"
VERSION = "1.0.0"

## Watermarking Settings
DEFAULT_STRENGTH = 0.1
MIN_STRENGTH = 0.05
MAX_STRENGTH = 0.3
BLOCK_SIZE = 8

## File Upload Settings
ALLOWED_EXTENSIONS = ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm']
MAX_FILE_SIZE_MB = 500
MAX_WATERMARK_LENGTH = 50

## Processing Settings
PROGRESS_UPDATE_INTERVAL = 10  # frames
FRAME_SAMPLE_RATE = 30  # for extraction

## UI Settings
DEFAULT_TAB = "embed"
TOAST_DURATION = 5000  # milliseconds

## Security Settings
# Change this in production!
SECRET_KEY = "your-secret-key-change-in-production"

## Development Settings
DEBUG = True
HOST = "0.0.0.0"
PORT = 8000
