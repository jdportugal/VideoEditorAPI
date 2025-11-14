#!/usr/bin/env python3
"""
ShortsCreator API Usage Examples
"""

import requests
import time
import json

BASE_URL = "http://localhost:5000"

def example_add_subtitles():
    """Example: Add subtitles to a video with custom styling"""
    print("📝 Example: Adding subtitles with custom styling...")
    
    data = {
        "language": "en",
        "url": "https://your-video-url.com/video.mp4",
        "return_subtitles_file": True,
        "settings": {
            "style": "classic",
            "box-color": "#000000",
            "outline-width": 8,
            "word-color": "#FFFFFF",
            "shadow-offset": 2,
            "shadow-color": "#000000",
            "max-words-per-line": 3,
            "font-size": 120,
            "font-family": "Arial-Bold",
            "position": "bottom-center",
            "outline-color": "#000000",
            "line-color": "#FFFF00"
        }
    }
    
    print(f"Request: POST {BASE_URL}/add-subtitles")
    print(f"Data: {json.dumps(data, indent=2)}")

def example_split_video():
    """Example: Split a video from 10s to 30s"""
    print("\n✂️ Example: Splitting video...")
    
    data = {
        "url": "https://your-video-url.com/long-video.mp4",
        "start_time": 10.5,  # Start at 10.5 seconds
        "end_time": 30.0     # End at 30 seconds
    }
    
    print(f"Request: POST {BASE_URL}/split-video")
    print(f"Data: {json.dumps(data, indent=2)}")

def example_join_videos():
    """Example: Join multiple videos"""
    print("\n🔗 Example: Joining multiple videos...")
    
    data = {
        "urls": [
            "https://your-video-url.com/intro.mp4",
            "https://your-video-url.com/main-content.mp4",
            "https://your-video-url.com/outro.mp4"
        ]
    }
    
    print(f"Request: POST {BASE_URL}/join-videos")
    print(f"Data: {json.dumps(data, indent=2)}")

def example_add_music():
    """Example: Add background music with custom settings"""
    print("\n🎵 Example: Adding background music...")
    
    data = {
        "video_url": "https://your-video-url.com/video.mp4",
        "music_url": "https://your-music-url.com/background.mp3",
        "volume": 0.3,      # 30% volume
        "fade_in": 2.0,     # 2-second fade in
        "fade_out": 3.0,    # 3-second fade out
        "loop_music": True  # Loop music to match video length
    }
    
    print(f"Request: POST {BASE_URL}/add-music")
    print(f"Data: {json.dumps(data, indent=2)}")

def example_job_monitoring():
    """Example: Monitor job progress"""
    print("\n📊 Example: Monitoring job progress...")
    
    job_id = "example-job-id-here"
    
    print(f"Request: GET {BASE_URL}/job-status/{job_id}")
    print("Response example:")
    
    example_response = {
        "job_id": job_id,
        "job_type": "add_subtitles",
        "status": "completed",
        "created_at": "2024-01-01T12:00:00",
        "updated_at": "2024-01-01T12:02:30",
        "progress": 100,
        "output_path": f"temp/{job_id}_output.mp4",
        "subtitle_path": f"temp/{job_id}_subtitles.srt",
        "error": None
    }
    
    print(json.dumps(example_response, indent=2))

def example_download_result():
    """Example: Download processed file"""
    print("\n⬇️ Example: Downloading result...")
    
    job_id = "example-job-id-here"
    print(f"Request: GET {BASE_URL}/download/{job_id}")
    print("This will download the processed video file")

def show_curl_examples():
    """Show cURL examples for testing"""
    print("\n🔧 cURL Examples for Testing:")
    print("-" * 40)
    
    print("\n1. Health Check:")
    print("curl http://localhost:5000/health")
    
    print("\n2. Add Subtitles:")
    print('''curl -X POST http://localhost:5000/add-subtitles \\
  -H "Content-Type: application/json" \\
  -d '{
    "language": "en",
    "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
    "return_subtitles_file": true,
    "settings": {
      "style": "classic",
      "font-size": 100,
      "position": "bottom-center"
    }
  }' ''')
    
    print("\n3. Split Video:")
    print('''curl -X POST http://localhost:5000/split-video \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
    "start_time": 2.0,
    "end_time": 8.0
  }' ''')
    
    print("\n4. Check Job Status:")
    print("curl http://localhost:5000/job-status/YOUR-JOB-ID")
    
    print("\n5. Download Result:")
    print("curl -O http://localhost:5000/download/YOUR-JOB-ID")

def main():
    """Display all examples"""
    print("🎬 ShortsCreator API - Usage Examples")
    print("=" * 50)
    
    example_add_subtitles()
    example_split_video()
    example_join_videos()
    example_add_music()
    example_job_monitoring()
    example_download_result()
    show_curl_examples()
    
    print("\n" + "=" * 50)
    print("💡 Tips:")
    print("- All video/audio files are passed via URLs")
    print("- Processing is asynchronous - use job polling")
    print("- Job status files are stored in the 'jobs/' directory")
    print("- Processed files are stored in the 'temp/' directory")
    print("- Run 'python test_api.py' for automated testing")

if __name__ == "__main__":
    main()