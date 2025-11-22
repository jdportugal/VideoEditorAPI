"""
High-Performance VideoEditor API
Uses all available system resources for maximum processing speed.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import uuid
import os
import time
import psutil
import gc
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Import services
from app.services.job_manager import JobManager
from app.services.performance_subtitle_service import PerformanceSubtitleService
from app.services.optimized_video_service import OptimizedVideoService
from app.config.performance_config import PerformanceConfig
from app.utils.download_utils import download_file

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize performance configuration
perf_config = PerformanceConfig()
print("\n" + "="*60)
print("🚀 HIGH-PERFORMANCE VIDEOEDITOR API")
print("="*60)
perf_config.print_performance_info()

# Initialize services with performance optimizations
job_manager = JobManager()
subtitle_service = PerformanceSubtitleService()
video_service = OptimizedVideoService()

# Performance monitoring
resource_stats = {
    "peak_memory": 0,
    "average_cpu": 0,
    "job_count": 0,
    "warnings": [],
    "performance_mode": "HIGH_PERFORMANCE"
}

# Configure ThreadPoolExecutor with maximum workers
max_workers = perf_config.get_resource_limits()["max_concurrent_jobs"]
executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="PerformanceWorker")

logger.info(f"🚀 Performance mode initialized with {max_workers} concurrent workers")

@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check with performance metrics."""
    memory = psutil.virtual_memory()
    
    # Update peak memory tracking
    current_memory_percent = memory.percent / 100
    if current_memory_percent > resource_stats["peak_memory"]:
        resource_stats["peak_memory"] = current_memory_percent
    
    # Get CPU usage
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "performance_mode": "HIGH_PERFORMANCE",
        "resources": {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
            "workers": max_workers,
            "total_cpu_cores": perf_config.system_info["total_cpu_cores"],
            "physical_cpu_cores": perf_config.system_info["physical_cpu_cores"]
        },
        "performance_stats": {
            "peak_memory": resource_stats["peak_memory"],
            "average_cpu": cpu_percent,  # Real-time CPU
            "job_count": resource_stats["job_count"],
            "warnings": resource_stats["warnings"][-5:],  # Last 5 warnings
            "max_concurrent_jobs": max_workers
        },
        "whisper_model": {
            "status": "loaded" if subtitle_service.current_model else "no_model_loaded",
            "current_model": subtitle_service.current_model_name,
            "recommended_model": perf_config.get_whisper_config()["model"],
            "fp16_enabled": perf_config.get_whisper_config()["fp16"]
        }
    }
    
    return jsonify(health_data)

