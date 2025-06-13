import os
import uuid
import threading
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

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', config.SECRET_KEY)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configuration
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
PROCESSED_FOLDER = os.getenv('PROCESSED_FOLDER', 'processed')
ALLOWED_EXTENSIONS = set(config.ALLOWED_EXTENSIONS)
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', config.MAX_FILE_SIZE_MB * 1024 * 1024))

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
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
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    print("🔧 Background worker started")
    while True:
        try:
            print("⏳ Waiting for tasks...")
            task = processing_queue.get()
            if task is None:
                break
            print(f"📋 Processing task: {task['id']}")
            
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
            success = processor.embed_watermark_in_video(
                input_path, output_path, watermark_text, strength, 
                watermarker, progress_callback
            )
            
            if success:
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
                processing_status[task_id] = {
                    'task_id': task_id,
                    'status': 'error',
                    'progress': 0,
                    'message': 'Processing failed. Please try again.'
                }
            
            socketio.emit('processing_update', processing_status[task_id], room=task_id)
            
            # Clean up input file
            if os.path.exists(input_path):
                os.remove(input_path)
                
        except Exception as e:
            if 'task_id' in locals():
                processing_status[task_id] = {
                    'task_id': task_id,
                    'status': 'error',
                    'progress': 0,
                    'message': f'Error: {str(e)}'
                }
                socketio.emit('processing_update', processing_status[task_id], room=task_id)
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
def upload_file():
    if 'files' not in request.files:
        return jsonify({'error': 'No files selected'}), 400
    
    files = request.files.getlist('files')
    watermark_text = request.form.get('watermark_text', '')
    strength = float(request.form.get('strength', config.DEFAULT_STRENGTH))
    
    if len(watermark_text) > config.MAX_WATERMARK_LENGTH:
        return jsonify({'error': f'Watermark text too long (max {config.MAX_WATERMARK_LENGTH} characters)'}), 400
    
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No files selected'}), 400
    
    uploaded_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            # Generate unique task ID
            task_id = str(uuid.uuid4())
            
            # Secure filename
            original_filename = secure_filename(file.filename)
            filename = f"{task_id}_{original_filename}"
            
            # Save uploaded file
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(input_path)
            
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
            processing_queue.put(task)
            print(f"📊 Queue size: {processing_queue.qsize()}")
            
            # Initialize status
            processing_status[task_id] = {
                'status': 'queued',
                'progress': 0,
                'message': 'Queued for processing...'
            }
            
            uploaded_files.append({
                'task_id': task_id,
                'filename': original_filename
            })
    
    return jsonify({
        'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
        'files': uploaded_files
    })

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
    import psutil
    import platform
    
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
    print(f"🎬 Starting {config.APP_NAME} v{config.VERSION}")
    print(f"📊 Server running on http://{config.HOST}:{config.PORT}")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📁 Processed folder: {PROCESSED_FOLDER}")
    print(f"📏 Max file size: {MAX_CONTENT_LENGTH // (1024*1024)}MB")
    print("🚀 Ready to process videos!")
    socketio.run(app, debug=config.DEBUG, host=config.HOST, port=config.PORT)
