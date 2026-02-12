#!/usr/bin/env python3
"""
Test the fixed fish-eye implementation without border artifacts
"""
import requests
import json

API_BASE = "http://localhost:8080"

def test_fixed_barrel_distortion():
    """Test the corrected barrel distortion without duplication artifacts"""
    
    print("=== Testing Fixed Barrel Distortion (No Border Artifacts) ===")
    print()
    
    # Use a sample video URL
    test_video_url = "https://sample-videos.com/zip/10/mp4/720/mp4-720.mp4"
    
    # Test with corrected parameters that should match the Homer Simpson effect
    test_params = {
        "url": test_video_url,
        "filter_type": "fish-eye",
        "custom_parameters": {
            "distortion_strength": 0.4,      # Moderate barrel distortion
            "zoom_factor": 1.0,              # No zoom
            "circular_crop": False,          # Rectangular frame (no circular crop)
            "vignette_intensity": 0.0,       # No darkening
            "center_x": 0.5,                 # Centered horizontally
            "center_y": 0.5                  # Centered vertically
        }
    }
    
    print("🎬 Testing with corrected parameters:")
    print("   • distortion_strength: 0.4 (moderate barrel effect)")
    print("   • zoom_factor: 1.0 (no zoom)")
    print("   • circular_crop: false (maintains rectangular frame)")
    print("   • vignette_intensity: 0.0 (no edge darkening)")
    print("   • Fixed: BORDER_CONSTANT (eliminates corner duplication)")
    print()
    
    # Make request
    try:
        response = requests.post(f"{API_BASE}/video-filters", json=test_params)
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ Fixed fish-eye job started: {job_id}")
            print(f"🔍 Check status: curl {API_BASE}/job-status/{job_id}")
            print(f"📥 Download when complete: curl {API_BASE}/download/{job_id}")
            print()
            print("🎯 Expected Result:")
            print("   • Rectangular frame maintained")
            print("   • Content curves inward at corners (barrel effect)")
            print("   • NO image duplication or artifacts in corners")
            print("   • Smooth distortion like the Homer Simpson image")
            return job_id
        else:
            print(f"❌ Failed to start job: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    job_id = test_fixed_barrel_distortion()
    
    if job_id:
        print("\n🔧 Key Fixes Applied:")
        print("   • Changed from cv2.BORDER_REFLECT to cv2.BORDER_CONSTANT")
        print("   • Eliminated border mode logic confusion")
        print("   • Uses black borders instead of image reflections")
        print("   • Should now match the smooth barrel effect you expected")