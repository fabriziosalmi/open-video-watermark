import os
import uuid
import threading
import psutil
import platform
import logging
import magic
from queue import Queue
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
import json
from datetime import datetime
from dotenv import load_dotenv

from watermark.dct_watermark import DCTWatermark
from watermark.video_processor import VideoProcessor
import config
from security import (
    setup_security_middleware, rate_limit, secure_endpoint,
    validate_video_upload, validate_watermark_text, validate_strength_parameter
)

# Load environment variables
load_dotenv()

# Setup logging
def setup_logging():
    """Setup logging configuration"""
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler()
        ]
    )

setup_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# Setup security middleware
setup_security_middleware(app)

# Setup CORS origins
cors_origins = config.CORS_ORIGINS.split(',') if config.CORS_ORIGINS != '*' else "*"
socketio = SocketIO(app, cors_allowed_origins=cors_origins, async_mode='threading')

# Configuration
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
PROCESSED_FOLDER = os.getenv('PROCESSED_FOLDER', 'processed')
ALLOWED_EXTENSIONS = set(config.ALLOWED_EXTENSIONS)
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', config.MAX_FILE_SIZE_MB * 1024 * 1024))

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Processing queue and status tracking
processing_queue = Queue()
processing_status = {}
file_registry = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_magic(file_path):
    """Validate file using magic numbers (MIME type detection)"""
    try:
        mime = magic.from_file(file_path, mime=True)
        logger.info(f"Detected MIME type: {mime} for file: {file_path}")
        
        # Video MIME types
        allowed_video_mimes = [
            'video/mp4',
            'video/avi', 
            'video/x-msvideo',
            'video/quicktime',
            'video/x-matroska',
            'video/x-ms-wmv',
            'video/x-flv',
            'video/webm'
        ]
        
        return mime in allowed_video_mimes
    except ImportError:
        logger.warning("python-magic not available, falling back to extension-only validation")
        return True  # Fallback to extension validation only
    except Exception as e:
        logger.error(f"Error validating file magic: {e}")
        return False

