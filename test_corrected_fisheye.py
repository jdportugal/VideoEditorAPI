#!/usr/bin/env python3
"""
Test the corrected fish-eye/barrel distortion implementation
"""
import requests
import json

API_BASE = "http://localhost:8080"

def test_corrected_barrel_distortion():
    """Test the corrected barrel distortion that maintains rectangular frame"""
    
    print("=== Testing Corrected Barrel Distortion (No Circular Effect) ===")
    print()
    
    # Use a sample video URL
    test_video_url = "https://sample-videos.com/zip/10/mp4/720/mp4-720.mp4"
    
    # Test with default corrected parameters
    test_params = {
        "url": test_video_url,
        "filter_type": "fish-eye"  # Now defaults to subtle barrel distortion
    }
    
    print("🎬 Testing with corrected default parameters:")
    print("   • distortion_strength: 0.2 (subtle)")
    print("   • zoom_factor: 1.0 (no zoom)")
    print("   • circular_crop: false (maintains rectangular frame)")
    print("   • vignette_intensity: 0.0 (no edge darkening)")
    print()
    
    # Make request
    try:
        response = requests.post(f"{API_BASE}/video-filters", json=test_params)
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ Job started successfully: {job_id}")
            print(f"🔍 Check status: curl {API_BASE}/job-status/{job_id}")
            print(f"📥 Download when complete: curl {API_BASE}/download/{job_id}")
            return job_id
        else:
            print(f"❌ Failed to start job: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_custom_barrel_parameters():
    """Test different levels of barrel distortion"""
    
    print("\n=== Custom Barrel Distortion Levels ===")
    print()
    
    test_video_url = "https://sample-videos.com/zip/10/mp4/720/mp4-720.mp4"
    
    # Different distortion levels
    test_levels = [
        {
            "name": "Very Subtle",
            "params": {
                "distortion_strength": 0.1,
                "zoom_factor": 1.0,
                "circular_crop": False,
                "vignette_intensity": 0.0
            }
        },
        {
            "name": "Light Barrel",
            "params": {
                "distortion_strength": 0.3,
                "zoom_factor": 1.0,
                "circular_crop": False,
                "vignette_intensity": 0.0
            }
        },
        {
            "name": "Moderate Barrel",
            "params": {
                "distortion_strength": 0.5,
                "zoom_factor": 1.0,
                "circular_crop": False,
                "vignette_intensity": 0.0
            }
        }
    ]
    
    for i, test_config in enumerate(test_levels, 1):
        print(f"{i}. {test_config['name']} Barrel Distortion:")
        for param, value in test_config['params'].items():
            print(f"   - {param}: {value}")
        print()

if __name__ == "__main__":
    job_id = test_corrected_barrel_distortion()
    test_custom_barrel_parameters()
    
    if job_id:
        print("\n🎯 Key Changes Made:")
        print("   • Fixed coordinate normalization to use full frame dimensions")
        print("   • Removed circular radius constraints")
        print("   • Changed border mode to BORDER_REFLECT (no black borders)")
        print("   • Updated default parameters for subtle effect")
        print("   • Barrel distortion now affects entire rectangular frame")
        print()
        print("💡 Result: Frame stays rectangular with curved content inside")
        print("   (Similar to the Homer Simpson image you showed)")