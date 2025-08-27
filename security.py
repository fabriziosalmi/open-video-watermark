#!/usr/bin/env python3
"""
Security middleware and utilities for Open Video Watermark
Implements rate limiting, security headers, and production safety features.
"""

import time
import hashlib
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify, current_app
import logging
from datetime import datetime, timedelta
import re
import os

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.clients = defaultdict(deque)
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(self, client_id: str, limit: int, window: int) -> bool:
        """
        Check if client is within rate limit
        
        Args:
            client_id: Unique identifier for client (usually IP)
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            True if request is allowed, False if rate limited
        """
        now = time.time()
        
        # Cleanup old entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup()
            self.last_cleanup = now
        
        # Get client's request history
        client_requests = self.clients[client_id]
        
        # Remove requests outside the window
        while client_requests and client_requests[0] < now - window:
            client_requests.popleft()
        
        # Check if under limit
        if len(client_requests) < limit:
            client_requests.append(now)
            return True
        
        return False
    
    def _cleanup(self):
        """Remove old client entries to prevent memory bloat"""
        now = time.time()
        clients_to_remove = []
        
        for client_id, requests in self.clients.items():
            # Remove requests older than 1 hour
            while requests and requests[0] < now - 3600:
                requests.popleft()
            
            # Remove clients with no recent requests
            if not requests:
                clients_to_remove.append(client_id)
        
        for client_id in clients_to_remove:
            del self.clients[client_id]
        
        logger.debug(f"Rate limiter cleanup: removed {len(clients_to_remove)} inactive clients")

# Global rate limiter instance
rate_limiter = RateLimiter()

def get_client_ip():
    """Get client IP address, considering proxies"""
    # Check for forwarded headers (common with reverse proxies)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Take the first IP in case of multiple proxies
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    return request.remote_addr or 'unknown'

def rate_limit(limit: int = 60, window: int = 60, per: str = 'ip'):
    """
    Rate limiting decorator
    
    Args:
        limit: Maximum requests allowed
        window: Time window in seconds
        per: Rate limiting key ('ip' for IP-based, 'user' for user-based)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if per == 'ip':
                client_id = get_client_ip()
            else:
                # For user-based rate limiting (would need authentication)
                client_id = request.headers.get('Authorization', get_client_ip())
            
            if not rate_limiter.is_allowed(client_id, limit, window):
                logger.warning(f"Rate limit exceeded for {client_id}: {limit}/{window}s")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {limit} requests per {window} seconds allowed',
                    'retry_after': window
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def add_security_headers(response):
    """Add security headers to response"""
    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self' ws: wss:; "
        "frame-ancestors 'none';"
    )
    
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Remove server information
    response.headers['Server'] = 'OpenVideoWatermark/1.0'
    
    return response

def validate_filename(filename: str) -> bool:
    """
    Validate uploaded filename for security
    
    Args:
        filename: Filename to validate
        
    Returns:
        True if filename is safe, False otherwise
    """
    if not filename:
        return False
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check for null bytes
    if '\x00' in filename:
        return False
    
    # Check for suspicious extensions
    dangerous_extensions = {
        'exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'js', 'jar',
        'msi', 'dll', 'sh', 'py', 'php', 'jsp', 'asp', 'aspx'
    }
    
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    if ext in dangerous_extensions:
        return False
    
    # Check filename length
    if len(filename) > 255:
        return False
    
    # Check for control characters
    if any(ord(c) < 32 and c not in '\t\n\r' for c in filename):
        return False
    
    return True

def sanitize_input(text: str, max_length: int = None) -> str:
    """
    Sanitize user input text
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ''
    
    # Remove null bytes and control characters
    sanitized = ''.join(c for c in text if ord(c) >= 32 or c in '\t\n\r')
    
    # Limit length
    if max_length:
        sanitized = sanitized[:max_length]
    
    # Strip whitespace
    sanitized = sanitized.strip()
    
    return sanitized