@app.route('/performance-mode', methods=['POST'])
def set_performance_mode():
    """Set processing mode: optimized, performance, or auto."""
    try:
        data = request.json
        mode = data.get('mode', 'auto').lower()
        
        if mode not in ['optimized', 'performance', 'auto']:
            return jsonify({"error": "Invalid mode. Use 'optimized', 'performance', or 'auto'"}), 400
        
        # Store mode preference
        resource_stats["performance_mode"] = mode.upper()
        
        response = {
            "status": "success",
            "mode": mode.upper(),
            "message": f"Performance mode set to {mode.upper()}",
            "settings": {}
        }
        
        if mode == 'performance':
            response["settings"] = {
                "whisper_model": perf_config.get_whisper_config()["model"],
                "max_workers": max_workers,
                "parallel_chunks": perf_config.get_video_processing_config()["parallel_chunks"],
                "memory_limit": f"{perf_config.get_resource_limits()['max_memory_percent']}%"
            }
        elif mode == 'optimized':
            response["settings"] = {
                "whisper_model": "tiny",
                "max_workers": 2,
                "parallel_chunks": 1,
                "memory_limit": "85%"
            }
        else:  # auto
            available_memory = psutil.virtual_memory().available / (1024**3)
            if available_memory > 4:
                selected_mode = "PERFORMANCE"
            else:
                selected_mode = "OPTIMIZED"
            response["settings"] = {"auto_selected": selected_mode}
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate-subtitles', methods=['POST'])
def generate_subtitles():
    """Generate subtitles for a video and save them by project_id."""
    try:
        data = request.json
        
        if not data or 'url' not in data:
            return jsonify({"error": "Missing required 'url' parameter"}), 400
        
        # Generate job ID and project_id if not provided
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
            "performance_mode": resource_stats.get("performance_mode", "AUTO")
        }
        
        # Create job for subtitle generation
        job_manager.create_job(job_id, "generate_subtitles", "pending", generation_settings)
        
        # Update resource stats
        resource_stats["job_count"] += 1
        
        # Submit subtitle generation job
        future = executor.submit(process_generate_subtitles_job, job_id, generation_settings)
        
        return jsonify({
            "job_id": job_id,
            "project_id": project_id,
            "project_id_generated": project_id != data.get('project_id'),
            "status": "pending",
            "message": "Subtitle generation started",
            "performance_mode": resource_stats["performance_mode"],
            "estimated_workers": max_workers,
            "check_status_url": f"/job-status/{job_id}"
        })
        
    except Exception as e:
        logger.error(f"Error starting subtitle generation job: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/add-subtitles', methods=['POST'])
def add_subtitles():
    """Add subtitles to video using project_id. Generates if not exist."""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "Missing request data"}), 400
        
        # Generate job ID and project_id if not provided
        job_id = str(uuid.uuid4())
        project_id = data.get('project_id', str(uuid.uuid4()))
        
        # Check if subtitles exist for this project
        existing_subtitles = job_manager.get_project_subtitles(project_id)
        
        # If subtitles exist, URL is optional (use stored URL)
        # If subtitles don't exist, URL is required for generation
        if not existing_subtitles and 'url' not in data:
            return jsonify({
                "error": "URL is required when subtitles don't exist for this project",
                "project_id": project_id,
                "project_id_generated": project_id != data.get('project_id')
            }), 400
        
        # Determine URL: use provided URL or stored URL from existing subtitles
        video_url = data.get('url')
        if existing_subtitles and not video_url:
            video_url = existing_subtitles.get('video_url')
            if not video_url:
                return jsonify({"error": "No URL available. Provide URL or ensure project subtitles include video URL"}), 400
        
        # Default settings for video processing
        default_settings = {
            "project_id": project_id,
            "url": video_url,
            "language": data.get("language", "en"),
            "timing_offset": data.get("timing_offset", 0.0),
            "word_level_mode": data.get("word_level_mode", "karaoke"),
            "settings": {
                "font-size": data.get("settings", {}).get("font-size", 120),
                "font-family": data.get("settings", {}).get("font-family", "Luckiest Guy"),
                "line-color": data.get("settings", {}).get("line-color", "#FFF4E9"),
                "outline-color": data.get("settings", {}).get("outline-color", "#000000"),
                "outline-width": data.get("settings", {}).get("outline-width", 10),
                "position": data.get("settings", {}).get("position", "bottom-center"),
                "max-words-per-line": data.get("settings", {}).get("max-words-per-line", 4),
                "normal-color": data.get("settings", {}).get("normal-color", "#FFFFFF"),
                "normal_color": data.get("settings", {}).get("normal_color", "#FFFFFF")
            },
            "performance_mode": resource_stats.get("performance_mode", "AUTO"),
            "has_existing_subtitles": existing_subtitles is not None
        }
        
        # Create job for video processing with subtitles
        job_manager.create_job(job_id, "add_subtitles", "pending", default_settings)
        
        # Update resource stats
        resource_stats["job_count"] += 1
        
        # Submit video processing job
        future = executor.submit(process_add_subtitles_job, job_id, default_settings)
        
        if existing_subtitles:
            url_source = "stored" if not data.get('url') else "provided" 
            status_message = f"Adding existing subtitles to video (using {url_source} URL)"
        else:
            status_message = "Generating and adding subtitles to video"
        
        return jsonify({
            "job_id": job_id,
            "project_id": project_id,
            "project_id_generated": project_id != data.get('project_id'),
            "status": "pending",
            "message": status_message,
            "subtitles_exist": existing_subtitles is not None,
            "video_url": video_url,
            "url_source": "stored" if existing_subtitles and not data.get('url') else "provided",
            "performance_mode": resource_stats["performance_mode"],
            "estimated_workers": max_workers,
            "check_status_url": f"/job-status/{job_id}"
        })
        
    except Exception as e:
        logger.error(f"Error starting add subtitles job: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/job-status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status with performance metrics."""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        # Add system performance info
        memory = psutil.virtual_memory()
        
        response = {
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "error": job.get("error"),
            "status_message": job.get("status_message", "Processing..."),
            "processing_info": job.get("processing_info", {}),
            "system_status": {
                "memory_usage_percent": memory.percent,
                "cpu_cores_available": perf_config.system_info["total_cpu_cores"],
                "performance_mode": resource_stats["performance_mode"],
                "estimated_completion": "High-performance processing active"
            }
        }
        
        # Add output paths if completed
        if job["status"] == "completed":
            response["output_path"] = job.get("output_path")
            response["subtitle_path"] = job.get("subtitle_path")
            
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return jsonify({"error": str(e)}), 500

def process_generate_subtitles_job(job_id, settings):
    """Generate subtitles only and save them by project_id."""
    video_path = None
    start_time = time.time()
    
    try:
        job_manager.update_job_status(job_id, "processing", 10, "🚀 Starting subtitle generation...")
        
        # Download video
        job_manager.update_job_status(job_id, "processing", 15, "📥 Downloading video...")
        video_url = settings['url']
        video_path = download_file(video_url, 'temp', f"{job_id}_input.mp4")
        job_manager.update_job_status(job_id, "processing", 25, "✅ Video download completed")
        
        # Progress callback
        def update_progress(progress, message):
            # Map subtitle generation to 25-90% range
            mapped_progress = 25 + int((progress / 100) * 65)
            job_manager.update_job_status(job_id, "processing", mapped_progress, message)
        
        # Generate subtitles using performance service
        job_manager.update_job_status(job_id, "processing", 30, "🎙️ Generating subtitles...")
        subtitle_data = subtitle_service.generate_subtitles(
            video_path,
            settings['language'],
            settings.get('timing_offset', 0.0),
            progress_callback=update_progress
        )
        
        # Save subtitles for the project
        job_manager.update_job_status(job_id, "processing", 95, "💾 Saving subtitles...")
        subtitle_path = job_manager.save_project_subtitles(
            settings['project_id'], 
            subtitle_data, 
            settings['url']
        )
        
        if not subtitle_path:
            raise Exception("Failed to save project subtitles")
        
        # Update job completion
        processing_time = time.time() - start_time
        job_manager.update_job_status(job_id, "completed", 100, f"✅ Subtitles generated and saved in {processing_time:.1f}s")
        
        # Update job with subtitle path
        job = job_manager.get_job(job_id)
        job['subtitle_path'] = subtitle_path
        job['processing_time'] = processing_time
        job['subtitle_count'] = len(subtitle_data)
        job_manager._save_job(job)
        
        logger.info(f"✅ Subtitle generation completed for project {settings['project_id']} in {processing_time:.1f}s")
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"❌ Subtitle generation failed: {str(e)}"
        logger.error(f"{error_msg} (after {processing_time:.1f}s)")
        job_manager.update_job_status(job_id, "failed", None, error_msg)
        
        # Update job with error
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

def process_add_subtitles_job(job_id, settings):
    """Add subtitles to video, generating them if they don't exist."""
    video_path = None
    start_time = time.time()
    
    try:
        # Check if subtitles exist
        existing_subtitles = job_manager.get_project_subtitles(settings['project_id'])
        
        if existing_subtitles:
            job_manager.update_job_status(job_id, "processing", 10, "📋 Using existing subtitles...")
            subtitle_data = existing_subtitles['subtitle_data']
        else:
            # Generate subtitles first
            job_manager.update_job_status(job_id, "processing", 10, "🎙️ Generating subtitles...")
            
            # Download video for subtitle generation
            video_url = settings['url'] 
            video_path = download_file(video_url, 'temp', f"{job_id}_input.mp4")
            
            # Progress callback for subtitle generation (10-50%)
            def subtitle_progress(progress, message):
                mapped_progress = 10 + int((progress / 100) * 40)
                job_manager.update_job_status(job_id, "processing", mapped_progress, f"🎙️ {message}")
            
            subtitle_data = subtitle_service.generate_subtitles(
                video_path,
                settings['language'],
                settings.get('timing_offset', 0.0),
                progress_callback=subtitle_progress
            )
            
            # Save generated subtitles
            job_manager.save_project_subtitles(settings['project_id'], subtitle_data, settings['url'])
        
        # Process video with subtitles (50-100%)
        job_manager.update_job_status(job_id, "processing", 55, "🎬 Adding subtitles to video...")
        
        # Re-download video if not already available
        if not video_path:
            video_url = settings['url']
            video_path = download_file(video_url, 'temp', f"{job_id}_input.mp4")
        
        # Process video with video service
        video_progress_start = 60
        def video_progress(progress, message):
            mapped_progress = video_progress_start + int((progress / 100) * 35)
            job_manager.update_job_status(job_id, "processing", mapped_progress, f"🎬 {message}")
        
        # Generate output path
        output_path = f"temp/{job_id}_output.mp4"
        
        # Call video service with correct parameters (no progress_callback support)
        result_path = video_service.add_subtitles_to_video(
            video_path,
            subtitle_data,
            output_path,
            settings['settings'],
            settings.get('word_level_mode', 'karaoke')
        )
        
        # Update progress manually since progress_callback not supported
        job_manager.update_job_status(job_id, "processing", 95, "🎬 Video processing completed")
        
        # Complete job
        processing_time = time.time() - start_time
        job_manager.update_job_status(job_id, "completed", 100, f"✅ Video processed with subtitles in {processing_time:.1f}s")
        
        # Update job with output
        job = job_manager.get_job(job_id)
        job['output_path'] = result_path
        job['processing_time'] = processing_time
        job_manager._save_job(job)
        
        logger.info(f"✅ Video processing completed for project {settings['project_id']} in {processing_time:.1f}s")
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"❌ Video processing failed: {str(e)}"
        logger.error(f"{error_msg} (after {processing_time:.1f}s)")
        job_manager.update_job_status(job_id, "failed", None, error_msg)
        
        # Update job with error
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

def process_subtitle_job_performance(job_id, settings):
    """High-performance subtitle processing with all optimizations."""
    video_path = None
    start_time = time.time()
    
    try:
        # Performance mode selection
        mode = settings.get("performance_mode", "AUTO")
        
        # Update job with processing info
        job_manager.update_job_status(job_id, "processing", 10, "🚀 Initializing high-performance processing...")
        
        # Log system state
        memory_before = psutil.virtual_memory()
        cpu_before = psutil.cpu_percent()
        logger.info(f"🚀 Starting performance job {job_id}")
        logger.info(f"📊 System: {memory_before.percent:.1f}% memory, {cpu_before:.1f}% CPU")
        logger.info(f"⚡ Mode: {mode}, Workers: {max_workers}")
        
        # Download video with progress
        job_manager.update_job_status(job_id, "processing", 15, "📥 Downloading video...")
        video_url = settings['url']
        video_path = download_file(video_url, 'temp', f"{job_id}_input.mp4")
        job_manager.update_job_status(job_id, "processing", 20, "✅ Video download completed")
        
        # Create performance progress callback
        def update_progress(progress, message):
            job_manager.update_job_status(job_id, "processing", progress, message)
        
        # Auto-select service based on performance mode and resources
        if mode in ["PERFORMANCE", "HIGH_PERFORMANCE"] or mode == "AUTO":
            available_memory = psutil.virtual_memory().available / (1024**3)
            if available_memory > 3:  # Use performance mode if enough memory
                logger.info("🚀 Using HIGH-PERFORMANCE subtitle service")
                subtitle_data = subtitle_service.generate_subtitles(
                    video_path,
                    settings['language'],
                    settings.get('timing_offset', 0.0),
                    progress_callback=update_progress
                )
            else:
                logger.info("⚡ Using OPTIMIZED subtitle service (insufficient memory for performance mode)")
                # Fall back to optimized service
                from app.services.optimized_subtitle_service import OptimizedSubtitleService
                fallback_service = OptimizedSubtitleService()
                subtitle_data = fallback_service.generate_subtitles(
                    video_path,
                    settings['language'],
                    settings.get('timing_offset', 0.0),
                    progress_callback=update_progress
                )
        else:
            logger.info("🎯 Using OPTIMIZED subtitle service (user preference)")
            from app.services.optimized_subtitle_service import OptimizedSubtitleService
            fallback_service = OptimizedSubtitleService()
            subtitle_data = subtitle_service.generate_subtitles(
                video_path,
                settings['language'],
                settings.get('timing_offset', 0.0),
                progress_callback=update_progress
            )
        
        job_manager.update_job_status(job_id, "processing", 65, "✅ Subtitle generation completed")
        
        # Video processing with performance optimizations
        job_manager.update_job_status(job_id, "processing", 70, "🎬 Starting video processing...")
        
        output_path = f"temp/{job_id}_output.mp4"
        word_mode = settings.get('word_level_mode', 'off')
        
        result_path = video_service.add_subtitles_to_video(
            video_path,
            subtitle_data,
            output_path,
            {**settings['settings'], **settings.get('word_level_settings', {})},
            word_mode
        )
        
        job_manager.update_job_status(job_id, "processing", 90, "🎬 Video processing completed")
        
        # Verify output
        if not os.path.exists(result_path):
            raise Exception(f"Video processing failed - output file not created: {result_path}")
        
        # Handle subtitle file
        result = {"output_path": result_path}
        
        if settings.get('return_subtitles_file', False):
            subtitle_path = f"temp/{job_id}_subtitles.json"
            import json
            with open(subtitle_path, 'w') as f:
                json.dump(subtitle_data, f, indent=2)
            result["subtitle_path"] = subtitle_path
        
        # Performance metrics
        processing_time = time.time() - start_time
        memory_after = psutil.virtual_memory()
        
        performance_info = {
            "processing_time_seconds": round(processing_time, 2),
            "memory_peak_percent": memory_after.percent,
            "performance_mode": mode,
            "workers_used": max_workers
        }
        
        logger.info(f"🎉 Performance job {job_id} completed in {processing_time:.1f}s")
        logger.info(f"📊 Peak memory: {memory_after.percent:.1f}%, Workers: {max_workers}")
        
        # Complete job
        job_manager.complete_job(job_id, result)
        job_manager.update_job_status(job_id, "completed", 100, f"🎉 Completed in {processing_time:.1f}s")
        
        # Update performance stats
        job = job_manager.get_job(job_id)
        if job:
            job["processing_info"] = performance_info
            job_manager._save_job(job)
        
    except Exception as e:
        error_message = f"Performance processing failed: {str(e)}"
        logger.error(f"❌ Job {job_id} failed: {error_message}")
        job_manager.update_job_status(job_id, "failed", None, f"❌ {error_message}")
        
        job = job_manager.get_job(job_id)
        if job:
            job["error"] = error_message
            job_manager._save_job(job)
    
    finally:
        # Cleanup
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except:
                pass
        
        # Memory cleanup
        gc.collect()

# Background resource monitoring for performance mode
def monitor_resources_performance():
    """Enhanced resource monitoring for performance mode."""
    while True:
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Update running averages
            resource_stats["average_cpu"] = (resource_stats["average_cpu"] + cpu_percent) / 2
            
            # Track peak memory
            if memory.percent > resource_stats["peak_memory"] * 100:
                resource_stats["peak_memory"] = memory.percent / 100
            
            # Performance mode warnings
            limits = perf_config.get_resource_limits()
            
            if memory.percent > limits["emergency_cleanup_threshold"]:
                warning = f"CRITICAL: Emergency memory cleanup triggered at {memory.percent:.1f}%"
                logger.critical(warning)
                resource_stats["warnings"].append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "memory_critical",
                    "value": memory.percent,
                    "message": warning
                })
                # Emergency cleanup
                subtitle_service._cleanup_memory()
                gc.collect()
                
            elif memory.percent > limits["max_memory_percent"]:
                warning = f"WARNING: High memory usage {memory.percent:.1f}%"
                logger.warning(warning)
                resource_stats["warnings"].append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "memory_warning",
                    "value": memory.percent,
                    "message": warning
                })
            
            # Keep only last 100 warnings
            if len(resource_stats["warnings"]) > 100:
                resource_stats["warnings"] = resource_stats["warnings"][-100:]
                
        except Exception as e:
            logger.error(f"Resource monitoring error: {e}")
        
        time.sleep(5)  # Check every 5 seconds

