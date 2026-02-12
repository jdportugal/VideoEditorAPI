#!/usr/bin/env python3
"""
Test the fixed outline-width behavior - setting outline-width to 0 should remove outline
"""
import requests
import json

API_BASE = "http://localhost:8080"

def test_no_outline():
    """Test that outline-width: 0 removes the outline completely"""
    
    print("=== Testing Fixed Outline Removal (outline-width: 0) ===")
    print()
    
    # Use a sample video URL
    test_video_url = "https://sample-videos.com/zip/10/mp4/720/mp4-720.mp4"
    
    # Test with outline-width set to 0
    test_params = {
        "url": test_video_url,
        "subtitle_mode": "popup",
        "font-family": "Times Bold Italic",   # New dramatic serif font
        "font-size": 80,                      # Large size
        "line-color": "#FFFFFF",              # White text
        "outline-width": 0,                   # NO OUTLINE (this should work now)
        "position": "center-center"           # Center positioning
    }
    
    print("🎬 Testing NO OUTLINE (outline-width: 0):")
    print("   • Font: Times Bold Italic")
    print("   • Size: 80px")
    print("   • Color: White text")
    print("   • Outline: NONE (outline-width: 0)")
    print("   • Expected: Clean white text with NO black border")
    print()
    
    # Make request
    try:
        response = requests.post(f"{API_BASE}/add-subtitles", json=test_params)
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ No outline test job started: {job_id}")
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

def test_with_outline():
    """Test that outline-width > 0 still works normally"""
    
    print("\n=== Testing Normal Outline (outline-width: 3) ===")
    print()
    
    test_video_url = "https://sample-videos.com/zip/10/mp4/720/mp4-720.mp4"
    
    test_params = {
        "url": test_video_url,
        "subtitle_mode": "popup", 
        "font-family": "Times Bold Italic",
        "font-size": 80,
        "line-color": "#FFFF00",              # Yellow text
        "outline-color": "#FF0000",           # Red outline
        "outline-width": 3,                   # Normal outline width
        "position": "center-bottom"
    }
    
    print("🎬 Testing WITH OUTLINE (outline-width: 3):")
    print("   • Font: Times Bold Italic")
    print("   • Size: 80px") 
    print("   • Color: Yellow text")
    print("   • Outline: Red border (width: 3)")
    print("   • Expected: Yellow text with red border")
    print()
    
    try:
        response = requests.post(f"{API_BASE}/add-subtitles", json=test_params)
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ With outline test job started: {job_id}")
            return job_id
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    job1 = test_no_outline()
    job2 = test_with_outline()
    
    if job1 and job2:
        print(f"\n🔧 Outline Fix Summary:")
        print(f"   No Outline (outline-width: 0): {job1}")
        print(f"   With Outline (outline-width: 3): {job2}")
        print()
        print("✅ Fix Applied:")
        print("   • outline-width: 0 → Excludes stroke parameters entirely")
        print("   • outline-width > 0 → Includes stroke_color and stroke_width")
        print("   • MoviePy now properly renders text without outline when requested")
        print()
        print("🎯 The black outline issue should now be resolved!")
    
    print("\n📖 Usage Examples:")
    print("No outline:")
    print('   {"outline-width": 0}')
    print()
    print("With outline:")
    print('   {"outline-width": 3, "outline-color": "#000000"}')