"""
Unified VideoEditor API Server
Uses all available system resources with Whisper tiny model.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import threading
import psutil
import time
import math
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime
import re
import logging
import mimetypes
import shutil

# Import services
from app.services.video_service import VideoService
from app.services.subtitle_service import SubtitleService
from app.services.job_manager import JobManager
from app.services.audio_service import AudioService
from app.services.video_filter_service import VideoFilterService
from app.services.aspect_ratio_service import AspectRatioService
from app.services.voiceover_service import VoiceoverService
from app.utils.download_utils import download_file

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize services
video_service = VideoService()
subtitle_service = SubtitleService()
job_manager = JobManager()
audio_service = AudioService()
video_filter_service = VideoFilterService()
aspect_ratio_service = AspectRatioService()
voiceover_service = VoiceoverService()

# Auto-detect optimal workers (use all available cores)
optimal_workers = min(psutil.cpu_count(logical=True), 8)  # Cap at 8 for stability
executor = ThreadPoolExecutor(max_workers=optimal_workers)

# Resource monitoring
resource_stats = {
    "peak_memory": 0,
    "average_cpu": 0,
    "job_count": 0,
    "warnings": []
}

logger.info(f"🚀 VideoEditor API initialized with {optimal_workers} workers")
logger.info(f"💾 System: {psutil.virtual_memory().total/(1024**3):.1f}GB RAM, {psutil.cpu_count()} CPU cores")
logger.info(f"🎙️ Whisper Model: tiny (fixed)")

def parse_time_to_seconds(time_input):
    """Convert time format to seconds."""
    if isinstance(time_input, (int, float)):
        return float(time_input)
    
    if isinstance(time_input, str):
        try:
            return float(time_input)
        except ValueError:
            pass
        
        # Parse time formats: HH:MM:SS,mmm or HH:MM:SS.mmm or HH:MM:SS:mmm
        time_pattern = r'(\d{1,2}):(\d{1,2}):(\d{1,2})[,.:](\d{3})'
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

def detect_and_rename_media_file(temp_path, job_id):
    """
    Detect the actual file type of downloaded media and rename with correct extension.
    
    Args:
        temp_path: Path to the temporary downloaded file
        job_id: Job ID for generating the new filename
    
    Returns:
        str: Path to the renamed file with correct extension
    """
    try:
        # Try to detect file type using multiple methods
        detected_ext = None
        
        # Method 1: Use mimetypes to guess from file content
        mime_type, _ = mimetypes.guess_type(temp_path)
        
        if not mime_type:
            # Method 2: Try to read file signature/magic bytes
            with open(temp_path, 'rb') as f:
                header = f.read(16)
                
                # Check common image signatures
                if header.startswith(b'\x89PNG\r\n\x1a\n'):
                    mime_type = 'image/png'
                elif header.startswith(b'\xff\xd8\xff'):
                    mime_type = 'image/jpeg'
                elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                    mime_type = 'image/gif'
                elif header.startswith(b'BM'):
                    mime_type = 'image/bmp'
                # Check video signatures
                elif b'ftypmp4' in header or b'ftypisom' in header:
                    mime_type = 'video/mp4'
                elif header.startswith(b'\x1aE\xdf\xa3'):
                    mime_type = 'video/webm'
                elif header.startswith(b'RIFF') and b'AVI ' in header:
                    mime_type = 'video/avi'
        
        # Map mime types to extensions
        if mime_type:
            if mime_type in ['image/png']:
                detected_ext = '.png'
            elif mime_type in ['image/jpeg']:
                detected_ext = '.jpg'
            elif mime_type in ['image/gif']:
                detected_ext = '.gif'
            elif mime_type in ['image/bmp']:
                detected_ext = '.bmp'
            elif mime_type in ['video/mp4']:
                detected_ext = '.mp4'
            elif mime_type in ['video/webm']:
                detected_ext = '.webm'
            elif mime_type in ['video/avi']:
                detected_ext = '.avi'
        
        # Default to .mp4 if detection fails
        if not detected_ext:
            detected_ext = '.mp4'
            logger.warning(f"Could not detect file type for {temp_path}, defaulting to .mp4")
        
        # Create new path with correct extension
        new_path = f"temp/{job_id}_media{detected_ext}"
        
        # Rename the file
        shutil.move(temp_path, new_path)
        
        logger.info(f"File type detected as {detected_ext}, renamed to {new_path}")
        return new_path
        
    except Exception as e:
        logger.error(f"Error detecting file type: {e}")
        # Fallback: just rename to .mp4
        fallback_path = f"temp/{job_id}_media.mp4"
        try:
            shutil.move(temp_path, fallback_path)
            return fallback_path
        except:
            # If even rename fails, return original path
            return temp_path

@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check with system information."""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent()
    
    # Update peak memory tracking
    current_memory_percent = memory.percent / 100
    if current_memory_percent > resource_stats["peak_memory"]:
        resource_stats["peak_memory"] = current_memory_percent
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "resources": {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
            "workers": optimal_workers,
            "total_cpu_cores": psutil.cpu_count(logical=True),
            "physical_cpu_cores": psutil.cpu_count(logical=False)
        },
        "whisper_model": {
            "status": "loaded" if hasattr(subtitle_service, 'current_model') else "ready",
            "model": "tiny",  # Always tiny
            "fp16_enabled": True
        },
        "performance_stats": {
            "peak_memory": resource_stats["peak_memory"],
            "average_cpu": cpu_percent,
            "job_count": resource_stats["job_count"],
            "warnings": resource_stats["warnings"][-5:]  # Last 5 warnings
        }
    }
    
    return jsonify(health_data)

