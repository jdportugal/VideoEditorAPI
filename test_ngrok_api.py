#!/usr/bin/env python3
"""
Test ShortsCreator API via ngrok tunnel
"""

import requests
import json
import sys

def get_ngrok_url():
    """Get the current ngrok public URL"""
    try:
        response = requests.get('http://localhost:4040/api/tunnels')
        data = response.json()
        
        if data['tunnels']:
            return data['tunnels'][0]['public_url']
        else:
            return None
    except Exception:
        return None

def test_health(base_url):
    """Test the health endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_split_video(base_url):
    """Test the split video endpoint"""
    print("\n✂️ Testing split video endpoint...")
    
    data = {
        "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
        "start_time": 1.0,
        "end_time": 5.0
    }
    
    try:
        response = requests.post(f"{base_url}/split-video", json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Split video job created: {result['job_id']}")
            return result['job_id']
        else:
            print(f"❌ Split video failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Split video error: {str(e)}")
        return None

def check_job_status(base_url, job_id):
    """Check job status"""
    print(f"\n📊 Checking job status: {job_id}")
    try:
        response = requests.get(f"{base_url}/job-status/{job_id}")
        if response.status_code == 200:
            result = response.json()
            status = result['status']
            print(f"📋 Job Status: {status}")
            print(f"📋 Progress: {result.get('progress', 0)}%")
            
            if status == 'completed':
                print("✅ Job completed successfully!")
                if result.get('output_path'):
                    print(f"📁 Output file: {result['output_path']}")
                return True
            elif status == 'failed':
                print(f"❌ Job failed: {result.get('error', 'Unknown error')}")
                return False
            else:
                print(f"⏳ Job still {status}...")
                return None
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status check error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🧪 ShortsCreator ngrok API Test")
    print("=" * 40)
    
    # Get ngrok URL
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("❌ Could not get ngrok URL. Make sure ngrok is running:")
        print("   ./setup_ngrok.sh")
        sys.exit(1)
    
    print(f"🌐 Testing API at: {ngrok_url}")
    
    # Test health
    if not test_health(ngrok_url):
        print("\n❌ Health check failed. API may not be accessible.")
        sys.exit(1)
    
    # Test split video (fastest operation)
    job_id = test_split_video(ngrok_url)
    if not job_id:
        print("\n❌ Could not create test job.")
        sys.exit(1)
    
    # Check initial status
    check_job_status(ngrok_url, job_id)
    
    print(f"\n🎉 Basic ngrok API test completed!")
    print(f"📋 Your API is accessible at: {ngrok_url}")
    print(f"📊 Job ID for monitoring: {job_id}")
    print(f"🔍 Check status: {ngrok_url}/job-status/{job_id}")
    print(f"⬇️  Download when done: {ngrok_url}/download/{job_id}")
    
    print(f"\n📋 Example API calls:")
    print(f"curl {ngrok_url}/health")
    print(f"curl {ngrok_url}/job-status/{job_id}")

if __name__ == "__main__":
    main()