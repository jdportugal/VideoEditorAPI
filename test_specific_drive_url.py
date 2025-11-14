#!/usr/bin/env python3
"""
Test the specific failing Google Drive URL
"""

import requests

def test_google_drive_download():
    """Test the specific Google Drive URL that's failing"""
    
    # The problematic URL
    original_url = "https://drive.google.com/file/d/1OchuYiLR5BeJ09foC8-1Gh9Op6iOkfDM/view?usp=drive_link"
    direct_url = "https://drive.google.com/uc?export=download&id=1OchuYiLR5BeJ09foC8-1Gh9Op6iOkfDM"
    confirm_url = "https://drive.google.com/uc?export=download&id=1OchuYiLR5BeJ09foC8-1Gh9Op6iOkfDM&confirm=t"
    
    print("🧪 Testing Google Drive URL Download")
    print("=" * 50)
    
    urls_to_test = [
        ("Original URL", original_url),
        ("Direct URL", direct_url), 
        ("Confirm URL", confirm_url)
    ]
    
    for name, url in urls_to_test:
        print(f"\n📋 Testing {name}:")
        print(f"URL: {url}")
        
        try:
            # Test with HEAD request first
            print("  🔍 Testing with HEAD request...")
            head_response = requests.head(url, allow_redirects=True, timeout=10)
            print(f"  📊 Status: {head_response.status_code}")
            print(f"  📊 Content-Type: {head_response.headers.get('content-type', 'None')}")
            print(f"  📊 Content-Length: {head_response.headers.get('content-length', 'None')}")
            
            # Test with GET request for first few bytes
            print("  📥 Testing with partial GET request...")
            response = requests.get(url, stream=True, timeout=10)
            content_type = response.headers.get('content-type', '').lower()
            
            print(f"  📊 GET Status: {response.status_code}")
            print(f"  📊 GET Content-Type: {content_type}")
            
            # Read first 500 bytes to check content
            first_chunk = next(response.iter_content(chunk_size=500), b'')
            
            if b'<html' in first_chunk.lower() or b'<!doctype' in first_chunk.lower():
                print("  ❌ Content appears to be HTML")
                print(f"  📝 First 200 chars: {first_chunk[:200].decode('utf-8', errors='ignore')}")
            else:
                print("  ✅ Content appears to be binary")
                print(f"  📝 First 50 bytes: {first_chunk[:50]}")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print(f"\n" + "=" * 50)
    print("💡 Recommendations:")
    print("1. Check if the Google Drive file is publicly accessible")
    print("2. Verify the file permissions are set to 'Anyone with the link can view'")
    print("3. Try a different Google Drive file to test the API")

if __name__ == "__main__":
    test_google_drive_download()