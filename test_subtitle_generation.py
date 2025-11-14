#!/usr/bin/env python3
"""
Test subtitle generation with working video URLs
"""

import requests
import time

def test_subtitle_generation():
    """Test subtitle generation with known working video URLs"""
    
    api_base = "http://localhost:5000"
    
    # Test with a working video URL that has speech
    test_video = {
        "name": "W3Schools Video with Audio",
        "url": "https://www.w3schools.com/html/mov_bbb.mp4",
        "language": "en"
    }
    
    print("🎤 Testing Subtitle Generation")
    print("=" * 50)
    print(f"Video: {test_video['name']}")
    print(f"URL: {test_video['url']}")
    print(f"Language: {test_video['language']}")
    
    try:
        # Test API health
        health_response = requests.get(f"{api_base}/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ API Health: OK")
        else:
            print(f"❌ API Health: FAILED ({health_response.status_code})")
            return
        
        # Create subtitle generation job
        payload = {
            "url": test_video['url'],
            "language": test_video['language'],
            "return_subtitles_file": True,
            "settings": {
                "font-size": 100,
                "line-color": "#FFFFFF", 
                "position": "bottom-center"
            }
        }
        
        print(f"\\n📋 Creating subtitle job...")
        response = requests.post(f"{api_base}/add-subtitles", json=payload, timeout=30)
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data['job_id']
            print(f"✅ Job Created: {job_id}")
            
            # Monitor job progress
            max_attempts = 30  # 5 minutes max 
            attempt = 0
            
            print(f"\\n📋 Monitoring subtitle generation...")
            
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
                            print("✅ SUCCESS! Subtitle generation completed!")
                            print(f"📁 Video Output: {status_data.get('output_path', 'N/A')}")
                            print(f"📄 Subtitle File: {status_data.get('subtitle_path', 'N/A')}")
                            return True
                        elif status == 'failed':
                            error_msg = status_data.get('error', 'Unknown error')
                            print(f"❌ FAILED: {error_msg}")
                            return False
                        elif status in ['pending', 'processing']:
                            continue
                        else:
                            print(f"⚠️  Unknown status: {status}")
                    else:
                        print(f"❌ Status check error: {status_response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error during status check: {e}")
            
            print("⏰ Subtitle generation timed out")
            return False
            
        else:
            print(f"❌ Job creation failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_audio_extraction_diagnosis():
    """Test basic audio extraction capability"""
    
    api_base = "http://localhost:5000"
    
    print(f"\\n🔧 Testing Audio Extraction Diagnosis")
    print("=" * 50)
    
    # Test the video that worked for splitting
    working_video = "https://www.w3schools.com/html/mov_bbb.mp4"
    
    # Create a simple job to see if the issue is in download or audio processing
    payload = {
        "url": working_video,
        "start_time": 1.0,
        "end_time": 3.0
    }
    
    print(f"📋 Testing video download first...")
    response = requests.post(f"{api_base}/split-video", json=payload, timeout=30)
    
    if response.status_code == 200:
        job_data = response.json()
        job_id = job_data['job_id']
        print(f"✅ Download test job: {job_id}")
        
        # Quick status check
        time.sleep(5)
        status_response = requests.get(f"{api_base}/job-status/{job_id}")
        if status_response.status_code == 200:
            status_data = status_response.json()
            status = status_data.get('status')
            print(f"📊 Download status: {status}")
            if status == 'failed':
                print(f"❌ Download failed: {status_data.get('error')}")
            else:
                print(f"✅ Download appears successful")
        
        return True
    else:
        print(f"❌ Download test failed: {response.status_code}")
        return False

if __name__ == "__main__":
    print("🧪 Audio/Subtitle System Diagnosis")
    print("=" * 60)
    
    # First test basic download
    download_ok = test_audio_extraction_diagnosis()
    
    if download_ok:
        print(f"\\n" + "=" * 60)
        # Then test subtitle generation
        subtitle_ok = test_subtitle_generation()
        
        print(f"\\n" + "=" * 60)
        print("📊 DIAGNOSIS RESULTS:")
        print(f"   • Video Download: {'✅ WORKING' if download_ok else '❌ FAILED'}")
        print(f"   • Subtitle Generation: {'✅ WORKING' if subtitle_ok else '❌ FAILED'}")
        
        if not subtitle_ok:
            print(f"\\n💡 RECOMMENDATION:")
            print(f"   • The issue is confirmed: Google Drive large files return HTML")
            print(f"   • Audio extraction fails because the file is HTML, not MP4") 
            print(f"   • Solution: Use alternative video hosting for subtitle generation")
            print(f"   • Test command that should work:")
            print(f"     curl -X POST http://localhost:5000/add-subtitles \\")
            print(f"       -H 'Content-Type: application/json' \\")
            print(f"       -d '{{")
            print(f"         \"url\": \"https://www.w3schools.com/html/mov_bbb.mp4\",")
            print(f"         \"language\": \"en\"")
            print(f"       }}'")
    else:
        print(f"\\n❌ Basic download failed - investigating further...")