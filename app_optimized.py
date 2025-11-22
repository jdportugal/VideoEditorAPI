from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import threading
import time
import gc
import psutil
import logging
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime
import re

# Import optimized services
from app.services.optimized_video_service import OptimizedVideoService
from app.services.optimized_subtitle_service import OptimizedSubtitleService
from app.services.job_manager import JobManager
from app.utils.download_utils import download_file

# Configure logging for performance monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize optimized services
video_service = OptimizedVideoService()
subtitle_service = OptimizedSubtitleService()
job_manager = JobManager()

# Resource monitoring configuration
MEMORY_WARNING_THRESHOLD = 0.85  # 85%
MEMORY_CRITICAL_THRESHOLD = 0.95  # 95%
CPU_WARNING_THRESHOLD = 0.90      # 90%

# Adaptive worker configuration based on system resources
def get_optimal_worker_count():
    """Determine optimal worker count based on system resources."""
    memory_gb = psutil.virtual_memory().total / (1024**3)
    cpu_count = psutil.cpu_count()
    
    # Conservative worker allocation for resource-constrained systems
    if memory_gb <= 4:  # 4GB or less
        return 1  # Single worker to avoid memory pressure
    elif memory_gb <= 8:  # 4-8GB
        return min(2, cpu_count)
    else:  # 8GB+
        return min(4, cpu_count)

# Thread pool for async processing with adaptive sizing
optimal_workers = get_optimal_worker_count()
logger.info(f"Initializing with {optimal_workers} workers for {psutil.virtual_memory().total/(1024**3):.1f}GB system")
executor = ThreadPoolExecutor(max_workers=optimal_workers)

# Resource monitoring thread
monitoring_active = True
resource_stats = {
    "peak_memory": 0,
    "average_cpu": 0,
    "job_count": 0,
    "warnings": []
}

def monitor_system_resources():
    """Background thread to monitor system resources."""
    global monitoring_active, resource_stats
    
    cpu_samples = []
    
    while monitoring_active:
        try:
            # Memory monitoring
            memory = psutil.virtual_memory()
            memory_percent = memory.percent / 100.0
            
            # CPU monitoring
            cpu_percent = psutil.cpu_percent(interval=1) / 100.0
            cpu_samples.append(cpu_percent)
            if len(cpu_samples) > 60:  # Keep last 60 samples (1 minute)
                cpu_samples.pop(0)
            
            # Update stats
            resource_stats["peak_memory"] = max(resource_stats["peak_memory"], memory_percent)
            resource_stats["average_cpu"] = sum(cpu_samples) / len(cpu_samples)
            
            # Check for warning conditions
            if memory_percent > MEMORY_CRITICAL_THRESHOLD:
                warning = f"CRITICAL: Memory usage {memory_percent:.1%} - triggering cleanup"
                logger.critical(warning)
                resource_stats["warnings"].append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "memory_critical",
                    "value": memory_percent,
                    "message": warning
                })
                # Trigger emergency cleanup
                emergency_cleanup()
                
            elif memory_percent > MEMORY_WARNING_THRESHOLD:
                warning = f"WARNING: High memory usage {memory_percent:.1%}"
                logger.warning(warning)
                resource_stats["warnings"].append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "memory_warning", 
                    "value": memory_percent,
                    "message": warning
                })
            
            if cpu_percent > CPU_WARNING_THRESHOLD:
                warning = f"WARNING: High CPU usage {cpu_percent:.1%}"
                logger.warning(warning)
                resource_stats["warnings"].append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "cpu_warning",
                    "value": cpu_percent,
                    "message": warning
                })
            
            # Keep only last 100 warnings
            if len(resource_stats["warnings"]) > 100:
                resource_stats["warnings"] = resource_stats["warnings"][-100:]
            
        except Exception as e:
            logger.error(f"Resource monitoring error: {e}")
        
        time.sleep(5)  # Check every 5 seconds

