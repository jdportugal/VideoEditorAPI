#!/usr/bin/env python3
"""
Test the new Times Bold Italic font for dramatic text styling
"""
import requests
import json

API_BASE = "http://localhost:8080"

def test_times_bold_italic_font():
    """Test the new Times Bold Italic font similar to the image"""
    
    print("=== Testing New Times Bold Italic Font ===")
    print()
    
    # Use a sample video URL
    test_video_url = "https://sample-videos.com/zip/10/mp4/720/mp4-720.mp4"
    
    # Test with the new dramatic serif font
    test_params = {
        "url": test_video_url,
        "subtitle_mode": "popup",
        "font-family": "Times Bold Italic",   # New dramatic serif font
        "font-size": 70,                      # Slightly smaller for readability
        "line-color": "#FFFFFF",              # White text
        "outline-color": "#000000",           # Black outline
        "outline-width": 4,                   # Thick outline for contrast
        "position": "center-bottom"           # Bottom center positioning
    }
    
    print("🎬 Testing with new Times Bold Italic font:")
    print("   • Font: Times Bold Italic (bold italic serif)")
    print("   • Style: Editorial/magazine look like the image")
    print("   • Size: 70px for readability")
    print("   • Colors: White text with black outline")
    print("   • Position: Bottom center")
    print()
    
    # Make request
    try:
        response = requests.post(f"{API_BASE}/add-subtitles", json=test_params)
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ Font test job started: {job_id}")
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

def test_impact_font():
    """Test the Impact font for strong text"""
    
    print("\n=== Testing Impact Font ===")
    print()
    
    test_video_url = "https://sample-videos.com/zip/10/mp4/720/mp4-720.mp4"
    
    test_params = {
        "url": test_video_url,
        "subtitle_mode": "popup",
        "font-family": "Impact",              # Bold condensed sans-serif
        "font-size": 80,                      # Larger size for impact
        "line-color": "#FFFF00",              # Yellow text
        "outline-color": "#000000",           # Black outline
        "outline-width": 5,                   # Extra thick outline
        "position": "center-center"           # Center positioning
    }
    
    print("🎬 Testing with Impact font:")
    print("   • Font: Impact (bold condensed sans-serif)")
    print("   • Style: Strong impact text")
    print("   • Size: 80px for maximum impact")
    print("   • Colors: Yellow text with thick black outline")
    print()
    
    try:
        response = requests.post(f"{API_BASE}/add-subtitles", json=test_params)
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ Impact font test started: {job_id}")
            return job_id
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def show_font_usage_examples():
    """Show usage examples for the new fonts"""
    
    print("\n📖 Font Usage Examples:")
    print()
    
    print("1. Times Bold Italic (Editorial Style):")
    print('   curl -X POST http://localhost:8080/add-subtitles \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"url": "video-url", "font-family": "Times Bold Italic"}\'')
    print()
    
    print("2. Impact (Strong Headlines):")
    print('   curl -X POST http://localhost:8080/add-subtitles \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"url": "video-url", "font-family": "Impact", "font-size": 90}\'')
    print()
    
    print("3. Available Fonts:")
    print("   • 'Luckiest Guy' - Fun decorative")
    print("   • 'Times Bold Italic' - Dramatic serif (like your image)")
    print("   • 'Impact' - Bold condensed sans-serif")
    print("   • 'DejaVu-Sans-Bold' - Default fallback")

if __name__ == "__main__":
    job1 = test_times_bold_italic_font()
    job2 = test_impact_font()
    show_font_usage_examples()
    
    if job1 and job2:
        print(f"\n🎯 Font Comparison:")
        print(f"   Times Bold Italic: {job1}")
        print(f"   Impact: {job2}")
        print("\nBoth fonts are now available for subtitle styling!")