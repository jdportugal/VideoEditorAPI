from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime
import re

from app.services.video_service import VideoService
from app.services.subtitle_service import SubtitleService
from app.services.job_manager import JobManager
from app.utils.download_utils import download_file

app = Flask(__name__)
CORS(app)

# Initialize services
video_service = VideoService()
subtitle_service = SubtitleService()
job_manager = JobManager()

# Thread pool for async processing
executor = ThreadPoolExecutor(max_workers=4)

def parse_time_to_seconds(time_input):
    """
    Convert time format to seconds.
    Supports:
    - Numeric seconds: 5.5 or "5.5"
    - SRT format: "00:00:05,500" or "00:00:05.500"
    - Simple format: "05.5"
    """
    if isinstance(time_input, (int, float)):
        return float(time_input)
    
    if isinstance(time_input, str):
        # Try to parse as float first
        try:
            return float(time_input)
        except ValueError:
            pass
        
        # Parse SRT time format: HH:MM:SS,mmm or HH:MM:SS.mmm
        time_pattern = r'(\d{1,2}):(\d{1,2}):(\d{1,2})[,.](\d{3})'
        match = re.match(time_pattern, time_input.strip())
        
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            milliseconds = int(match.group(4))
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            return total_seconds
        
        # If no pattern matches, raise an error
        raise ValueError(f"Invalid time format: {time_input}")
    
    raise ValueError(f"Unsupported time type: {type(time_input)}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/add-subtitles', methods=['POST'])
def add_subtitles():
    try:
        data = request.get_json()
        
        # Log request info
        print(f"📝 Processing subtitle request")
        
        # Validate required fields
        if not data or 'url' not in data:
            return jsonify({"error": "Missing required field: url"}), 400
        
        # Create job ID
        job_id = str(uuid.uuid4())
        
        # Default settings (simplified)
        default_settings = {
            "language": "en",
            "return_subtitles_file": True,  # Always return subtitle files
            "word_level_mode": "karaoke",   # Default to karaoke mode
            "settings": {
                "font-size": 120,
                "font-family": "Luckiest Guy",
                "line-color": "#FFF4E9", 
                "outline-width": 10,
                "normal-color": "#FFFFFF"      # Used for both normal and highlighting
            }
        }
        
        # Merge with provided settings  
        settings = {**default_settings, **data}
        
        # Merge nested settings properly
        if "settings" in data:
            settings["settings"] = {**default_settings["settings"], **data["settings"]}
        
        # Start async processing
        job_manager.create_job(job_id, "add_subtitles", "pending", settings)
        executor.submit(process_subtitle_job, job_id, settings)
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "Subtitle processing started"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/split-video', methods=['POST'])
def split_video():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['url', 'start_time', 'end_time']
        for field in required_fields:
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
        
        # Create job ID
        job_id = str(uuid.uuid4())
        
        # Update data with parsed times
        processed_data = {
            **data,
            'start_time': start_seconds,
            'end_time': end_seconds
        }
        
        # Start async processing
        job_manager.create_job(job_id, "split_video", "pending", processed_data)
        executor.submit(process_split_job, job_id, processed_data)
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "Video splitting started"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/join-videos', methods=['POST'])
def join_videos():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'urls' not in data or not isinstance(data['urls'], list):
            return jsonify({"error": "Missing required field: urls (must be an array)"}), 400
        
        if len(data['urls']) < 2:
            return jsonify({"error": "At least 2 video URLs are required"}), 400
        
        # Create job ID
        job_id = str(uuid.uuid4())
        
        # Start async processing
        job_manager.create_job(job_id, "join_videos", "pending", data)
        executor.submit(process_join_job, job_id, data)
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "Video joining started"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/add-music', methods=['POST'])
def add_music():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['video_url', 'music_url']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create job ID
        job_id = str(uuid.uuid4())
        
        # Optional settings
        settings = {
            "volume": data.get('volume', 0.5),  # Music volume (0.0 to 1.0)
            "fade_in": data.get('fade_in', 0),  # Fade in duration in seconds
            "fade_out": data.get('fade_out', 0),  # Fade out duration in seconds
            "loop_music": data.get('loop_music', False)  # Loop music to match video length
        }
        
        job_data = {**data, "settings": settings}
        
        # Start async processing
        job_manager.create_job(job_id, "add_music", "pending", job_data)
        executor.submit(process_music_job, job_id, job_data)
        
        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "Music addition started"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/job-status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    try:
        job = job_manager.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        # Return only essential fields with download URLs instead of paths
        simplified_job = {
            "job_id": job.get("job_id"),
            "status": job.get("status"),
            "progress": job.get("progress", 0),
            "error": job.get("error")
        }
        
        # Add download URLs if job is completed
        if job.get("status") == "completed":
            if job.get("output_path"):
                simplified_job["video_download_url"] = f"/download/{job_id}"
            if job.get("subtitle_path"):
                simplified_job["subtitle_download_url"] = f"/download-subtitles/{job_id}"
        
        return jsonify(simplified_job)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            return jsonify({"error": "No subtitle file available - set return_subtitles_file: true in request"}), 404
        
        if not os.path.exists(job['subtitle_path']):
            return jsonify({"error": "Subtitle file not found"}), 404
        
        return send_file(job['subtitle_path'], as_attachment=True, download_name=f"{job_id}_subtitles.srt")
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Async processing functions
def process_subtitle_job(job_id, settings):
    video_path = None
    try:
        job_manager.update_job_status(job_id, "processing")
        
        # Download video
        video_url = settings['url']
        video_path = download_file(video_url, 'temp', f"{job_id}_input.mp4")
        
        # Generate subtitles using Whisper
        subtitle_data = subtitle_service.generate_subtitles(
            video_path, 
            settings['language'],
            settings.get('timing_offset', 0.0)
        )
        
        # Analyze timing for potential issues
        timing_analysis = subtitle_service.analyze_timing_gaps(subtitle_data)
        
        # Create video with subtitles
        output_path = f"temp/{job_id}_output.mp4"
        word_mode = settings.get('word_level_mode', 'off')
        print(f"🎯 Processing with {word_mode} mode")
        
        video_service.add_subtitles_to_video(
            video_path,
            subtitle_data,
            output_path,
            {**settings['settings'], **settings.get('word_level_settings', {})},
            word_mode
        )
        
        # Verify output video was actually created
        if not os.path.exists(output_path):
            raise Exception(f"Video processing failed - output file not created: {output_path}")
        
        # Handle subtitle file return
        result = {"output_path": output_path}
        if settings.get('return_subtitles_file', False):
            subtitle_path = f"temp/{job_id}_subtitles.srt"
            subtitle_service.save_subtitle_file(subtitle_data, subtitle_path)
            result["subtitle_path"] = subtitle_path
        
        job_manager.complete_job(job_id, result)
        
    except Exception as e:
        error_message = f"Error processing subtitles: {str(e)}"
        print(f"Job {job_id} failed: {error_message}")
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
                    print(f"Cleaned up partial file: {file_path}")
                except Exception as cleanup_error:
                    print(f"Warning: Could not cleanup {file_path}: {cleanup_error}")

def process_split_job(job_id, data):
    try:
        job_manager.update_job_status(job_id, "processing")
        
        # Download video
        video_url = data['url']
        video_path = download_file(video_url, 'temp', f"{job_id}_input.mp4")
        
        # Split video
        output_path = f"temp/{job_id}_split.mp4"
        video_service.split_video(
            video_path,
            data['start_time'],
            data['end_time'],
            output_path
        )
        
        job_manager.complete_job(job_id, {"output_path": output_path})
        
    except Exception as e:
        job_manager.fail_job(job_id, str(e))

def process_join_job(job_id, data):
    try:
        job_manager.update_job_status(job_id, "processing")
        
        # Download all videos
        video_paths = []
        for i, url in enumerate(data['urls']):
            video_path = download_file(url, 'temp', f"{job_id}_input_{i}.mp4")
            video_paths.append(video_path)
        
        # Join videos
        output_path = f"temp/{job_id}_joined.mp4"
        video_service.join_videos(video_paths, output_path)
        
        job_manager.complete_job(job_id, {"output_path": output_path})
        
    except Exception as e:
        job_manager.fail_job(job_id, str(e))

def process_music_job(job_id, data):
    try:
        job_manager.update_job_status(job_id, "processing")
        
        # Download video and music
        video_path = download_file(data['video_url'], 'temp', f"{job_id}_video.mp4")
        music_path = download_file(data['music_url'], 'temp', f"{job_id}_music.mp3")
        
        # Add music to video
        output_path = f"temp/{job_id}_with_music.mp4"
        video_service.add_music_to_video(
            video_path,
            music_path,
            output_path,
            data['settings']
        )
        
        job_manager.complete_job(job_id, {"output_path": output_path})
        
    except Exception as e:
        job_manager.fail_job(job_id, str(e))

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('temp', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('jobs', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)