def emergency_cleanup():
    """Emergency memory cleanup when critical threshold is reached."""
    logger.info("Performing emergency memory cleanup...")
    
    # Force garbage collection
    gc.collect()
    
    # Unload Whisper model if loaded
    try:
        subtitle_service.unload_model()
    except Exception as e:
        logger.error(f"Error unloading model: {e}")
    
    # Clean up video service memory
    try:
        video_service._cleanup_memory()
    except Exception as e:
        logger.error(f"Error cleaning video service: {e}")

# Start resource monitoring
monitor_thread = threading.Thread(target=monitor_system_resources, daemon=True)
monitor_thread.start()

def parse_time_to_seconds(time_input):
    """Convert time format to seconds with enhanced parsing."""
    if isinstance(time_input, (int, float)):
        return float(time_input)
    
    if isinstance(time_input, str):
        try:
            return float(time_input)
        except ValueError:
            pass
        
        time_pattern = r'(\d{1,2}):(\d{1,2}):(\d{1,2})[,.](\d{3})'
        match = re.match(time_pattern, time_input.strip())
        
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            milliseconds = int(match.group(4))
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            return total_seconds
        
        raise ValueError(f"Invalid time format: {time_input}")
    
    raise ValueError(f"Unsupported time type: {type(time_input)}")

