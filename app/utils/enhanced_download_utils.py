import requests
import os
import uuid
import re
import time
from urllib.parse import urlparse, parse_qs
from typing import Optional

class DownloadError(Exception):
    pass

def _extract_google_drive_file_id(url: str) -> Optional[str]:
    """Extract file ID from various Google Drive URL formats"""
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'/d/([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def _is_google_drive_url(url: str) -> bool:
    """Check if URL is a Google Drive URL."""
    return any(domain in url.lower() for domain in [
        'drive.google.com', 
        'docs.google.com',
        'googleapis.com'
    ])

def _download_google_drive_file(file_id: str, destination_path: str) -> bool:
    """
    Enhanced Google Drive download with multiple bypass strategies
    
    Returns:
        True if successful download, False otherwise
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    print(f"🚀 ENHANCED GOOGLE DRIVE DOWNLOAD")
    print(f"🆔 File ID: {file_id}")
    print(f"💾 Destination: {destination_path}")
    
    # Strategy 1: Direct download
    print(f"\\n🔄 STRATEGY 1: Direct download")
    try:
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = session.get(download_url, stream=True, timeout=30)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                print(f"✅ Direct download successful")
                _save_response_to_file(response, destination_path)
                return _verify_download(destination_path)
        print(f"❌ Direct download failed - virus scan detected")
    except Exception as e:
        print(f"❌ Direct download error: {e}")
    
    # Strategy 2: Confirmation token bypass
    print(f"\\n🔄 STRATEGY 2: Confirmation token bypass")
    try:
        scan_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = session.get(scan_url, timeout=30)
        
        if response.status_code == 200:
            # Extract confirmation token from HTML
            confirm_patterns = [
                r'confirm=([a-zA-Z0-9_-]{10,})',
                r'"confirm"\\s*:\\s*"([a-zA-Z0-9_-]+)"',
                r'name="confirm"\\s+value="([^"]+)"',
                r'&amp;confirm=([a-zA-Z0-9_-]+)',
                r'/uc\\?export=download[^"]*&confirm=([a-zA-Z0-9_-]+)',
            ]
            
            confirm_token = None
            for pattern in confirm_patterns:
                matches = re.findall(pattern, response.text)
                if matches:
                    # Get the longest match (usually more specific)
                    confirm_token = max(matches, key=len)
                    print(f"🎟️  Found confirm token: {confirm_token[:15]}...")
                    break
            
            if confirm_token:
                confirmed_url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm={confirm_token}"
                download_response = session.get(confirmed_url, stream=True, timeout=120)
                if download_response.status_code == 200:
                    content_type = download_response.headers.get('content-type', '').lower()
                    if 'text/html' not in content_type:
                        print(f"✅ Confirmation bypass successful")
                        _save_response_to_file(download_response, destination_path)
                        return _verify_download(destination_path)
            
        print(f"❌ Confirmation bypass failed")
    except Exception as e:
        print(f"❌ Confirmation bypass error: {e}")
    
    # Strategy 3: Google UserContent domain
    print(f"\\n🔄 STRATEGY 3: UserContent domain")
    usercontent_urls = [
        f"https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0",
        f"https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0&confirm=t",
    ]
    
    for url in usercontent_urls:
        try:
            print(f"   📡 Trying: {url[:80]}...")
            response = session.get(url, stream=True, timeout=120, allow_redirects=True)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    print(f"✅ UserContent domain successful")
                    _save_response_to_file(response, destination_path)
                    return _verify_download(destination_path)
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"❌ UserContent domain failed")
    
    # Strategy 4: Session-based download
    print(f"\\n🔄 STRATEGY 4: Session-based download")
    try:
        # Visit file page to establish session
        file_url = f"https://drive.google.com/file/d/{file_id}/view"
        session.get(file_url, timeout=30)
        time.sleep(2)  # Wait for session
        
        # Try download with session
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = session.get(download_url, stream=True, timeout=120)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                print(f"✅ Session-based download successful")
                _save_response_to_file(response, destination_path)
                return _verify_download(destination_path)
        
        print(f"❌ Session-based download failed")
    except Exception as e:
        print(f"❌ Session-based download error: {e}")
    
    # Strategy 5: Alternative domains and parameters
    print(f"\\n🔄 STRATEGY 5: Alternative domains")
    alternative_urls = [
        f"https://docs.google.com/uc?export=download&id={file_id}",
        f"https://drive.google.com/u/0/uc?export=download&id={file_id}",
        f"https://drive.google.com/uc?export=download&id={file_id}&resourcekey=0",
        f"https://drive.google.com/uc?id={file_id}&export=download&confirm=t"
    ]
    
    for url in alternative_urls:
        try:
            print(f"   📡 Trying: {url[:80]}...")
            response = session.get(url, stream=True, timeout=120, allow_redirects=True)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    print(f"✅ Alternative domain successful")
                    _save_response_to_file(response, destination_path)
                    return _verify_download(destination_path)
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"❌ Alternative domains failed")
    
    # Strategy 6: Multiple redirects and cookies
    print(f"\\n🔄 STRATEGY 6: Multiple redirects")
    try:
        # Build up cookies by visiting multiple pages
        session.get(f"https://drive.google.com", timeout=30)
        session.get(f"https://drive.google.com/file/d/{file_id}/view", timeout=30)
        session.get(f"https://drive.google.com/uc?id={file_id}", timeout=30)
        
        # Final download attempt
        final_url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"
        response = session.get(final_url, stream=True, timeout=120, allow_redirects=True)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                print(f"✅ Multiple redirects successful")
                _save_response_to_file(response, destination_path)
                return _verify_download(destination_path)
        
        print(f"❌ Multiple redirects failed")
    except Exception as e:
        print(f"❌ Multiple redirects error: {e}")
    
    return False

def _save_response_to_file(response: requests.Response, file_path: str) -> None:
    """Save streaming response to file with progress"""
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"   📥 Downloaded: {percent:.1f}% ({downloaded:,} / {total_size:,} bytes)", end='\\r')
    
    if total_size > 0:
        print(f"   📥 Download complete: {downloaded:,} bytes")

def _verify_download(file_path: str) -> bool:
    """Verify downloaded file is valid (not HTML)"""
    try:
        if not os.path.exists(file_path):
            return False
        
        file_size = os.path.getsize(file_path)
        if file_size < 1000:  # Too small to be a valid video
            return False
        
        # Check if it's HTML content
        with open(file_path, 'rb') as f:
            first_bytes = f.read(1000).lower()
            if b'<html' in first_bytes or b'<!doctype' in first_bytes or b'virus scan warning' in first_bytes:
                print(f"   ❌ Downloaded HTML instead of video content")
                return False
        
        print(f"   ✅ Verified: Valid video file ({file_size:,} bytes)")
        return True
        
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
        return False

def download_file(url: str, destination_dir: str, filename: Optional[str] = None) -> str:
    """
    Enhanced download function with robust Google Drive support
    
    Args:
        url: URL of the file to download
        destination_dir: Directory to save the file
        filename: Optional filename. If not provided, will be generated
        
    Returns:
        Path to the downloaded file
        
    Raises:
        DownloadError: If download fails
    """
    try:
        # Create destination directory if it doesn't exist
        os.makedirs(destination_dir, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            parsed_url = urlparse(url)
            url_filename = os.path.basename(parsed_url.path)
            
            if url_filename and '.' in url_filename:
                filename = url_filename
            else:
                file_extension = _guess_extension_from_url(url)
                filename = f"{str(uuid.uuid4())}{file_extension}"
        
        # Full path for the downloaded file
        file_path = os.path.join(destination_dir, filename)
        
        # Handle Google Drive URLs with enhanced strategies
        if _is_google_drive_url(url):
            print(f"🟢 GOOGLE DRIVE DETECTED: {url}")
            
            file_id = _extract_google_drive_file_id(url)
            if not file_id:
                raise DownloadError("Could not extract file ID from Google Drive URL")
            
            # Use enhanced Google Drive downloader
            success = _download_google_drive_file(file_id, file_path)
            
            if success:
                print(f"✅ ENHANCED GOOGLE DRIVE DOWNLOAD SUCCESSFUL!")
                return file_path
            else:
                raise DownloadError("All Google Drive download strategies failed")
        
        # Handle non-Google Drive URLs (original logic)
        print(f"🔽 DOWNLOADING: {url}")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        _save_response_to_file(response, file_path)
        
        if not _verify_download(file_path):
            raise DownloadError("Downloaded file verification failed")
        
        return file_path
        
    except requests.exceptions.RequestException as e:
        raise DownloadError(f"Failed to download {url}: {str(e)}")
    except Exception as e:
        raise DownloadError(f"Error downloading file: {str(e)}")

def _guess_extension_from_url(url: str) -> str:
    """Guess file extension from URL"""
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
    audio_extensions = ['.mp3', '.wav', '.aac', '.ogg', '.flac', '.m4a']
    
    for ext in video_extensions + audio_extensions:
        if path.endswith(ext):
            return ext
    
    if any(keyword in url.lower() for keyword in ['video', 'mp4', 'avi', 'mov']):
        return '.mp4'
    elif any(keyword in url.lower() for keyword in ['audio', 'music', 'mp3', 'sound']):
        return '.mp3'
    
    return '.mp4'

# Keep existing utility functions for backward compatibility
def cleanup_temp_file(file_path: str) -> bool:
    """Clean up a temporary file."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Cleaned up temporary file: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error cleaning up file {file_path}: {str(e)}")
        return False

def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    try:
        return os.path.getsize(file_path) if os.path.exists(file_path) else 0
    except Exception:
        return 0

def is_valid_url(url: str) -> bool:
    """Check if URL is valid and accessible."""
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        response = requests.head(url, timeout=10)
        return response.status_code < 400
        
    except Exception:
        return False