@app.route('/generate-subtitles', methods=['POST'])
def generate_subtitles():
    """Generate subtitles only without adding to video."""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({"error": "Missing required 'url' parameter"}), 400
        
        job_id = str(uuid.uuid4())
        project_id = data.get('project_id', str(uuid.uuid4()))
        
        # Check if subtitles already exist for this project
        existing_subtitles = job_manager.get_project_subtitles(project_id)
        if existing_subtitles:
            return jsonify({
                "message": "Subtitles already exist for this project",
                "project_id": project_id,
                "created_at": existing_subtitles["created_at"],
                "subtitle_count": len(existing_subtitles["subtitle_data"]),
                "status": "already_exists"
            })
        
        # Settings for subtitle generation only
        generation_settings = {
            "project_id": project_id,
            "url": data['url'],
            "language": data.get("language", "en"),
            "timing_offset": data.get("timing_offset", 0.0),
            "model": "tiny"  # Force tiny model
        }
        
        job_manager.create_job(job_id, "generate_subtitles", "pending", generation_settings)
        resource_stats["job_count"] += 1
        
        executor.submit(process_generate_subtitles_job, job_id, generation_settings)
        
        return jsonify({
            "job_id": job_id,
            "project_id": project_id,
            "project_id_generated": project_id != data.get('project_id'),
            "status": "pending",
            "message": "Subtitle generation started",
            "whisper_model": "tiny",
            "estimated_workers": optimal_workers,
            "check_status_url": f"/job-status/{job_id}"
        })
        
    except Exception as e:
        logger.error(f"Error starting subtitle generation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/add-subtitles', methods=['POST'])
def add_subtitles():
    """Add subtitles to video, generating them if they don't exist."""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({"error": "Missing required field: url"}), 400
        
        job_id = str(uuid.uuid4())
        
        # Default settings
        default_settings = {
            "language": "en",
            "return_subtitles_file": True,
            "word_level_mode": "karaoke",
            "model": "tiny",  # Force tiny model
            "settings": {
                "font-size": 120,
                "font-family": "Luckiest Guy",
                "line-color": "#FFF4E9", 
                "outline-width": 10,
                "normal-color": "#FFFFFF"
            }
        }
        
        # Merge with provided settings
        settings = {**default_settings, **data}
        if "settings" in data:
            settings["settings"] = {**default_settings["settings"], **data["settings"]}
        
        job_manager.create_job(job_id, "add_subtitles", "pending", settings)
        resource_stats["job_count"] += 1
        
        executor.submit(process_subtitle_job, job_id, settings)
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "Subtitle processing started",
            "whisper_model": "tiny",
            "estimated_workers": optimal_workers
        })
        
    except Exception as e:
        logger.error(f"Error starting subtitle job: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/split-video', methods=['POST'])
def split_video():
    """Split video by time range."""
    try:
        data = request.get_json()
        
        # Validate input
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
        
        job_id = str(uuid.uuid4())
        
        processed_data = {
            **data,
            'start_time': start_seconds,
            'end_time': end_seconds
        }
        
        job_manager.create_job(job_id, "split_video", "pending", processed_data)
        resource_stats["job_count"] += 1
        
        executor.submit(process_split_job, job_id, processed_data)
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "Video splitting started",
            "estimated_workers": optimal_workers
        })
        
    except Exception as e:
        logger.error(f"Error starting split job: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/join-videos', methods=['POST'])
def join_videos():
    """Join multiple videos together."""
    try:
        data = request.get_json()
        
        if not data or 'urls' not in data or not isinstance(data['urls'], list):
            return jsonify({"error": "Missing required field: urls (must be an array)"}), 400
        
        if len(data['urls']) < 2:
            return jsonify({"error": "At least 2 video URLs are required"}), 400
        
        job_id = str(uuid.uuid4())
        
        job_manager.create_job(job_id, "join_videos", "pending", data)
        resource_stats["job_count"] += 1
        
        executor.submit(process_join_job, job_id, data)
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "Video joining started",
            "video_count": len(data['urls']),
            "estimated_workers": optimal_workers
        })
        
    except Exception as e:
        logger.error(f"Error starting join job: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/add-music', methods=['POST'])
def add_music():
    """Add background music to video."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['video_url', 'music_url']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        job_id = str(uuid.uuid4())
        
        # Optional settings with proper type conversion
        settings = {
            "volume": float(data.get('volume', 0.5)),
            "fade_in": float(data.get('fade_in', 0)),
            "fade_out": float(data.get('fade_out', 0)),
            "loop_music": str(data.get('loop_music', False)).lower() in ['true', '1', 'yes']
        }
        
        job_data = {**data, "settings": settings}
        
        job_manager.create_job(job_id, "add_music", "pending", job_data)
        resource_stats["job_count"] += 1
        
        executor.submit(process_music_job, job_id, job_data)
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "Music addition started",
            "estimated_workers": optimal_workers
        })
        
    except Exception as e:
        logger.error(f"Error starting music job: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/voice-filters', methods=['POST'])
def apply_voice_filter():
    """Apply voice filters to audio/video files."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'url' not in data:
            return jsonify({"error": "Missing required field: url"}), 400
        
        # Get filter type (default to telephone)
        filter_type = data.get('filter_type', 'telephone')
        
        # Validate filter type
        supported_filters = audio_service.get_supported_filters()
        if filter_type not in supported_filters:
            return jsonify({
                "error": f"Unsupported filter type: {filter_type}",
                "supported_filters": supported_filters
            }), 400
        
        job_id = str(uuid.uuid4())
        
        # Job data
        job_data = {
            "url": data['url'],
            "filter_type": filter_type,
            "filter_info": supported_filters[filter_type]
        }
        
        job_manager.create_job(job_id, "voice_filter", "pending", job_data)
        resource_stats["job_count"] += 1
        
        executor.submit(process_voice_filter_job, job_id, job_data)
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": f"Voice filter processing started",
            "filter_applied": supported_filters[filter_type],
            "estimated_workers": optimal_workers
        })
        
    except Exception as e:
        logger.error(f"Error starting voice filter job: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/voice-filters/list', methods=['GET'])
def list_voice_filters():
    """Get list of available voice filters."""
    try:
        supported_filters = audio_service.get_supported_filters()
        return jsonify({
            "supported_filters": supported_filters,
            "default_filter": "telephone"
        })
    except Exception as e:
        logger.error(f"Error listing voice filters: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/video-filters', methods=['POST'])
def apply_video_filter():
    """Apply visual filters to video files."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'url' not in data:
            return jsonify({"error": "Missing required field: url"}), 400
        
        # Get filter type (default to crt)
        filter_type = data.get('filter_type', 'crt')
        
        # Validate filter type
        supported_filters = video_filter_service.get_supported_filters()
        if filter_type not in supported_filters:
            return jsonify({
                "error": f"Unsupported filter type: {filter_type}",
                "supported_filters": supported_filters
            }), 400
        
        # Get custom parameters if provided
        custom_params = data.get('parameters', {})
        
        job_id = str(uuid.uuid4())
        
        # Job data
        job_data = {
            "url": data['url'],
            "filter_type": filter_type,
            "custom_parameters": custom_params,
            "filter_info": supported_filters[filter_type]
        }
        
        job_manager.create_job(job_id, "video_filter", "pending", job_data)
        resource_stats["job_count"] += 1
        
        executor.submit(process_video_filter_job, job_id, job_data)
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": f"Video filter processing started",
            "filter_applied": supported_filters[filter_type],
            "custom_parameters": custom_params,
            "estimated_workers": optimal_workers
        })
        
    except Exception as e:
        logger.error(f"Error starting video filter job: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/video-filters/list', methods=['GET'])
def list_video_filters():
    """Get list of available video filters."""
    try:
        supported_filters = video_filter_service.get_supported_filters()
        return jsonify({
            "supported_filters": supported_filters,
            "default_filter": "crt"
        })
    except Exception as e:
        logger.error(f"Error listing video filters: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/video-filters/parameters/<filter_type>', methods=['GET'])
def get_filter_parameters(filter_type):
    """Get default parameters for a specific filter."""
    try:
        parameters = video_filter_service.get_filter_parameters(filter_type)
        if parameters is None:
            return jsonify({"error": f"Filter type '{filter_type}' not found"}), 404
        
        return jsonify({
            "filter_type": filter_type,
            "parameters": parameters,
            "description": f"Default parameters for {filter_type} filter"
        })
    except Exception as e:
        logger.error(f"Error getting filter parameters: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/video-aspect-ratio', methods=['POST'])
def change_video_aspect_ratio():
    """Change video aspect ratio with different scaling modes."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'url' not in data:
            return jsonify({"error": "Missing required field: url"}), 400
        
        if 'aspect_ratio' not in data:
            return jsonify({"error": "Missing required field: aspect_ratio"}), 400
        
        # Get parameters
        aspect_ratio = data['aspect_ratio']
        scale_mode = data.get('scale_mode', 'fit')
        target_height = data.get('target_height')
        
        # Validate aspect ratio
        try:
            aspect_ratio_service.parse_aspect_ratio(aspect_ratio)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        
        # Validate scale mode
        if scale_mode not in aspect_ratio_service.get_scale_modes():
            return jsonify({
                "error": f"Invalid scale mode: {scale_mode}",
                "available_modes": list(aspect_ratio_service.get_scale_modes().keys())
            }), 400
        
        job_id = str(uuid.uuid4())
        
        # Job data
        job_data = {
            "url": data['url'],
            "aspect_ratio": aspect_ratio,
            "scale_mode": scale_mode,
            "target_height": target_height,
            "scale_mode_info": aspect_ratio_service.get_scale_modes()[scale_mode]
        }
        
        job_manager.create_job(job_id, "aspect_ratio", "pending", job_data)
        resource_stats["job_count"] += 1
        
        executor.submit(process_aspect_ratio_job, job_id, job_data)
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": f"Aspect ratio change started",
            "aspect_ratio": aspect_ratio,
            "scale_mode": scale_mode,
            "scale_mode_info": aspect_ratio_service.get_scale_modes()[scale_mode],
            "estimated_workers": optimal_workers
        })
        
    except Exception as e:
        logger.error(f"Error starting aspect ratio job: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/video-aspect-ratio/ratios', methods=['GET'])
def list_aspect_ratios():
    """Get list of common aspect ratios."""
    try:
        ratios = aspect_ratio_service.get_common_ratios()
        return jsonify({
            "common_ratios": ratios,
            "examples": {
                "youtube": "16:9",
                "tiktok": "9:16", 
                "instagram_post": "1:1",
                "instagram_story": "9:16"
            }
        })
    except Exception as e:
        logger.error(f"Error listing aspect ratios: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/video-aspect-ratio/modes', methods=['GET'])
def list_scale_modes():
    """Get list of available scaling modes."""
    try:
        modes = aspect_ratio_service.get_scale_modes()
        return jsonify({
            "scale_modes": modes,
            "default_mode": "fit"
        })
    except Exception as e:
        logger.error(f"Error listing scale modes: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/add-voiceover', methods=['POST'])
def add_voiceover():
    """Add voiceover to video with intelligent duration matching."""
    try:
        data = request.get_json()
        
        # Validate required fields - now support both video_url and image_url  
        if not data or ('video_url' not in data and 'image_url' not in data) or 'audio_url' not in data:
            return jsonify({"error": "Missing required fields: (video_url OR image_url) and audio_url"}), 400
        
        # Determine the media URL (prioritize video_url if both provided)
        media_url = data.get('video_url') or data.get('image_url')
        
        # Create job
        job_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id,
            "operation": "add_voiceover",
            "media_url": media_url,
            "audio_url": data["audio_url"],
            "zoom_factor": data.get("zoom_factor", 1.0),  # Default no zoom
            "created_at": datetime.now().isoformat()
        }
        
        # Initialize job status
        job_manager.create_job(job_id, "add_voiceover", "pending", job_data)
        
        # Submit job to executor
        executor.submit(process_voiceover_job, job_id, job_data)
        
        return jsonify({
            "message": "Voiceover job started",
            "job_id": job_id,
            "status_url": f"/job-status/{job_id}"
        }), 202
        
    except Exception as e:
        logger.error(f"Error starting voiceover job: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/job-status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status and progress."""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        # Add system info
        memory = psutil.virtual_memory()
        
        response = {
            "job_id": job_id,
            "status": job["status"],
            "progress": job.get("progress", 0),
            "error": job.get("error"),
            "status_message": job.get("status_message", "Processing..."),
            "processing_info": job.get("processing_info", {}),
            "system_status": {
                "memory_usage_percent": memory.percent,
                "cpu_cores_available": psutil.cpu_count(),
                "workers": optimal_workers
            }
        }
        
        # Add download URLs if completed
        if job["status"] == "completed":
            if job.get("output_path"):
                response["video_download_url"] = f"/download/{job_id}"
            if job.get("subtitle_path"):
                response["subtitle_download_url"] = f"/download-subtitles/{job_id}"
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/download/<job_id>', methods=['GET'])
def download_result(job_id):
    """Download processed video file."""
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
        logger.error(f"Download error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/download-subtitles/<job_id>', methods=['GET'])
def download_subtitles(job_id):
    """Download subtitle file."""
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
        logger.error(f"Subtitle download error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/cleanup', methods=['POST'])
def cleanup_all():
    """Comprehensive cleanup endpoint."""
    try:
        logger.info("🧹 Starting cleanup...")
        
        cleanup_stats = {
            "jobs_removed": 0,
            "temp_files_removed": 0,
            "upload_files_removed": 0,
            "static_files_removed": 0,
            "total_size_freed": 0
        }
        
        # Clean up all directories
        for dir_name in ['jobs', 'temp', 'uploads', 'static']:
            if os.path.exists(dir_name):
                for file_name in os.listdir(dir_name):
                    file_path = os.path.join(dir_name, file_name)
                    if os.path.isfile(file_path):
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleanup_stats[f"{dir_name}_files_removed"] += 1
                            cleanup_stats["total_size_freed"] += file_size
                        except Exception as e:
                            logger.warning(f"Could not remove {file_path}: {e}")
        
        # Format size
        def format_size(bytes_size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_size < 1024.0:
                    return f"{bytes_size:.2f} {unit}"
                bytes_size /= 1024.0
            return f"{bytes_size:.2f} TB"
        
        cleanup_stats["total_size_freed_formatted"] = format_size(cleanup_stats["total_size_freed"])
        
        logger.info(f"🧹 Cleanup completed! Freed {cleanup_stats['total_size_freed_formatted']}")
        
        return jsonify({
            "status": "success",
            "message": "Cleanup completed",
            "timestamp": datetime.now().isoformat(),
            "cleanup_stats": cleanup_stats
        })
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({"error": str(e)}), 500

# Background job processors
def process_generate_subtitles_job(job_id, settings):
    """Generate subtitles only."""
    video_path = None
    start_time = time.time()
    
    try:
        job_manager.update_job_status(job_id, "processing", 10, "🚀 Starting subtitle generation...")
        
        # Download video
        job_manager.update_job_status(job_id, "processing", 15, "📥 Downloading video...")
        video_url = settings['url']
        video_path = download_file(video_url, 'temp', f"{job_id}_input.mp4")
        job_manager.update_job_status(job_id, "processing", 25, "✅ Video downloaded")
        
        # Progress callback
        def update_progress(progress, message):
            mapped_progress = 25 + int((progress / 100) * 65)
            job_manager.update_job_status(job_id, "processing", mapped_progress, message)
        
        # Generate subtitles with tiny model
        job_manager.update_job_status(job_id, "processing", 30, "🎙️ Generating subtitles with Whisper tiny...")
        subtitle_data = subtitle_service.generate_subtitles(
            video_path,
            settings['language'],
            settings.get('timing_offset', 0.0)
        )
        
        # Save subtitles
        job_manager.update_job_status(job_id, "processing", 95, "💾 Saving subtitles...")
        subtitle_path = job_manager.save_project_subtitles(
            settings['project_id'], 
            subtitle_data, 
            settings['url']
        )
        
        if not subtitle_path:
            raise Exception("Failed to save project subtitles")
        
        processing_time = time.time() - start_time
        job_manager.update_job_status(job_id, "completed", 100, f"✅ Subtitles generated in {processing_time:.1f}s")
        
        # Update job with results
        job = job_manager.get_job(job_id)
        job['subtitle_path'] = subtitle_path
        job['processing_time'] = processing_time
        job['subtitle_count'] = len(subtitle_data)
        job['model_used'] = 'tiny'
        job_manager._save_job(job)
        
        logger.info(f"✅ Subtitle generation completed for project {settings['project_id']} in {processing_time:.1f}s")
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"❌ Subtitle generation failed: {str(e)}"
        logger.error(f"{error_msg} (after {processing_time:.1f}s)")
        job_manager.update_job_status(job_id, "failed", None, error_msg)
        
        job = job_manager.get_job(job_id)
        if job:
            job['error'] = str(e)
            job['processing_time'] = processing_time
            job_manager._save_job(job)
    
    finally:
        # Cleanup
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except:
                pass

def process_subtitle_job(job_id, settings):
    """Add subtitles to video."""
    video_path = None
    start_time = time.time()
    
    try:
        job_manager.update_job_status(job_id, "processing", 10, "🚀 Starting subtitle processing...")
        
        # Download video
        job_manager.update_job_status(job_id, "processing", 15, "📥 Downloading video...")
        video_url = settings['url']
        video_path = download_file(video_url, 'temp', f"{job_id}_input.mp4")
        job_manager.update_job_status(job_id, "processing", 30, "✅ Video downloaded")
        
        # Generate subtitles with tiny model
        job_manager.update_job_status(job_id, "processing", 35, "🎙️ Generating subtitles...")
        subtitle_data = subtitle_service.generate_subtitles(
            video_path, 
            settings['language'],
            settings.get('timing_offset', 0.0)
        )
        
        job_manager.update_job_status(job_id, "processing", 70, "🎬 Adding subtitles to video...")
        
        # Create video with subtitles
        output_path = f"temp/{job_id}_output.mp4"
        word_mode = settings.get('word_level_mode', 'karaoke')
        
        # Debug: Print settings being passed to video service
        print(f"📋 JOB SETTINGS DEBUG: Full settings object: {settings}")
        print(f"📋 JOB SETTINGS DEBUG: settings['settings']: {settings.get('settings', 'NOT FOUND')}")
        
        video_service.add_subtitles_to_video(
            video_path,
            subtitle_data,
            output_path,
            settings['settings'],
            word_mode
        )
        
        # Verify output
        if not os.path.exists(output_path):
            raise Exception(f"Video processing failed - output file not created")
        
        # Handle subtitle file return
        result = {"output_path": output_path}
        if settings.get('return_subtitles_file', False):
            subtitle_path = f"temp/{job_id}_subtitles.srt"
            subtitle_service.save_subtitle_file(subtitle_data, subtitle_path)
            result["subtitle_path"] = subtitle_path
        
        processing_time = time.time() - start_time
        job_manager.update_job_status(job_id, "completed", 100, f"✅ Completed in {processing_time:.1f}s")
        
        job_manager.complete_job(job_id, result)
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_message = f"Error processing subtitles: {str(e)}"
        logger.error(f"Job {job_id} failed: {error_message}")
        job_manager.fail_job(job_id, error_message)
        
        # Clean up partial files on failure
        cleanup_files = [
            f"temp/{job_id}_input.mp4",
            f"temp/{job_id}_output.mp4",
            f"temp/{job_id}_subtitles.srt"
        ]
        for file_path in cleanup_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass

def process_split_job(job_id, data):
    """Split video by time range."""
    video_path = None
    start_time = time.time()
    
    try:
        job_manager.update_job_status(job_id, "processing", 10, "🚀 Starting video splitting...")
        
        # Get video path
        if 'url' in data:
            job_manager.update_job_status(job_id, "processing", 15, "📥 Downloading video...")
            video_url = data['url']
            video_path = download_file(video_url, 'temp', f"{job_id}_input.mp4")
            job_manager.update_job_status(job_id, "processing", 30, "✅ Video downloaded")
        elif 'job_id' in data:
            previous_job = job_manager.get_job(data['job_id'])
            if not previous_job or previous_job['status'] != 'completed':
                raise Exception(f"Previous job not completed: {data['job_id']}")
            
            video_path = previous_job.get('output_path')
            if not video_path or not os.path.exists(video_path):
                raise Exception(f"Previous job output file not found")
        
        job_manager.update_job_status(job_id, "processing", 50, "✂️ Splitting video...")
        
        # Split video
        output_path = f"temp/{job_id}_split.mp4"
        video_service.split_video(
            video_path,
            data['start_time'],
            data['end_time'],
            output_path
        )
        
        processing_time = time.time() - start_time
        job_manager.update_job_status(job_id, "completed", 100, f"✅ Split completed in {processing_time:.1f}s")
        
        job_manager.complete_job(job_id, {"output_path": output_path})
        
    except Exception as e:
        processing_time = time.time() - start_time
        job_manager.fail_job(job_id, str(e))
    
    finally:
        if 'url' in data and video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except:
                pass

def process_join_job(job_id, data):
    """Join multiple videos."""
    video_paths = []
    start_time = time.time()
    
    try:
        job_manager.update_job_status(job_id, "processing", 10, "🚀 Starting video joining...")
        
        # Download all videos
        total_videos = len(data['urls'])
        for i, url in enumerate(data['urls']):
            progress = 10 + (i * 60 // total_videos)
            job_manager.update_job_status(job_id, "processing", progress, f"📥 Downloading video {i+1}/{total_videos}...")
            video_path = download_file(url, 'temp', f"{job_id}_input_{i}.mp4")
            video_paths.append(video_path)
        
        job_manager.update_job_status(job_id, "processing", 75, "🔗 Joining videos...")
        
        # Join videos
        output_path = f"temp/{job_id}_joined.mp4"
        video_service.join_videos(video_paths, output_path)
        
        processing_time = time.time() - start_time
        job_manager.update_job_status(job_id, "completed", 100, f"✅ Joined in {processing_time:.1f}s")
        
        job_manager.complete_job(job_id, {"output_path": output_path})
        
    except Exception as e:
        processing_time = time.time() - start_time
        job_manager.fail_job(job_id, str(e))
    
    finally:
        for video_path in video_paths:
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except:
                    pass

def process_music_job(job_id, data):
    """Add music to video."""
    video_path = None
    music_path = None
    start_time = time.time()
    
    try:
        job_manager.update_job_status(job_id, "processing", 10, "🚀 Starting music addition...")
        
        # Download video and music
        job_manager.update_job_status(job_id, "processing", 15, "📥 Downloading video...")
        video_path = download_file(data['video_url'], 'temp', f"{job_id}_video.mp4")
        job_manager.update_job_status(job_id, "processing", 30, "📥 Downloading music...")
        music_path = download_file(data['music_url'], 'temp', f"{job_id}_music.mp3")
        
        job_manager.update_job_status(job_id, "processing", 50, "🎵 Adding music to video...")
        
        # Add music to video
        output_path = f"temp/{job_id}_with_music.mp4"
        video_service.add_music_to_video(
            video_path,
            music_path,
            output_path,
            data['settings']
        )
        
        processing_time = time.time() - start_time
        job_manager.update_job_status(job_id, "completed", 100, f"✅ Music added in {processing_time:.1f}s")
        
        job_manager.complete_job(job_id, {"output_path": output_path})
        
    except Exception as e:
        processing_time = time.time() - start_time
        job_manager.fail_job(job_id, str(e))
    
    finally:
        for file_path in [video_path, music_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass

def process_voice_filter_job(job_id, data):
    """Apply voice filter to audio/video."""
    input_path = None
    start_time = time.time()
    
    try:
        job_manager.update_job_status(job_id, "processing", 10, "🚀 Starting voice filter processing...")
        
        # Download input file first
        job_manager.update_job_status(job_id, "processing", 15, "📥 Downloading input file...")
        
        # Download as temporary file first to detect actual type
        temp_input_path = download_file(data['url'], 'temp', f"{job_id}_temp_input")
        
        # Detect actual file type using file command or moviepy
        job_manager.update_job_status(job_id, "processing", 25, "🔍 Detecting file type...")
        
        try:
            # Try to detect if it's a video file using moviepy
            import moviepy.editor as mp
            try:
                test_video = mp.VideoFileClip(temp_input_path)
                # If we can get video properties, it's a video file
                is_video_file = hasattr(test_video, 'fps') and test_video.fps is not None
                test_video.close()
                logger.info(f"Video detection: fps check passed = {is_video_file}")
            except Exception as e:
                # If moviepy fails to load as video, it's likely audio
                is_video_file = False
                logger.info(f"Video detection: moviepy failed ({e}), treating as audio")
            
            # Rename file with correct extension based on detection
            if is_video_file:
                input_filename = f"{job_id}_input.mp4"
                output_ext = '.mp4'
                file_type = "VIDEO"
            else:
                input_filename = f"{job_id}_input.wav"
                output_ext = '.wav'
                file_type = "AUDIO"
            
            input_path = os.path.join('temp', input_filename)
            
            # Rename the temp file to correct filename
            import shutil
            shutil.move(temp_input_path, input_path)
            
            job_manager.update_job_status(job_id, "processing", 30, f"✅ File downloaded and detected as {file_type}")
            logger.info(f"Voice filter: URL={data['url']}, detected_type={file_type}, output_ext={output_ext}")
            
        except Exception as e:
            logger.error(f"File type detection failed: {e}, defaulting to audio")
            # Default to audio if detection fails
            input_filename = f"{job_id}_input.wav"
            output_ext = '.wav'
            input_path = os.path.join('temp', input_filename)
            
            # Rename the temp file
            import shutil
            shutil.move(temp_input_path, input_path)
        
        output_path = f"temp/{job_id}_filtered{output_ext}"
        
        job_manager.update_job_status(job_id, "processing", 40, f"🎵 Applying {data['filter_type']} filter...")
        
        # Apply voice filter
        audio_service.apply_voice_filter(
            input_path,
            output_path,
            data['filter_type']
        )
        
        # Verify output
        if not os.path.exists(output_path):
            raise Exception("Voice filter processing failed - output file not created")
        
        processing_time = time.time() - start_time
        job_manager.update_job_status(job_id, "completed", 100, f"✅ Filter applied in {processing_time:.1f}s")
        
        job_manager.complete_job(job_id, {"output_path": output_path})
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_message = f"Error applying voice filter: {str(e)}"
        logger.error(f"Job {job_id} failed: {error_message}")
        job_manager.fail_job(job_id, error_message)
        
        # Clean up partial files on failure
        cleanup_files = [
            input_path,
            f"temp/{job_id}_filtered.mp4",
            f"temp/{job_id}_filtered.wav"
        ]
        for file_path in cleanup_files:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
    
    finally:
        # Clean up input file
        if input_path and os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass

def process_video_filter_job(job_id, data):
    """Apply video filter to video."""
    input_path = None
    start_time = time.time()
    
    try:
        job_manager.update_job_status(job_id, "processing", 10, "🚀 Starting video filter processing...")
        
        # Download input video
        job_manager.update_job_status(job_id, "processing", 15, "📥 Downloading video...")
        input_path = download_file(data['url'], 'temp', f"{job_id}_input.mp4")
        job_manager.update_job_status(job_id, "processing", 30, "✅ Video downloaded")
        
        output_path = f"temp/{job_id}_filtered.mp4"
        
        job_manager.update_job_status(job_id, "processing", 35, f"🎬 Applying {data['filter_type']} filter...")
        
        # Apply video filter
        video_filter_service.apply_video_filter(
            input_path,
            output_path,
            data['filter_type'],
            data.get('custom_parameters')
        )
        
        # Verify output
        if not os.path.exists(output_path):
            raise Exception("Video filter processing failed - output file not created")
        
        processing_time = time.time() - start_time
        job_manager.update_job_status(job_id, "completed", 100, f"✅ Filter applied in {processing_time:.1f}s")
        
        job_manager.complete_job(job_id, {"output_path": output_path})
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_message = f"Error applying video filter: {str(e)}"
        logger.error(f"Job {job_id} failed: {error_message}")
        job_manager.fail_job(job_id, error_message)
        
        # Clean up partial files on failure
        cleanup_files = [
            input_path,
            f"temp/{job_id}_filtered.mp4"
        ]
        for file_path in cleanup_files:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
    
    finally:
        # Clean up input file
        if input_path and os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass

def process_aspect_ratio_job(job_id, data):
    """Process aspect ratio change job."""
    input_path = None
    start_time = time.time()
    
    try:
        job_manager.update_job_status(job_id, "processing", 10, "🚀 Starting aspect ratio change...")
        
        # Download input video
        job_manager.update_job_status(job_id, "processing", 15, "📥 Downloading video...")
        input_path = download_file(data['url'], 'temp', f"{job_id}_input.mp4")
        job_manager.update_job_status(job_id, "processing", 30, "✅ Video downloaded")
        
        output_path = f"temp/{job_id}_aspect_changed.mp4"
        
        job_manager.update_job_status(job_id, "processing", 35, f"📐 Changing aspect ratio to {data['aspect_ratio']}...")
        
        # Apply aspect ratio change (this will set job status to completed)
        aspect_ratio_service.change_aspect_ratio(
            input_path,
            output_path,
            data['aspect_ratio'],
            data['scale_mode'],
            data.get('target_height'),
            job_manager=job_manager,
            job_id=job_id
        )
        
        # Verify output
        if not os.path.exists(output_path):
            raise Exception("Aspect ratio change failed - output file not created")
        
        # Complete the job with final details (status already set by service)
        processing_time = time.time() - start_time
        job_manager.complete_job(job_id, {
            "output_path": output_path, 
            "processing_time": f"{processing_time:.1f}s",
            "final_status": "✅ Aspect ratio change completed successfully"
        })
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_message = f"Error changing aspect ratio: {str(e)}"
        logger.error(f"Job {job_id} failed: {error_message}")
        job_manager.fail_job(job_id, error_message)
        
        # Clean up partial files on failure
        cleanup_files = [
            input_path,
            f"temp/{job_id}_aspect_changed.mp4"
        ]
        for file_path in cleanup_files:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
    
    finally:
        # Clean up input file
        if input_path and os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass

def process_voiceover_job(job_id, data):
    """Process voiceover addition job."""
    video_path = None
    audio_path = None
    start_time = time.time()
    
    try:
        job_manager.update_job_status(job_id, "processing", 5, "🚀 Starting voiceover addition...")
        
        # Download media file (video or image)
        job_manager.update_job_status(job_id, "processing", 15, "📥 Downloading media file...")
        media_url = data['media_url']
        
        # Download with temporary name first, then detect actual format
        temp_media_path = download_file(media_url, 'temp', f"{job_id}_media_temp")
        job_manager.update_job_status(job_id, "processing", 25, "🔍 Detecting file format...")
        
        # Detect actual file type and rename appropriately
        media_path = detect_and_rename_media_file(temp_media_path, job_id)
        job_manager.update_job_status(job_id, "processing", 30, "✅ Media file downloaded and validated")
        
        # Download audio file
        job_manager.update_job_status(job_id, "processing", 35, "📥 Downloading audio...")
        audio_path = download_file(data['audio_url'], 'temp', f"{job_id}_audio.mp3")
        job_manager.update_job_status(job_id, "processing", 50, "✅ Audio downloaded")
        
        # Validate files
        job_manager.update_job_status(job_id, "processing", 55, "🔍 Validating media files...")
        voiceover_service.validate_files(media_path, audio_path)
        
        # Get media info for duration analysis
        if voiceover_service.is_image_file(media_path):
            job_manager.update_job_status(job_id, "processing", 60, "🖼️ Image detected - will create video with zoom")
        else:
            media_info = voiceover_service.get_media_info(media_path)
            audio_info = voiceover_service.get_media_info(audio_path)
            
            if media_info and audio_info:
                duration_info = f"Media: {media_info['duration']:.1f}s, Audio: {audio_info['duration']:.1f}s"
                job_manager.update_job_status(job_id, "processing", 60, f"📊 {duration_info}")
        
        output_path = f"temp/{job_id}_with_voiceover.mp4"
        
        job_manager.update_job_status(job_id, "processing", 65, "🎤 Adding voiceover with duration matching...")
        
        # Apply voiceover with zoom factor
        zoom_factor = data.get('zoom_factor', 1.0)
        voiceover_service.add_voiceover(
            media_path,
            audio_path,
            output_path,
            zoom_factor=zoom_factor
        )
        
        # Verify output
        if not os.path.exists(output_path):
            raise Exception("Voiceover addition failed - output file not created")
        
        processing_time = time.time() - start_time
        job_manager.update_job_status(job_id, "completed", 100, f"✅ Voiceover added in {processing_time:.1f}s")
        
        job_manager.complete_job(job_id, {"output_path": output_path})
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_message = f"Error adding voiceover: {str(e)}"
        logger.error(f"Job {job_id} failed: {error_message}")
        job_manager.fail_job(job_id, error_message)
        
        # Clean up partial files on failure
        cleanup_files = [
            video_path,
            audio_path,
            f"temp/{job_id}_with_voiceover.mp4"
        ]
        for file_path in cleanup_files:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
    
    finally:
        # Clean up input files
        for file_path in [media_path, audio_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass

# Background resource monitoring
def monitor_resources():
    """Monitor system resources."""
    while True:
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Update stats
            resource_stats["average_cpu"] = (resource_stats["average_cpu"] + cpu_percent) / 2
            
            if memory.percent > resource_stats["peak_memory"] * 100:
                resource_stats["peak_memory"] = memory.percent / 100
            
            # Add warnings for high usage
            if memory.percent > 90:
                warning = f"High memory usage: {memory.percent:.1f}%"
                resource_stats["warnings"].append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "memory_high",
                    "message": warning
                })
                
            # Keep only last 50 warnings
            if len(resource_stats["warnings"]) > 50:
                resource_stats["warnings"] = resource_stats["warnings"][-50:]
                
        except Exception as e:
            logger.error(f"Resource monitoring error: {e}")
        
        time.sleep(10)  # Check every 10 seconds

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('temp', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('jobs', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Start background monitoring
    monitoring_thread = threading.Thread(target=monitor_resources, daemon=True)
    monitoring_thread.start()
    
    # Use port from environment or default to 8080
    port = int(os.environ.get('PORT', 8080))
    
    logger.info("🚀 Starting Unified VideoEditor API")
    logger.info(f"🌐 Port: {port}")
    logger.info(f"⚡ Workers: {optimal_workers}")
    logger.info(f"🎙️ Whisper Model: tiny (fixed)")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    finally:
        executor.shutdown(wait=True)