def load_file_registry():
    """Load file registry from disk"""
    registry_file = os.path.join(PROCESSED_FOLDER, 'registry.json')
    if os.path.exists(registry_file):
        try:
            with open(registry_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_file_registry():
    """Save file registry to disk"""
    registry_file = os.path.join(PROCESSED_FOLDER, 'registry.json')
    with open(registry_file, 'w') as f:
        json.dump(file_registry, f, indent=2)

def process_video_worker():
    """Background worker for processing videos"""
    logger.info("🔧 Background worker started")
    while True:
        try:
            logger.debug("⏳ Waiting for tasks...")
            task = processing_queue.get()
            if task is None:
                break
            logger.info(f"📋 Processing task: {task['id']}")
            
            task_id = task['id']
            input_path = task['input_path']
            output_path = task['output_path']
            watermark_text = task['watermark_text']
            strength = task['strength']
            original_filename = task['original_filename']
            
            # Update status
            processing_status[task_id] = {
                'task_id': task_id,
                'status': 'processing',
                'progress': 0,
                'message': 'Initializing...'
            }
            socketio.emit('processing_update', processing_status[task_id], room=task_id)
            
            # Initialize watermarking
            watermarker = DCTWatermark()
            processor = VideoProcessor()
            
            def progress_callback(frame_num, total_frames, message="Processing"):
                progress = int((frame_num / total_frames) * 100)
                processing_status[task_id] = {
                    'task_id': task_id,
                    'status': 'processing',
                    'progress': progress,
                    'message': f'{message} frame {frame_num}/{total_frames}... {progress}%'
                }
                socketio.emit('processing_update', processing_status[task_id], room=task_id)
            
            # Process video
            logger.info(f"Starting video processing for task {task_id}: {original_filename}")
            success = processor.embed_watermark_in_video(
                input_path, output_path, watermark_text, strength, 
                watermarker, progress_callback
            )
            
            if success:
                logger.info(f"Video processing completed successfully for task {task_id}")
                # Update file registry
                file_info = {
                    'id': task_id,
                    'original_filename': original_filename,
                    'processed_filename': os.path.basename(output_path),
                    'watermark_text': watermark_text,
                    'strength': strength,
                    'processed_date': datetime.now().isoformat(),
                    'file_size': os.path.getsize(output_path)
                }
                file_registry[task_id] = file_info
                save_file_registry()
                
                processing_status[task_id] = {
                    'task_id': task_id,
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Processing completed successfully!'
                }
            else:
                logger.error(f"Video processing failed for task {task_id}")
                processing_status[task_id] = {
                    'task_id': task_id,
                    'status': 'error',
                    'progress': 0,
                    'message': 'Processing failed. Please try again.'
                }
            
            socketio.emit('processing_update', processing_status[task_id], room=task_id)
            
            # Clean up input file on success
            if os.path.exists(input_path):
                try:
                    os.remove(input_path)
                    logger.debug(f"Cleaned up input file: {input_path}")
                except OSError as e:
                    logger.warning(f"Could not remove input file {input_path}: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error processing task {task.get('id', 'unknown')}: {e}", exc_info=True)
            if 'task_id' in locals():
                processing_status[task_id] = {
                    'task_id': task_id,
                    'status': 'error',
                    'progress': 0,
                    'message': f'Processing failed: {str(e)}'
                }
                socketio.emit('processing_update', processing_status[task_id], room=task_id)
                
                # Clean up files on error
                for path in [input_path, output_path]:
                    if 'path' in locals() and os.path.exists(path):
                        try:
                            os.remove(path)
                            logger.debug(f"Cleaned up file on error: {path}")
                        except OSError:
                            pass
        finally:
            processing_queue.task_done()

# Start background worker
worker_thread = threading.Thread(target=process_video_worker, daemon=True)
worker_thread.start()

# Load existing file registry
file_registry = load_file_registry()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
@rate_limit(limit=10, window=60)  # 10 uploads per minute
@secure_endpoint
def upload_file():
    if 'files' not in request.files:
        return jsonify({'error': 'No files selected'}), 400
    
    files = request.files.getlist('files')
    watermark_text = request.form.get('watermark_text', '')
    
    # Validate watermark text
    if not watermark_text.strip():
        return jsonify({'error': 'Watermark text cannot be empty'}), 400
    
    if len(watermark_text) > config.MAX_WATERMARK_LENGTH:
        return jsonify({'error': f'Watermark text too long (max {config.MAX_WATERMARK_LENGTH} characters)'}), 400
    
    # Validate and parse strength
    try:
        strength = float(request.form.get('strength', config.DEFAULT_STRENGTH))
        if not (config.MIN_STRENGTH <= strength <= config.MAX_STRENGTH):
            return jsonify({'error': f'Strength must be between {config.MIN_STRENGTH} and {config.MAX_STRENGTH}'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid strength value'}), 400
    
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No files selected'}), 400
    
    uploaded_files = []
    errors = []
    
    for file in files:
        if file and file.filename:
            if not allowed_file(file.filename):
                errors.append(f'{file.filename}: File type not supported')
                continue
                
            try:
                # Generate unique task ID
                task_id = str(uuid.uuid4())
                
                # Secure filename
                original_filename = secure_filename(file.filename)
                if not original_filename:
                    errors.append(f'{file.filename}: Invalid filename')
                    continue
                    
                filename = f"{task_id}_{original_filename}"
                
                # Save uploaded file
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(input_path)
                
                # Validate file using magic numbers
                if not validate_file_magic(input_path):
                    os.remove(input_path)
                    errors.append(f'{original_filename}: Invalid video file format (magic number check failed)')
                    logger.warning(f"Magic number validation failed for file: {original_filename}")
                    continue
                
                # Validate video file with OpenCV
                processor = VideoProcessor()
                if not processor.validate_video_file(input_path):
                    os.remove(input_path)  # Clean up invalid file
                    errors.append(f'{original_filename}: Invalid or corrupted video file')
                    logger.warning(f"OpenCV validation failed for file: {original_filename}")
                    continue
                
                # Prepare output path
                name, ext = os.path.splitext(original_filename)
                output_filename = f"{task_id}_watermarked_{name}{ext}"
                output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
                
                # Add to processing queue
                task = {
                    'id': task_id,
                    'input_path': input_path,
                    'output_path': output_path,
                    'watermark_text': watermark_text,
                    'strength': strength,
                    'original_filename': original_filename
                }
                
                print(f"🔄 Adding task to queue: {task_id}")
                logger.info(f"Adding task to processing queue: {task_id} - {original_filename}")
                processing_queue.put(task)
                print(f"📊 Queue size: {processing_queue.qsize()}")
                logger.debug(f"Current queue size: {processing_queue.qsize()}")
                
                # Initialize status
                processing_status[task_id] = {
                    'task_id': task_id,
                    'status': 'queued',
                    'progress': 0,
                    'message': 'Queued for processing...'
                }
                
                uploaded_files.append({
                    'task_id': task_id,
                    'filename': original_filename
                })
                
            except Exception as e:
                logger.error(f"Error uploading file {file.filename}: {e}", exc_info=True)
                errors.append(f'{file.filename}: Upload failed - {str(e)}')
                # Clean up any partially created files
                if 'input_path' in locals() and os.path.exists(input_path):
                    os.remove(input_path)
    
    response = {
        'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
        'files': uploaded_files
    }
    
    if errors:
        response['errors'] = errors
        response['message'] += f' ({len(errors)} failed)'
    
    status_code = 200 if uploaded_files else 400
    return jsonify(response), status_code

@app.route('/status/<task_id>')
def get_status(task_id):
    status = processing_status.get(task_id, {'status': 'unknown', 'progress': 0, 'message': 'Task not found'})
    return jsonify(status)

@app.route('/files')
def list_files():
    files = []
    for file_id, file_info in file_registry.items():
        files.append({
            'id': file_id,
            'original_filename': file_info['original_filename'],
            'processed_date': file_info['processed_date'],
            'file_size': file_info['file_size']
        })
    
    # Sort by processed date (newest first)
    files.sort(key=lambda x: x['processed_date'], reverse=True)
    return jsonify(files)

@app.route('/download/<file_id>')
def download_file(file_id):
    if file_id not in file_registry:
        return jsonify({'error': 'File not found'}), 404
    
    file_info = file_registry[file_id]
    file_path = os.path.join(app.config['PROCESSED_FOLDER'], file_info['processed_filename'])
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found on disk'}), 404
    
    return send_file(file_path, as_attachment=True, download_name=f"watermarked_{file_info['original_filename']}")

@app.route('/delete/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    if file_id not in file_registry:
        return jsonify({'error': 'File not found'}), 404
    
    file_info = file_registry[file_id]
    file_path = os.path.join(app.config['PROCESSED_FOLDER'], file_info['processed_filename'])
    
    # Remove file from disk
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Remove from registry
    del file_registry[file_id]
    save_file_registry()
    
    return jsonify({'message': 'File deleted successfully'})

@app.route('/queue/status')
def get_queue_status():
    """Get current processing queue status"""
    return jsonify({
        'queue_size': processing_queue.qsize(),
        'active_tasks': len([s for s in processing_status.values() if s['status'] == 'processing']),
        'completed_tasks': len([s for s in processing_status.values() if s['status'] == 'completed']),
        'failed_tasks': len([s for s in processing_status.values() if s['status'] == 'error'])
    })

@app.route('/system/info')
def get_system_info():
    """Get system information for monitoring"""
    
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return jsonify({
            'system': {
                'platform': platform.system(),
                'cpu_cores': psutil.cpu_count(),
                'cpu_usage': cpu_percent,
                'memory_total': memory.total,
                'memory_available': memory.available,
                'memory_percent': memory.percent,
                'disk_total': disk.total,
                'disk_free': disk.free,
                'disk_percent': (disk.used / disk.total) * 100
            },
            'app': {
                'version': config.VERSION,
                'debug': config.DEBUG,
                'max_file_size': MAX_CONTENT_LENGTH,
                'allowed_extensions': list(ALLOWED_EXTENSIONS)
            }
        })
    except ImportError:
        return jsonify({
            'system': {'error': 'psutil not available'},
            'app': {
                'version': config.VERSION,
                'debug': config.DEBUG,
                'max_file_size': MAX_CONTENT_LENGTH,
                'allowed_extensions': list(ALLOWED_EXTENSIONS)
            }
        })

@app.route('/health')
def health_check():
    """Health check endpoint for Docker and load balancers"""
    return jsonify({
        'status': 'healthy',
        'service': 'open-video-watermark',
        'version': config.VERSION,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/extract', methods=['POST'])
@rate_limit(limit=5, window=60)  # 5 extractions per minute
@secure_endpoint
def extract_watermark():
    """Extract watermark from uploaded video"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    watermark_length = int(request.form.get('watermark_length', 20))
    
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not supported'}), 400
    
    try:
        # Generate unique filename
        extract_id = str(uuid.uuid4())
        filename = f"{extract_id}_{secure_filename(file.filename)}"
        
        # Save uploaded file temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        # Validate video file
        processor = VideoProcessor()
        if not processor.validate_video_file(temp_path):
            os.remove(temp_path)
            return jsonify({'error': 'Invalid video file'}), 400
        
        # Extract watermark
        watermarker = DCTWatermark()
        extracted_text = processor.extract_watermark_from_video(
            temp_path, watermark_length, watermarker
        )
        
        # Clean up temporary file
        os.remove(temp_path)
        
        if extracted_text:
            return jsonify({
                'success': True,
                'extracted_watermark': extracted_text,
                'confidence': 'medium'  # Could implement actual confidence scoring
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No watermark detected or extraction failed'
            })
    
    except Exception as e:
        logger.error(f"Error extracting watermark: {e}", exc_info=True)
        # Clean up on error
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500

@app.route('/validate', methods=['POST'])
@rate_limit(limit=20, window=60)  # 20 validations per minute
@secure_endpoint
def validate_video():
    """Comprehensive video validation endpoint"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Save file temporarily for validation
        temp_id = str(uuid.uuid4())
        filename = f"validate_{temp_id}_{secure_filename(file.filename)}"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        # Perform comprehensive validation
        processor = VideoProcessor()
        validation_result = processor.validate_video_comprehensive(temp_path)
        
        # Clean up temporary file
        os.remove(temp_path)
        
        return jsonify(validation_result)
    
    except Exception as e:
        logger.error(f"Error validating video: {e}", exc_info=True)
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

@app.route('/estimate-time', methods=['POST'])
@rate_limit(limit=30, window=60)  # 30 estimates per minute
def estimate_processing_time():
    """Estimate processing time for video watermarking"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    watermark_text = request.form.get('watermark_text', 'Sample')
    
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Save file temporarily for analysis
        temp_id = str(uuid.uuid4())
        filename = f"estimate_{temp_id}_{secure_filename(file.filename)}"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        # Get processing time estimate
        processor = VideoProcessor()
        estimate = processor.estimate_processing_time(temp_path, watermark_text)
        
        # Get video info for additional context
        video_info = processor.get_video_info(temp_path)
        
        # Clean up temporary file
        os.remove(temp_path)
        
        return jsonify({
            'estimate': estimate,
            'video_info': video_info
        })
    
    except Exception as e:
        logger.error(f"Error estimating processing time: {e}", exc_info=True)
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'error': f'Estimation failed: {str(e)}'}), 500

@app.route('/batch-status')
def get_batch_status():
    """Get status of all batch processing tasks"""
    try:
        batch_stats = {
            'total_tasks': len(processing_status),
            'queued': len([s for s in processing_status.values() if s['status'] == 'queued']),
            'processing': len([s for s in processing_status.values() if s['status'] == 'processing']),
            'completed': len([s for s in processing_status.values() if s['status'] == 'completed']),
            'failed': len([s for s in processing_status.values() if s['status'] == 'error']),
            'queue_size': processing_queue.qsize(),
            'tasks': list(processing_status.values())[:10]  # Return latest 10 tasks
        }
        
        return jsonify(batch_stats)
    
    except Exception as e:
        logger.error(f"Error getting batch status: {e}")
        return jsonify({'error': 'Failed to get batch status'}), 500

@app.route('/metrics')
@rate_limit(limit=60, window=60)  # Standard rate limit for metrics
def get_metrics():
    """Get application metrics for monitoring"""
    try:
        # Processing metrics
        processing_metrics = {
            'total_files_processed': len(file_registry),
            'active_processes': len([s for s in processing_status.values() if s['status'] == 'processing']),
            'queue_length': processing_queue.qsize(),
            'success_rate': 0
        }
        
        # Calculate success rate
        if processing_status:
            successful = len([s for s in processing_status.values() if s['status'] == 'completed'])
            total = len(processing_status)
            processing_metrics['success_rate'] = round((successful / total) * 100, 2)
        
        # Storage metrics
        processed_files = list(file_registry.values())
        total_size = sum(f.get('file_size', 0) for f in processed_files)
        
        storage_metrics = {
            'total_processed_files': len(processed_files),
            'total_storage_mb': round(total_size / (1024 * 1024), 2),
            'average_file_size_mb': round((total_size / len(processed_files)) / (1024 * 1024), 2) if processed_files else 0
        }
        
        # System metrics (if psutil available)
        system_metrics = {}
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            system_metrics = {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2)
            }
        except:
            system_metrics = {'error': 'psutil not available'}
        
        return jsonify({
            'processing': processing_metrics,
            'storage': storage_metrics,
            'system': system_metrics,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'error': 'Failed to get metrics'}), 500

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_task')
def handle_join_task(data):
    task_id = data['task_id']
    join_room(task_id)
    
    # Send current status if available
    if task_id in processing_status:
        emit('processing_update', processing_status[task_id])

if __name__ == '__main__':
    logger.info(f"🎬 Starting {config.APP_NAME} v{config.VERSION}")
    logger.info(f"📊 Server running on http://{config.HOST}:{config.PORT}")
    logger.info(f"📁 Upload folder: {UPLOAD_FOLDER}")
    logger.info(f"📁 Processed folder: {PROCESSED_FOLDER}")
    logger.info(f"📏 Max file size: {MAX_CONTENT_LENGTH // (1024*1024)}MB")
    logger.info(f"🔒 CORS origins: {cors_origins}")
    logger.info(f"📝 Log level: {config.LOG_LEVEL}")
    logger.info("🚀 Ready to process videos!")
    
    print(f"🎬 Starting {config.APP_NAME} v{config.VERSION}")
    print(f"📊 Server running on http://{config.HOST}:{config.PORT}")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📁 Processed folder: {PROCESSED_FOLDER}")
    print(f"📏 Max file size: {MAX_CONTENT_LENGTH // (1024*1024)}MB")
    print("🚀 Ready to process videos!")
    socketio.run(app, debug=config.DEBUG, host=config.HOST, port=config.PORT)
