# Open Video Watermark API Documentation

This document provides comprehensive documentation for the Open Video Watermark REST API endpoints.

## Base URL

```
http://localhost:8000  # Development
https://your-domain.com  # Production
```

## Authentication

Currently, no authentication is required. In production, consider implementing API keys or OAuth2.

## Content Types

- Request: `multipart/form-data` for file uploads, `application/json` for data
- Response: `application/json`

---

## Endpoints

### Health & System Information

#### GET /health
Health check endpoint for monitoring and load balancers.

**Response:**
```json
{
  "status": "healthy",
  "service": "open-video-watermark", 
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /system/info
Get detailed system information and configuration.

**Response:**
```json
{
  "system": {
    "platform": "Darwin",
    "cpu_cores": 8,
    "cpu_usage": 15.2,
    "memory_total": 17179869184,
    "memory_available": 8589934592,
    "memory_percent": 50.0,
    "disk_total": 1000000000000,
    "disk_free": 500000000000,
    "disk_percent": 50.0
  },
  "app": {
    "version": "1.0.0",
    "debug": false,
    "max_file_size": 524288000,
    "allowed_extensions": ["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm"]
  }
}
```

#### GET /metrics
Get application performance metrics.

**Response:**
```json
{
  "processing": {
    "total_files_processed": 150,
    "active_processes": 2,
    "queue_length": 3,
    "success_rate": 95.5
  },
  "storage": {
    "total_processed_files": 150,
    "total_storage_mb": 1024.5,
    "average_file_size_mb": 6.8
  },
  "system": {
    "cpu_usage": 25.0,
    "memory_usage": 60.0,
    "memory_available_gb": 8.5
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Video Processing

#### POST /upload
Upload videos for watermarking processing.

**Parameters:**
- `files` (file[], required): Video files to process
- `watermark_text` (string, required): Text to embed (max 50 chars)
- `strength` (float, optional): Embedding strength 0.05-0.3 (default: 0.1)

**Request:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "files=@video1.mp4" \
  -F "files=@video2.mp4" \
  -F "watermark_text=My Watermark" \
  -F "strength=0.15"
```

**Response:**
```json
{
  "message": "Successfully uploaded 2 file(s)",
  "files": [
    {
      "task_id": "123e4567-e89b-12d3-a456-426614174000",
      "filename": "video1.mp4"
    },
    {
      "task_id": "123e4567-e89b-12d3-a456-426614174001", 
      "filename": "video2.mp4"
    }
  ],
  "errors": []
}
```

**Error Response:**
```json
{
  "error": "Watermark text cannot be empty",
  "errors": [
    "video3.avi: File type not supported",
    "video4.mp4: Invalid or corrupted video file"
  ]
}
```

#### GET /status/{task_id}
Get processing status for a specific task.

**Response:**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing", // "queued", "processing", "completed", "error"
  "progress": 65,
  "message": "Processing frame 650/1000... 65%"
}
```

#### POST /extract
Extract watermark from an uploaded video file.

**Parameters:**
- `file` (file, required): Video file to analyze
- `watermark_length` (int, optional): Expected watermark length (default: 20)

**Request:**
```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@watermarked_video.mp4" \
  -F "watermark_length=15"
```

**Response:**
```json
{
  "success": true,
  "extracted_watermark": "My Watermark",
  "confidence": "medium"
}
```

**No Watermark Found:**
```json
{
  "success": false,
  "message": "No watermark detected or extraction failed"
}
```

#### POST /validate
Perform comprehensive video file validation.

**Parameters:**
- `file` (file, required): Video file to validate

**Response:**
```json
{
  "valid": true,
  "file_exists": true,
  "file_size": 1048576,
  "readable": true,
  "has_video_stream": true,
  "has_audio_stream": false,
  "duration": 30.5,
  "frame_count": 915,
  "fps": 30.0,
  "resolution": [1920, 1080],
  "codec": 875967048,
  "errors": [],
  "warnings": ["Video duration is very long"]
}
```

#### POST /estimate-time
Estimate processing time for video watermarking.

**Parameters:**
- `file` (file, required): Video file to analyze
- `watermark_text` (string, optional): Watermark text for estimation

**Response:**
```json
{
  "estimate": {
    "estimated_seconds": 45.2,
    "estimated_minutes": 0.8,
    "confidence": 0.7,
    "factors": {
      "resolution_factor": 1.5,
      "watermark_factor": 0.8,
      "adjusted_rate": 20.3
    }
  },
  "video_info": {
    "frame_count": 915,
    "fps": 30.0,
    "width": 1920,
    "height": 1080,
    "codec": 875967048
  }
}
```

---

### File Management

#### GET /files
List all processed video files.

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "original_filename": "my_video.mp4",
    "processed_date": "2024-01-15T10:30:00Z",
    "file_size": 15728640
  }
]
```

#### GET /download/{file_id}
Download a processed video file.

**Response:** Binary video file with headers:
- `Content-Disposition: attachment; filename="watermarked_my_video.mp4"`
- `Content-Type: video/mp4`

#### DELETE /delete/{file_id}
Delete a processed video file.

**Response:**
```json
{
  "message": "File deleted successfully"
}
```

**Error Response:**
```json
{
  "error": "File not found"
}
```

---

### Queue & Batch Management

#### GET /queue/status
Get current processing queue status.

**Response:**
```json
{
  "queue_size": 3,
  "active_tasks": 2,
  "completed_tasks": 148,
  "failed_tasks": 2
}
```

#### GET /batch-status
Get detailed status of all batch processing tasks.

**Response:**
```json
{
  "total_tasks": 155,
  "queued": 3,
  "processing": 2,
  "completed": 148,
  "failed": 2,
  "queue_size": 3,
  "tasks": [
    {
      "task_id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "processing",
      "progress": 65,
      "message": "Processing frame 650/1000... 65%"
    }
  ]
}
```

---

## WebSocket Events

The application supports real-time updates via WebSocket connections.

### Connection
```javascript
const socket = io('http://localhost:8000');
```

### Events

#### join_task
Join a room to receive updates for a specific task.

**Emit:**
```javascript
socket.emit('join_task', {
  task_id: '123e4567-e89b-12d3-a456-426614174000'
});
```

#### processing_update
Receive real-time processing updates.

**Listen:**
```javascript
socket.on('processing_update', (data) => {
  console.log(`Task ${data.task_id}: ${data.progress}% - ${data.message}`);
});
```

**Event Data:**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "progress": 75,
  "message": "Processing frame 750/1000... 75%"
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters or missing data |
| 404 | Not Found - Resource does not exist |
| 413 | Payload Too Large - File size exceeds limit |
| 415 | Unsupported Media Type - Invalid file format |
| 500 | Internal Server Error - Server-side processing error |

## Error Response Format

```json
{
  "error": "Description of the error",
  "details": "Additional error details if available"
}
```

---

## Rate Limits

Currently no rate limiting is implemented. For production use, consider implementing:
- File upload limits: 10 files per minute per IP
- Processing queue limits: 5 concurrent tasks per user
- API request limits: 100 requests per minute per IP

---

## File Size Limits

- Maximum file size: 500MB (configurable via `MAX_CONTENT_LENGTH`)
- Supported formats: MP4, AVI, MOV, MKV, WMV, FLV, WebM
- Maximum watermark text length: 50 characters

---

## WebSocket Integration Example

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
</head>
<body>
    <script>
        const socket = io('http://localhost:8000');
        
        // Connect to task updates
        socket.emit('join_task', {
            task_id: 'your-task-id'
        });
        
        // Listen for progress updates
        socket.on('processing_update', (data) => {
            const progressBar = document.getElementById('progress');
            progressBar.style.width = data.progress + '%';
            progressBar.textContent = data.message;
            
            if (data.status === 'completed') {
                console.log('Processing completed!');
                // Redirect to download or refresh file list
            }
        });
    </script>
</body>
</html>
```

