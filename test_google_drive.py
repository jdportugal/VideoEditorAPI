#!/usr/bin/env python3
"""
Test Google Drive download functionality
"""

import sys
import os
sys.path.append('.')

from app.utils.download_utils import download_file, _convert_google_drive_url, _is_google_drive_url

def test_google_drive_url_conversion():
    """Test Google Drive URL conversion"""
    print("🧪 Testing Google Drive URL conversion...")
    
    test_cases = [
        {
            "name": "Sharing URL",
            "input": "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view?usp=sharing",
            "expected": "https://drive.google.com/uc?export=download&id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        },
        {
            "name": "Open URL",
            "input": "https://drive.google.com/open?id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
            "expected": "https://drive.google.com/uc?export=download&id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        },
        {
            "name": "Already direct URL",
            "input": "https://drive.google.com/uc?export=download&id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
            "expected": "https://drive.google.com/uc?export=download&id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        },
        {
            "name": "Non-Google Drive URL",
            "input": "https://example.com/video.mp4",
            "expected": "https://example.com/video.mp4"
        }
    ]
    
    for test in test_cases:
        result = _convert_google_drive_url(test["input"])
        if result == test["expected"]:
            print(f"✅ {test['name']}: PASS")
        else:
            print(f"❌ {test['name']}: FAIL")
            print(f"   Expected: {test['expected']}")
            print(f"   Got:      {result}")

def test_google_drive_detection():
    """Test Google Drive URL detection"""
    print("\n🔍 Testing Google Drive URL detection...")
    
    test_cases = [
        ("https://drive.google.com/file/d/1234/view", True),
        ("https://docs.google.com/document/d/1234", True),
        ("https://googleapis.com/drive/v3/files/1234", True),
        ("https://example.com/video.mp4", False),
        ("https://youtube.com/watch?v=1234", False)
    ]
    
    for url, expected in test_cases:
        result = _is_google_drive_url(url)
        if result == expected:
            print(f"✅ {url}: {'Google Drive' if expected else 'Not Google Drive'}")
        else:
            print(f"❌ {url}: FAIL - Expected {expected}, got {result}")

def test_download_sample():
    """Test downloading a sample file (if available)"""
    print("\n📥 Testing sample download...")
    print("Note: This test requires a valid public Google Drive video file URL")
    print("Skipping actual download test - would require real Google Drive URL")

def main():
    """Run all tests"""
    print("🎬 Google Drive Download Tests")
    print("=" * 40)
    
    test_google_drive_url_conversion()
    test_google_drive_detection()
    test_download_sample()
    
    print("\n" + "=" * 40)
    print("📋 Google Drive URL Formats Supported:")
    print("✅ https://drive.google.com/file/d/FILE_ID/view?usp=sharing")
    print("✅ https://drive.google.com/open?id=FILE_ID")  
    print("✅ https://drive.google.com/uc?export=download&id=FILE_ID")
    print("✅ https://docs.google.com/document/d/FILE_ID")
    
    print("\n📋 Features Added:")
    print("✅ Automatic URL conversion for Google Drive")
    print("✅ Virus scan warning bypass for large files")
    print("✅ Improved content type validation")
    print("✅ Better error handling for Google Drive edge cases")

if __name__ == "__main__":
    main()