@app.route('/download/<job_id>', methods=['GET'])
def download_result(job_id):
    """Download the completed video file."""
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
        logger.error(f"❌ Download error for job {job_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/download-subtitles/<job_id>', methods=['GET'])
def download_subtitles(job_id):
    """Download the subtitle file for a job."""
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
        logger.error(f"❌ Subtitle download error for job {job_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/split-video', methods=['POST'])
def split_video():
    """High-performance video splitting."""
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
        memory_threshold = perf_config.get_resource_limits()['max_memory_percent']
        
        if memory.percent > memory_threshold:
            logger.warning(f"Processing video split with high memory usage: {memory.percent:.1f}%")
        
        job_id = str(uuid.uuid4())
        
        processed_data = {
            **data,
            'start_time': start_seconds,
            'end_time': end_seconds,
            'performance_mode': resource_stats.get("performance_mode", "AUTO")
        }
        
        job_manager.create_job(job_id, "split_video", "pending", processed_data)
        
        # Update resource stats
        resource_stats["job_count"] += 1
        
        # Submit high-performance splitting job
        future = executor.submit(process_split_job_performance, job_id, processed_data)
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "High-performance video splitting started",
            "performance_mode": resource_stats["performance_mode"],
            "estimated_workers": max_workers,
            "check_status_url": f"/job-status/{job_id}"
        })
        
    except Exception as e:
        logger.error(f"Error in split_video: {e}")
        return jsonify({"error": str(e)}), 500

