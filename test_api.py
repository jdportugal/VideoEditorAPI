#!/usr/bin/env python3
"""
Simple test script for the ShortsCreator API
"""

import requests
import time
import json

# API base URL
BASE_URL = "http://localhost:5000"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_add_subtitles():
    """Test the add subtitles endpoint"""
    print("\n🎬 Testing add subtitles endpoint...")
    
    # Example request data
    data = {
        "language": "en",
        "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",  # Sample video URL
        "return_subtitles_file": True,
        "settings": {
            "style": "classic",
            "box-color": "#000000",
            "outline-width": 10,
            "word-color": "#002F6C",
            "shadow-offset": 0,
            "shadow-color": "#000000",
            "max-words-per-line": 4,
            "font-size": 100,
            "font-family": "Arial-Bold",
            "position": "center-center",
            "outline-color": "#000000",
            "line-color": "#FFF4E9"
        }
    }
    
    response = requests.post(f"{BASE_URL}/add-subtitles", json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Job ID: {result['job_id']}")
        return result['job_id']
    else:
        print(f"Error: {response.text}")
        return None

def test_split_video():
    """Test the split video endpoint"""
    print("\n✂️ Testing split video endpoint...")
    
    data = {
        "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
        "start_time": 2.0,
        "end_time": 8.0
    }
    
    response = requests.post(f"{BASE_URL}/split-video", json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Job ID: {result['job_id']}")
        return result['job_id']
    else:
        print(f"Error: {response.text}")
        return None

def test_join_videos():
    """Test the join videos endpoint"""
    print("\n🔗 Testing join videos endpoint...")
    
    data = {
        "urls": [
            "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
            "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
        ]
    }
    
    response = requests.post(f"{BASE_URL}/join-videos", json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Job ID: {result['job_id']}")
        return result['job_id']
    else:
        print(f"Error: {response.text}")
        return None

def check_job_status(job_id):
    """Check job status"""
    print(f"\n📊 Checking job status: {job_id}")
    
    max_attempts = 30  # Wait up to 5 minutes
    attempt = 0
    
    while attempt < max_attempts:
        response = requests.get(f"{BASE_URL}/job-status/{job_id}")
        
        if response.status_code == 200:
            result = response.json()
            status = result['status']
            progress = result.get('progress', 0)
            
            print(f"Status: {status}, Progress: {progress}%")
            
            if status == "completed":
                print("✅ Job completed successfully!")
                return True
            elif status == "failed":
                print(f"❌ Job failed: {result.get('error', 'Unknown error')}")
                return False
            else:
                print(f"⏳ Job still processing... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(10)
        else:
            print(f"Error checking status: {response.text}")
            return False
        
        attempt += 1
    
    print("⏰ Timeout waiting for job completion")
    return False

def main():
    """Run all tests"""
    print("🚀 Starting API tests...\n")
    
    # Test health endpoint
    if not test_health():
        print("❌ Health check failed. Make sure the API is running.")
        return
    
    # Test endpoints
    job_ids = []
    
    # Test split video (fastest operation)
    job_id = test_split_video()
    if job_id:
        job_ids.append(("split_video", job_id))
    
    # Test join videos
    job_id = test_join_videos()
    if job_id:
        job_ids.append(("join_videos", job_id))
    
    # Check job statuses
    for job_type, job_id in job_ids:
        print(f"\n{'='*50}")
        print(f"Monitoring {job_type} job...")
        check_job_status(job_id)
    
    print(f"\n{'='*50}")
    print("🎉 API tests completed!")
    print("\nNote: Subtitle generation test is commented out as it requires")
    print("a video with actual speech content for meaningful results.")

if __name__ == "__main__":
    main()