@app.route('/performance-mode', methods=['POST'])
def set_performance_mode():
    """Switch between optimized and performance modes."""
    try:
        data = request.json
        mode = data.get('mode', 'optimized').lower()
        
        if mode not in ['optimized', 'performance']:
            return jsonify({"error": "Invalid mode. Use 'optimized' or 'performance'"}), 400
        
        response = {
            "status": "success",
            "current_mode": "optimized",  # This app is always optimized
            "requested_mode": mode,
            "message": f"Current instance runs in OPTIMIZED mode. For {mode.upper()} mode, use docker-compose.{mode}.yml"
        }
        
        if mode == 'performance':
            response["instructions"] = {
                "step_1": "docker-compose down",
                "step_2": "docker-compose -f docker-compose.performance.yml up -d --build",
                "note": "Performance mode uses all available system resources"
            }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check with resource information."""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent()
    
    # Get model info if available
    model_info = {}
    try:
        model_info = subtitle_service.get_model_info()
    except Exception:
        model_info = {"status": "no_model_loaded"}
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "resources": {
            "memory_usage_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
            "cpu_usage_percent": cpu_percent,
            "workers": optimal_workers
        },
        "whisper_model": model_info,
        "performance_stats": resource_stats
    }
    
    # Add warning if resources are constrained
    if memory.percent > MEMORY_WARNING_THRESHOLD * 100:
        health_data["warnings"] = ["High memory usage detected"]
    
    return jsonify(health_data)

@app.route('/add-subtitles', methods=['POST'])
def add_subtitles():
    """Optimized subtitle addition with progress tracking."""
    try:
        data = request.get_json()
        
        logger.info("Processing optimized subtitle request")
        
        if not data or 'url' not in data:
            return jsonify({"error": "Missing required field: url"}), 400
        
        # Check system resources before accepting job
        memory = psutil.virtual_memory()
        if memory.percent > MEMORY_CRITICAL_THRESHOLD * 100:
            return jsonify({
                "error": "System memory critically low. Please try again later.",
                "memory_usage": f"{memory.percent:.1f}%"
            }), 503
        
        job_id = str(uuid.uuid4())
        
        # Optimized default settings for low-resource systems
        default_settings = {
            "language": "en",
            "return_subtitles_file": True,
            "word_level_mode": "karaoke",
            "settings": {
                "font-size": 80,  # Smaller font for memory efficiency
                "font-family": "DejaVu-Sans-Bold",  # Simple font
                "line-color": "#FFF4E9", 
                "outline-width": 5,  # Reduced outline for performance
                "normal-color": "#FFFFFF"
            }
        }
        
        # Merge with provided settings
        settings = {**default_settings, **data}
        
        if "settings" in data:
            settings["settings"] = {**default_settings["settings"], **data["settings"]}
        
        # Create job with enhanced tracking
        job_manager.create_job(job_id, "add_subtitles", "pending", settings)
        
        # Update resource stats
        resource_stats["job_count"] += 1
        
        # Submit with progress tracking
        future = executor.submit(process_subtitle_job_optimized, job_id, settings)
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "Optimized subtitle processing started",
            "estimated_time": "Processing time optimized for your system resources"
        })
        
    except Exception as e:
        logger.error(f"Error in add_subtitles: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/split-video', methods=['POST'])
def split_video():
    """Optimized video splitting."""
    try:
        data = request.get_json()
        
        has_url = 'url' in data
        has_job_id = 'job_id' in data
        
        if not has_url and not has_job_id:
            return jsonify({"error": "Must provide either 'url' or 'job_id'"}), 400
        
        if has_url and has_job_id:
            return jsonify({"error": "Provide either 'url' or 'job_id', not both"}), 400
        
        # Validate time fields
        required_time_fields = ['start_time', 'end_time'] 
        for field in required_time_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Parse and validate time formats
        try:
            start_seconds = parse_time_to_seconds(data['start_time'])
            end_seconds = parse_time_to_seconds(data['end_time'])
            
            if start_seconds >= end_seconds:
                return jsonify({"error": "Start time must be less than end time"}), 400
            
            if start_seconds < 0:
                return jsonify({"error": "Start time cannot be negative"}), 400
                
        except ValueError as e:
            return jsonify({"error": f"Invalid time format: {str(e)}"}), 400
        
        # Check system resources
        memory = psutil.virtual_memory()
        if memory.percent > MEMORY_WARNING_THRESHOLD * 100:
            logger.warning(f"Processing video split with high memory usage: {memory.percent:.1f}%")
        
        job_id = str(uuid.uuid4())
        
        processed_data = {
            **data,
            'start_time': start_seconds,
            'end_time': end_seconds
        }
        
        job_manager.create_job(job_id, "split_video", "pending", processed_data)
        executor.submit(process_split_job_optimized, job_id, processed_data)
        
        resource_stats["job_count"] += 1
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "Optimized video splitting started"
        })
        
    except Exception as e:
        logger.error(f"Error in split_video: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/join-videos', methods=['POST'])
def join_videos():
    """Optimized video joining."""
    try:
        data = request.get_json()
        
        if not data or 'urls' not in data or not isinstance(data['urls'], list):
            return jsonify({"error": "Missing required field: urls (must be an array)"}), 400
        
        if len(data['urls']) < 2:
            return jsonify({"error": "At least 2 video URLs are required"}), 400
        
        # For many videos, warn about resource usage
        if len(data['urls']) > 5:
            memory = psutil.virtual_memory()
            if memory.percent > MEMORY_WARNING_THRESHOLD * 100:
                return jsonify({
                    "error": "Too many videos for current system resources. Try with fewer videos.",
                    "max_recommended": 3
                }), 400
        
        job_id = str(uuid.uuid4())
        
        job_manager.create_job(job_id, "join_videos", "pending", data)
        executor.submit(process_join_job_optimized, job_id, data)
        
        resource_stats["job_count"] += 1
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "Optimized video joining started"
        })
        
    except Exception as e:
        logger.error(f"Error in join_videos: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/add-music', methods=['POST'])
def add_music():
    """Optimized music addition."""
    try:
        data = request.get_json()
        
        required_fields = ['video_url', 'music_url']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        job_id = str(uuid.uuid4())
        
        settings = {
            "volume": data.get('volume', 0.5),
            "fade_in": data.get('fade_in', 0),
            "fade_out": data.get('fade_out', 0),
            "loop_music": data.get('loop_music', False)
        }
        
        job_data = {**data, "settings": settings}
        
        job_manager.create_job(job_id, "add_music", "pending", job_data)
        executor.submit(process_music_job_optimized, job_id, job_data)
        
        resource_stats["job_count"] += 1
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "Optimized music addition started"
        })
        
    except Exception as e:
        logger.error(f"Error in add_music: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/job-status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Enhanced job status with resource information."""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        simplified_job = {
            "job_id": job.get("job_id"),
            "status": job.get("status"),
            "progress": job.get("progress", 0),
            "error": job.get("error"),
            "processing_info": job.get("processing_info", {})  # Enhanced info
        }
        
        # Add download URLs if completed
        if job.get("status") == "completed":
            if job.get("output_path"):
                simplified_job["video_download_url"] = f"/download/{job_id}"
            if job.get("subtitle_path"):
                simplified_job["subtitle_download_url"] = f"/download-subtitles/{job_id}"
        
        # Add current system status for active jobs
        if job.get("status") in ["pending", "processing"]:
            memory = psutil.virtual_memory()
            simplified_job["system_status"] = {
                "memory_usage_percent": memory.percent,
                "estimated_completion": "Processing optimized for your system"
            }
        
        return jsonify(simplified_job)
        
    except Exception as e:
        logger.error(f"Error in get_job_status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/system-status', methods=['GET'])
def get_system_status():
    """Get detailed system status and performance metrics."""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent()
    
    return jsonify({
        "memory": {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "usage_percent": memory.percent,
            "status": "critical" if memory.percent > 95 else "warning" if memory.percent > 85 else "normal"
        },
        "cpu": {
            "usage_percent": cpu_percent,
            "core_count": psutil.cpu_count(),
            "status": "warning" if cpu_percent > 90 else "normal"
        },
        "workers": {
            "current": optimal_workers,
            "active": len([t for t in threading.enumerate() if t.name.startswith("ThreadPoolExecutor")]),
            "recommended": get_optimal_worker_count()
        },
        "performance_stats": resource_stats,
        "whisper_model": subtitle_service.get_model_info()
    })

# Optimized processing functions

def process_subtitle_job_optimized(job_id, settings):
    """Optimized subtitle processing with progress tracking."""
    video_path = None
    start_time = time.time()
    
    try:
        # Update job with processing info
        job_manager.update_job_status(job_id, "processing", 10)
        
        # Log system state at start
        memory_before = psutil.virtual_memory()
        logger.info(f"Starting subtitle job {job_id} with {memory_before.percent:.1f}% memory usage")
        
        # Download video
        video_url = settings['url']
        video_path = download_file(video_url, 'temp', f"{job_id}_input.mp4")
        job_manager.update_job_status(job_id, "processing", 20)
        
        # Create progress callback function
        def update_progress(progress, message):
            job_manager.update_job_status(job_id, "processing", progress, message)
        
        # Generate subtitles with optimized service
        subtitle_data = subtitle_service.generate_subtitles(
            video_path, 
            settings['language'],
            settings.get('timing_offset', 0.0),
            progress_callback=update_progress
        )
        job_manager.update_job_status(job_id, "processing", 60, "✅ Subtitle generation completed")
        
        # Analyze timing
        timing_analysis = subtitle_service.analyze_timing_gaps(subtitle_data)
        
        # Create video with subtitles using optimized service
        output_path = f"temp/{job_id}_output.mp4"
        word_mode = settings.get('word_level_mode', 'off')
        
        logger.info(f"Processing with {word_mode} mode using optimized video service")
        
        video_service.add_subtitles_to_video(
            video_path,
            subtitle_data,
            output_path,
            {**settings['settings'], **settings.get('word_level_settings', {})},
            word_mode
        )
        job_manager.update_job_status(job_id, "processing", 90)
        
        # Verify output
        if not os.path.exists(output_path):
            raise Exception(f"Video processing failed - output file not created: {output_path}")
        
        # Handle subtitle file
        result = {"output_path": output_path}
        if settings.get('return_subtitles_file', False):
            subtitle_path = f"temp/{job_id}_subtitles.srt"
            subtitle_service.save_subtitle_file(subtitle_data, subtitle_path)
            result["subtitle_path"] = subtitle_path
        
        # Add processing info
        processing_time = time.time() - start_time
        memory_after = psutil.virtual_memory()
        
        result["processing_info"] = {
            "processing_time_seconds": processing_time,
            "memory_usage_before": f"{memory_before.percent:.1f}%",
            "memory_usage_after": f"{memory_after.percent:.1f}%",
            "model_used": subtitle_service.current_model_name,
            "timing_analysis": timing_analysis
        }
        
        job_manager.complete_job(job_id, result)
        logger.info(f"Subtitle job {job_id} completed in {processing_time:.1f}s")
        
    except Exception as e:
        error_message = f"Error processing subtitles: {str(e)}"
        logger.error(f"Job {job_id} failed: {error_message}")
        job_manager.fail_job(job_id, error_message)
        
        # Emergency cleanup on failure
        if psutil.virtual_memory().percent > MEMORY_WARNING_THRESHOLD * 100:
            emergency_cleanup()
        
        # Clean up partial files
        cleanup_files = [
            f"temp/{job_id}_input.mp4",
            f"temp/{job_id}_output.mp4", 
            f"temp/{job_id}_subtitles.srt"
        ]
        for file_path in cleanup_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Cleaned up partial file: {file_path}")
                except Exception as cleanup_error:
                    logger.error(f"Warning: Could not cleanup {file_path}: {cleanup_error}")

def process_split_job_optimized(job_id, data):
    """Optimized video splitting."""
    start_time = time.time()
    
    try:
        job_manager.update_job_status(job_id, "processing", 10)
        
        # Get video path
        if 'url' in data:
            video_url = data['url']
            video_path = download_file(video_url, 'temp', f"{job_id}_input.mp4")
        elif 'job_id' in data:
            previous_job = job_manager.get_job(data['job_id'])
            if not previous_job or previous_job['status'] != 'completed':
                raise Exception(f"Previous job not completed: {data['job_id']}")
            video_path = previous_job['output_path']
        
        job_manager.update_job_status(job_id, "processing", 50)
        
        # Split video with optimized service
        output_path = f"temp/{job_id}_split.mp4"
        video_service.split_video(
            video_path,
            data['start_time'],
            data['end_time'],
            output_path
        )
        
        processing_time = time.time() - start_time
        result = {
            "output_path": output_path,
            "processing_info": {
                "processing_time_seconds": processing_time,
                "method": "optimized_splitting"
            }
        }
        
        job_manager.complete_job(job_id, result)
        logger.info(f"Split job {job_id} completed in {processing_time:.1f}s")
        
    except Exception as e:
        logger.error(f"Split job {job_id} failed: {e}")
        job_manager.fail_job(job_id, str(e))

def process_join_job_optimized(job_id, data):
    """Optimized video joining."""
    start_time = time.time()
    
    try:
        job_manager.update_job_status(job_id, "processing", 10)
        
        # Download videos with progress
        video_paths = []
        for i, url in enumerate(data['urls']):
            video_path = download_file(url, 'temp', f"{job_id}_input_{i}.mp4")
            video_paths.append(video_path)
            progress = 10 + (i + 1) * 30 // len(data['urls'])
            job_manager.update_job_status(job_id, "processing", progress)
        
        # Join videos with optimized service
        output_path = f"temp/{job_id}_joined.mp4"
        video_service.join_videos(video_paths, output_path)
        
        processing_time = time.time() - start_time
        result = {
            "output_path": output_path,
            "processing_info": {
                "processing_time_seconds": processing_time,
                "videos_joined": len(video_paths),
                "method": "optimized_joining"
            }
        }
        
        job_manager.complete_job(job_id, result)
        logger.info(f"Join job {job_id} completed in {processing_time:.1f}s")
        
    except Exception as e:
        logger.error(f"Join job {job_id} failed: {e}")
        job_manager.fail_job(job_id, str(e))

def process_music_job_optimized(job_id, data):
    """Optimized music addition."""
    start_time = time.time()
    
    try:
        job_manager.update_job_status(job_id, "processing", 10)
        
        # Download files
        video_path = download_file(data['video_url'], 'temp', f"{job_id}_video.mp4")
        job_manager.update_job_status(job_id, "processing", 30)
        
        music_path = download_file(data['music_url'], 'temp', f"{job_id}_music.mp3")
        job_manager.update_job_status(job_id, "processing", 50)
        
        # Add music with optimized service
        output_path = f"temp/{job_id}_with_music.mp4"
        video_service.add_music_to_video(
            video_path,
            music_path,
            output_path,
            data['settings']
        )
        
        processing_time = time.time() - start_time
        result = {
            "output_path": output_path,
            "processing_info": {
                "processing_time_seconds": processing_time,
                "method": "optimized_music_addition"
            }
        }
        
        job_manager.complete_job(job_id, result)
        logger.info(f"Music job {job_id} completed in {processing_time:.1f}s")
        
    except Exception as e:
        logger.error(f"Music job {job_id} failed: {e}")
        job_manager.fail_job(job_id, str(e))

# Include all other endpoints from the original app.py
@app.route('/download/<job_id>', methods=['GET'])
def download_result(job_id):
    try:
        job = job_manager.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        if job['status'] != 'completed':
            return jsonify({"error": "Job not completed yet"}), 400
        
        if 'output_path' not in job:
            return jsonify({"error": "No output file available"}), 404
        
        return send_file(job['output_path'], as_attachment=True)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download-subtitles/<job_id>', methods=['GET'])
def download_subtitles(job_id):
    try:
        job = job_manager.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        if job['status'] != 'completed':
            return jsonify({"error": "Job not completed yet"}), 400
        
        if 'subtitle_path' not in job or not job['subtitle_path']:
            return jsonify({"error": "No subtitle file available"}), 404
        
        if not os.path.exists(job['subtitle_path']):
            return jsonify({"error": "Subtitle file not found"}), 404
        
        return send_file(job['subtitle_path'], as_attachment=True, download_name=f"{job_id}_subtitles.srt")
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/cleanup', methods=['POST'])
def cleanup_all():
    """Enhanced cleanup with resource monitoring."""
    try:
        logger.info("Starting comprehensive cleanup...")
        
        # Force memory cleanup first
        emergency_cleanup()
        
        cleanup_stats = {
            "jobs_removed": 0,
            "temp_files_removed": 0,
            "upload_files_removed": 0,
            "static_files_removed": 0,
            "total_size_freed": 0,
            "directories_cleaned": []
        }
        
        # Clean up directories (same as original but with better logging)
        directories = [
            ('jobs', 'jobs'),
            ('temp', 'temp'),
            ('uploads', 'uploads'),
            ('static', 'static')
        ]
        
        for dir_name, stat_key in directories:
            if os.path.exists(dir_name):
                for file_name in os.listdir(dir_name):
                    file_path = os.path.join(dir_name, file_name)
                    if os.path.isfile(file_path):
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleanup_stats[f"{stat_key}_removed"] += 1
                            cleanup_stats["total_size_freed"] += file_size
                            logger.info(f"Removed {stat_key} file: {file_path}")
                        except Exception as e:
                            logger.error(f"Could not remove {file_path}: {e}")
                cleanup_stats["directories_cleaned"].append(dir_name)
        
        # Format size
        def format_size(bytes_size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_size < 1024.0:
                    return f"{bytes_size:.2f} {unit}"
                bytes_size /= 1024.0
            return f"{bytes_size:.2f} TB"
        
        cleanup_stats["total_size_freed_formatted"] = format_size(cleanup_stats["total_size_freed"])
        
        # Reset performance stats
        resource_stats.update({
            "peak_memory": psutil.virtual_memory().percent / 100.0,
            "warnings": [],
            "job_count": 0
        })
        
        logger.info(f"Cleanup completed! Freed {cleanup_stats['total_size_freed_formatted']}")
        
        return jsonify({
            "status": "success",
            "message": "Enhanced cleanup completed with resource optimization",
            "timestamp": datetime.now().isoformat(),
            "cleanup_stats": cleanup_stats,
            "memory_after_cleanup": f"{psutil.virtual_memory().percent:.1f}%"
        })
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('temp', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('jobs', exist_ok=True)
    
    logger.info(f"Starting optimized VideoEditorAPI with {optimal_workers} workers")
    logger.info(f"System: {psutil.virtual_memory().total/(1024**3):.1f}GB RAM, {psutil.cpu_count()} CPU cores")
    
    # Use port from environment or default to 8080
    port = int(os.environ.get('PORT', 8080))
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    finally:
        # Clean shutdown
        monitoring_active = False
        executor.shutdown(wait=True)
        subtitle_service.unload_model()