def parse_time_to_seconds(time_input):
    """Parse various time formats to seconds."""
    import re
    
    if isinstance(time_input, (int, float)):
        return float(time_input)
    
    if isinstance(time_input, str):
        time_input = time_input.strip()
        
        # Handle MM:SS format (e.g., "1:30")
        if re.match(r'^\d{1,2}:\d{2}$', time_input):
            minutes, seconds = map(int, time_input.split(':'))
            return minutes * 60 + seconds
        
        # Handle HH:MM:SS format (e.g., "1:30:45")
        if re.match(r'^\d{1,2}:\d{2}:\d{2}$', time_input):
            hours, minutes, seconds = map(int, time_input.split(':'))
            return hours * 3600 + minutes * 60 + seconds
        
        # Handle HH:MM:SS.mmm format (e.g., "1:30:45.500")
        if re.match(r'^\d{1,2}:\d{2}:\d{2}\.\d+$', time_input):
            time_part, milliseconds_part = time_input.split('.')
            hours, minutes, seconds = map(int, time_part.split(':'))
            milliseconds = int(milliseconds_part.ljust(3, '0')[:3])
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            return total_seconds
        
        # Handle HH:MM:SS:FF format (e.g., "00:00:00:00", "1:30:45:12") - timecode with frames
        if re.match(r'^\d{1,2}:\d{2}:\d{2}:\d+$', time_input):
            hours, minutes, seconds, frames = map(int, time_input.split(':'))
            # Convert frames to additional seconds (assuming 30fps, common for video)
            frame_seconds = frames / 30.0 if frames > 0 else 0
            total_seconds = hours * 3600 + minutes * 60 + seconds + frame_seconds
            return total_seconds
        
        # Try to parse as float
        try:
            return float(time_input)
        except ValueError:
            pass
            
        raise ValueError(f"Invalid time format: {time_input}")
    
    raise ValueError(f"Unsupported time type: {type(time_input)}")