---

## Python Client Example

```python
import requests
import json

class VideoWatermarkClient:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
    
    def upload_videos(self, files, watermark_text, strength=0.1):
        """Upload videos for processing"""
        url = f"{self.base_url}/upload"
        
        data = {
            'watermark_text': watermark_text,
            'strength': strength
        }
        
        files_data = []
        for file_path in files:
            files_data.append(('files', open(file_path, 'rb')))
        
        try:
            response = requests.post(url, data=data, files=files_data)
            return response.json()
        finally:
            # Close file handles
            for _, file_handle in files_data:
                file_handle.close()
    
    def get_status(self, task_id):
        """Get processing status"""
        url = f"{self.base_url}/status/{task_id}"
        response = requests.get(url)
        return response.json()
    
    def extract_watermark(self, video_path, watermark_length=20):
        """Extract watermark from video"""
        url = f"{self.base_url}/extract"
        
        with open(video_path, 'rb') as f:
            files = {'file': f}
            data = {'watermark_length': watermark_length}
            response = requests.post(url, files=files, data=data)
            return response.json()
    
    def download_file(self, file_id, output_path):
        """Download processed video"""
        url = f"{self.base_url}/download/{file_id}"
        response = requests.get(url)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        return False

# Usage example
client = VideoWatermarkClient()

# Upload videos
result = client.upload_videos(
    files=['video1.mp4', 'video2.mp4'],
    watermark_text='My Copyright',
    strength=0.15
)

# Monitor progress
for file_info in result['files']:
    task_id = file_info['task_id']
    
    while True:
        status = client.get_status(task_id)
        print(f"Status: {status['status']} - {status['progress']}%")
        
        if status['status'] in ['completed', 'error']:
            break
        
        time.sleep(2)
```

This API documentation provides comprehensive coverage of all endpoints and features available in the Open Video Watermark application.
