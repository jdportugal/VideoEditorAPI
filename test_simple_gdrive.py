#!/usr/bin/env python3
"""
Simple test to trigger Google Drive download and watch logs
"""

import requests

def test_simple_gdrive():
    """Test the API with the specific Google Drive URL"""
    
    google_drive_url = "https://drive.google.com/file/d/1OchuYiLR5BeJ09foC8-1Gh9Op6iOkfDM/view?usp=drive_link"
    api_base = "http://localhost:5000"
    
    print("🧪 Simple Google Drive Test")
    print(f"URL: {google_drive_url}")
    
    split_payload = {
        "url": google_drive_url,
        "start_time": 2.0,
        "end_time": 5.0
    }
    
    print("📋 Sending request...")
    response = requests.post(f"{api_base}/split-video", json=split_payload, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Job ID: {result.get('job_id')}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_simple_gdrive()