def process_split_job_performance(job_id, data):
    """High-performance video splitting."""
    video_path = None
    start_time = time.time()
    
    try:
        job_manager.update_job_status(job_id, "processing", 10, "🚀 Starting high-performance video splitting...")
        
        # Get video path
        if 'url' in data:
            job_manager.update_job_status(job_id, "processing", 15, "📥 Downloading video...")
            video_url = data['url']
            video_path = download_file(video_url, 'temp', f"{job_id}_input.mp4")
            job_manager.update_job_status(job_id, "processing", 30, "✅ Video download completed")
        elif 'job_id' in data:
            job_manager.update_job_status(job_id, "processing", 20, "🔍 Using existing video...")
            previous_job = job_manager.get_job(data['job_id'])
            if not previous_job or previous_job['status'] != 'completed':
                raise Exception(f"Previous job not completed: {data['job_id']}")
            
            video_path = previous_job.get('output_path')
            if not video_path or not os.path.exists(video_path):
                raise Exception(f"Previous job output file not found: {video_path}")
            
            job_manager.update_job_status(job_id, "processing", 30, "✅ Video located")
        
        # Progress callback for video splitting
        def split_progress(progress, message):
            # Map splitting progress to 30-95% range
            mapped_progress = 30 + int((progress / 100) * 65)
            job_manager.update_job_status(job_id, "processing", mapped_progress, f"✂️ {message}")
        
        job_manager.update_job_status(job_id, "processing", 35, "✂️ Starting video splitting...")
        
        # Split video with optimized service
        output_path = f"temp/{job_id}_split.mp4"
        video_service.split_video(
            video_path,
            data['start_time'],
            data['end_time'],
            output_path
        )
        
        job_manager.update_job_status(job_id, "processing", 95, "✅ Video splitting completed")
        
        # Verify output
        if not os.path.exists(output_path):
            raise Exception(f"Split failed - output file not created: {output_path}")
        
        processing_time = time.time() - start_time
        job_manager.update_job_status(job_id, "completed", 100, f"✅ Video split completed in {processing_time:.1f}s")
        
        # Update job with results
        job = job_manager.get_job(job_id)
        job['output_path'] = output_path
        job['processing_time'] = processing_time
        job['split_info'] = {
            "start_time": data['start_time'],
            "end_time": data['end_time'],
            "duration": data['end_time'] - data['start_time']
        }
        job_manager._save_job(job)
        
        logger.info(f"✅ Split job {job_id} completed in {processing_time:.1f}s")
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"❌ Video splitting failed: {str(e)}"
        logger.error(f"{error_msg} (after {processing_time:.1f}s)")
        job_manager.update_job_status(job_id, "failed", None, error_msg)
        
        # Update job with error
        job = job_manager.get_job(job_id)
        if job:
            job['error'] = str(e)
            job['processing_time'] = processing_time
            job_manager._save_job(job)
    
    finally:
        # Cleanup downloaded video if it was downloaded for this job
        if 'url' in data and video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except:
                pass

# Start background monitoring
monitoring_thread = threading.Thread(target=monitor_resources_performance, daemon=True)
monitoring_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    
    logger.info("🚀 Starting HIGH-PERFORMANCE VideoEditor API")
    logger.info(f"🌐 Port: {port}")
    logger.info(f"⚡ Max workers: {max_workers}")
    logger.info(f"🧠 Total memory: {perf_config.system_info['total_memory_gb']:.1f}GB")
    logger.info(f"💻 CPU cores: {perf_config.system_info['total_cpu_cores']}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )