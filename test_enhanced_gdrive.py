#!/usr/bin/env python3
"""
Test the enhanced Google Drive download functionality
"""

import requests
import time

def test_api_with_google_drive():
    """Test the API with the specific Google Drive URL"""
    
    # The problematic URL
    google_drive_url = "https://drive.google.com/file/d/1OchuYiLR5BeJ09foC8-1Gh9Op6iOkfDM/view?usp=drive_link"
    
    # API endpoints
    api_base = "http://localhost:5000"
    
    print("🧪 Testing Enhanced Google Drive Download")
    print("=" * 50)
    print(f"Google Drive URL: {google_drive_url}")
    print(f"API Base: {api_base}")
    
    try:
        # Test API health first
        print("\n📋 Checking API health...")
        health_response = requests.get(f"{api_base}/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ API is healthy")
        else:
            print(f"❌ API health check failed: {health_response.status_code}")
            return
        
        # Test video splitting endpoint with Google Drive URL
        print("\n📋 Testing video split with Google Drive URL...")
        
        split_payload = {
            "url": google_drive_url,
            "start_time": 5.0,
            "end_time": 15.0
        }
        
        response = requests.post(f"{api_base}/split-video", json=split_payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ Job created successfully: {job_id}")
            
            # Monitor job progress
            print("\n📋 Monitoring job progress...")
            max_attempts = 30  # 5 minutes max
            attempt = 0
            
            while attempt < max_attempts:
                attempt += 1
                time.sleep(10)  # Check every 10 seconds
                
                try:
                    status_response = requests.get(f"{api_base}/job-status/{job_id}", timeout=10)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        
                        print(f"🔄 Attempt {attempt}: Status = {status}")
                        
                        if status == 'completed':
                            print("✅ SUCCESS! Google Drive download and video processing completed!")
                            print(f"📊 Job Details: {status_data}")
                            break
                        elif status == 'failed':
                            error_msg = status_data.get('error', 'Unknown error')
                            print(f"❌ Job Failed: {error_msg}")
                            break
                        elif status in ['pending', 'processing']:
                            continue
                        else:
                            print(f"⚠️  Unknown status: {status}")
                    else:
                        print(f"❌ Error checking status: {status_response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error during status check: {e}")
            
            if attempt >= max_attempts:
                print("⏰ Job monitoring timed out")
                
        else:
            print(f"❌ Job creation failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Error response: {response.text}")
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_api_with_google_drive()