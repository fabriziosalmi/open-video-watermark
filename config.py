# Open Video Watermark Configuration
import os
import secrets
import logging

## Application Settings
APP_NAME = "Open Video Watermark"
VERSION = "1.0.0"

## Watermarking Settings
DEFAULT_STRENGTH = float(os.getenv('DEFAULT_STRENGTH', 0.1))
MIN_STRENGTH = float(os.getenv('MIN_STRENGTH', 0.05))
MAX_STRENGTH = float(os.getenv('MAX_STRENGTH', 0.3))
BLOCK_SIZE = int(os.getenv('BLOCK_SIZE', 8))

## File Upload Settings
ALLOWED_EXTENSIONS = ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm']
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 500))
MAX_WATERMARK_LENGTH = int(os.getenv('MAX_WATERMARK_LENGTH', 50))

## Processing Settings
PROGRESS_UPDATE_INTERVAL = int(os.getenv('PROGRESS_UPDATE_INTERVAL', 10))  # frames
FRAME_SAMPLE_RATE = int(os.getenv('FRAME_SAMPLE_RATE', 30))  # for extraction

## UI Settings
DEFAULT_TAB = os.getenv('DEFAULT_TAB', "embed")
TOAST_DURATION = int(os.getenv('TOAST_DURATION', 5000))  # milliseconds

## Security Settings
def get_secret_key():
    """Get secret key from environment or generate a secure one"""
    secret = os.getenv('SECRET_KEY')
    if not secret or secret == "your-secret-key-change-in-production":
        # Generate a secure secret key and warn user
        secret = secrets.token_hex(32)
        logging.warning("Using auto-generated secret key. Set SECRET_KEY environment variable for production!")
    return secret

SECRET_KEY = get_secret_key()

## Development Settings
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes', 'on')
HOST = os.getenv('HOST', "0.0.0.0")
PORT = int(os.getenv('PORT', 8000))

## CORS Settings
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')

## Logging Settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