def validate_video_upload(file) -> tuple[bool, str]:
    """
    Validate uploaded video file for security
    
    Args:
        file: Uploaded file object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file:
        return False, "No file provided"
    
    # Check filename
    if not validate_filename(file.filename):
        return False, "Invalid filename"
    
    # Check file size (already handled by Flask's MAX_CONTENT_LENGTH, but double-check)
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset position
    
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024)  # 500MB
    if size > max_size:
        return False, f"File too large (max {max_size // (1024*1024)}MB)"
    
    if size < 1024:  # Minimum 1KB
        return False, "File too small"
    
    # Check file extension
    allowed_extensions = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}
    ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return False, f"File type not supported (allowed: {', '.join(allowed_extensions)})"
    
    return True, ""

def hash_client_id(client_ip: str, user_agent: str = None) -> str:
    """
    Create a hashed client identifier for privacy
    
    Args:
        client_ip: Client IP address
        user_agent: User agent string
        
    Returns:
        Hashed client identifier
    """
    # Include date to rotate hashes daily
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Combine IP, user agent, and date
    identifier = f"{client_ip}:{user_agent or ''}:{date_str}"
    
    # Hash with a secret salt (should be configured per deployment)
    salt = os.getenv('RATE_LIMIT_SALT', 'default-salt-change-in-production')
    
    return hashlib.sha256(f"{salt}:{identifier}".encode()).hexdigest()[:16]

class SecurityConfig:
    """Security configuration constants"""
    
    # Rate limits
    UPLOAD_RATE_LIMIT = (10, 60)  # 10 uploads per minute
    API_RATE_LIMIT = (100, 60)    # 100 API calls per minute
    EXTRACT_RATE_LIMIT = (5, 60)  # 5 extractions per minute
    
    # File limits
    MAX_FILES_PER_UPLOAD = 10
    MAX_WATERMARK_LENGTH = 50
    
    # Security settings
    ALLOWED_HOSTS = None  # Set to specific hosts in production
    SECURE_COOKIES = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Content security
    MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500MB
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}
    
    # Logging
    LOG_SECURITY_EVENTS = True
    LOG_RATE_LIMIT_VIOLATIONS = True

def log_security_event(event_type: str, client_ip: str, details: str = None):
    """Log security-related events"""
    if SecurityConfig.LOG_SECURITY_EVENTS:
        timestamp = datetime.now().isoformat()
        message = f"SECURITY [{timestamp}] {event_type} from {client_ip}"
        if details:
            message += f": {details}"
        logger.warning(message)

def setup_security_middleware(app):
    """Setup security middleware for Flask app"""
    
    # Add security headers to all responses
    app.after_request(add_security_headers)
    
    # Configure secure session cookies
    app.config.update(
        SESSION_COOKIE_SECURE=SecurityConfig.SESSION_COOKIE_SECURE,
        SESSION_COOKIE_HTTPONLY=SecurityConfig.SESSION_COOKIE_HTTPONLY,
        SESSION_COOKIE_SAMESITE=SecurityConfig.SESSION_COOKIE_SAMESITE,
    )
    
    # Add request size limits
    app.config['MAX_CONTENT_LENGTH'] = SecurityConfig.MAX_UPLOAD_SIZE
    
    # Log configuration
    logger.info("Security middleware configured:")
    logger.info(f"  - Rate limiting enabled")
    logger.info(f"  - Max upload size: {SecurityConfig.MAX_UPLOAD_SIZE // (1024*1024)}MB")
    logger.info(f"  - Security headers enabled")
    logger.info(f"  - Upload rate limit: {SecurityConfig.UPLOAD_RATE_LIMIT[0]}/{SecurityConfig.UPLOAD_RATE_LIMIT[1]}s")

# Decorator for common security validations
def secure_endpoint(f):
    """Decorator that adds common security validations to endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = get_client_ip()
        
        # Log all requests to sensitive endpoints
        if f.__name__ in ['upload_file', 'extract_watermark', 'validate_video']:
            log_security_event('SENSITIVE_REQUEST', client_ip, f"Endpoint: {f.__name__}")
        
        # Additional validations can be added here
        return f(*args, **kwargs)
    
    return decorated_function

# Input validation utilities
def validate_strength_parameter(strength_str: str) -> tuple[bool, float, str]:
    """
    Validate watermark strength parameter
    
    Args:
        strength_str: String representation of strength
        
    Returns:
        Tuple of (is_valid, strength_value, error_message)
    """
    try:
        strength = float(strength_str)
        if not (0.05 <= strength <= 0.3):
            return False, 0.0, "Strength must be between 0.05 and 0.3"
        return True, strength, ""
    except (ValueError, TypeError):
        return False, 0.0, "Invalid strength value"

def validate_watermark_text(text: str) -> tuple[bool, str, str]:
    """
    Validate watermark text input
    
    Args:
        text: Watermark text
        
    Returns:
        Tuple of (is_valid, sanitized_text, error_message)
    """
    if not text:
        return False, "", "Watermark text cannot be empty"
    
    sanitized = sanitize_input(text, SecurityConfig.MAX_WATERMARK_LENGTH)
    
    if len(sanitized) != len(text):
        return False, sanitized, "Watermark text contains invalid characters"
    
    if len(sanitized) > SecurityConfig.MAX_WATERMARK_LENGTH:
        return False, sanitized, f"Watermark text too long (max {SecurityConfig.MAX_WATERMARK_LENGTH} characters)"
    
    return True, sanitized, ""

# Content validation for advanced security
def validate_file_content(file_path: str, expected_types: set = None) -> tuple[bool, str]:
    """
    Validate file content using magic numbers
    
    Args:
        file_path: Path to file to validate
        expected_types: Set of expected MIME types
        
    Returns:
        Tuple of (is_valid, detected_type_or_error)
    """
    if expected_types is None:
        expected_types = {
            'video/mp4', 'video/avi', 'video/x-msvideo',
            'video/quicktime', 'video/x-matroska', 'video/x-ms-wmv',
            'video/x-flv', 'video/webm'
        }
    
    try:
        import magic
        
        # Check MIME type
        mime_type = magic.from_file(file_path, mime=True)
        
        if mime_type not in expected_types:
            return False, f"Invalid file type: {mime_type}"
        
        # Additional checks can be added here
        # For example, checking file headers, structure validation, etc.
        
        return True, mime_type
        
    except ImportError:
        logger.warning("python-magic not available, skipping content validation")
        return True, "unknown"
    except Exception as e:
        logger.error(f"Content validation error: {e}")
        return False, f"Content validation failed: {str(e)}"
