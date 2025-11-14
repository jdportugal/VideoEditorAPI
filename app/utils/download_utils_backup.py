import requests
import os
import uuid
import re
from urllib.parse import urlparse
from typing import Optional

class DownloadError(Exception):
    pass

def _is_valid_content_type(content_type: str, file_path: str, is_google_drive: bool = False) -> bool:
    if not content_type:
        return True
    
    content_type = content_type.lower()
    
    video_types = ['video/', 'audio/', 'application/octet-stream']
    
    if any(vtype in content_type for vtype in video_types):
        return True
    
    return False

def _is_google_drive_url(url: str) -> bool:
    """Check if URL is a Google Drive URL."""
    return any(domain in url.lower() for domain in [
        'drive.google.com', 
        'docs.google.com',
        'googleapis.com'
    ])

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

def _convert_google_drive_url(url: str) -> str:
    """Convert Google Drive URL to direct download format"""
    file_id = _extract_google_drive_file_id(url)
    if file_id:
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url

def download_file(url: str, destination_dir: str, filename: Optional[str] = None) -> str:
    """
    Download file from URL with improved Google Drive support
    
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
        
        # Check if this is a Google Drive URL
        is_google_drive = _is_google_drive_url(url)
        
        if is_google_drive:
            print(f"🔍 Google Drive URL detected: {url}")
            url = _convert_google_drive_url(url)
            print(f"🔄 Converted to: {url}")
        
        # Generate filename if not provided
        if not filename:
            parsed_url = urlparse(url)
            url_filename = os.path.basename(parsed_url.path)
            
            if url_filename and '.' in url_filename:
                filename = url_filename
            else:
                # Guess extension based on URL or use default
                if any(keyword in url.lower() for keyword in ['video', 'mp4', 'avi', 'mov']):
                    filename = f"{str(uuid.uuid4())}.mp4"
                else:
                    filename = f"{str(uuid.uuid4())}.mp4"
        
        # Full path for the downloaded file
        file_path = os.path.join(destination_dir, filename)
        
        # Download the file
        print(f"🔽 Downloading: {url}")
        response = requests.get(url, stream=True, timeout=300)
        
        # Debug response info
        print(f"📊 Response status: {response.status_code}")
        content_type = response.headers.get('content-type', 'unknown')
        print(f"📋 Content type: {content_type}")
        content_length = response.headers.get('content-length', 'unknown')
        print(f"📏 Content length: {content_length}")
        
        if response.status_code == 200:
            # For Google Drive, we might get HTML even with 200 status
            # Check the content to see if it's actually the virus scan page
            if is_google_drive and 'text/html' in content_type.lower():
                # Try to extract the actual download link from the HTML
                html_content = response.text
                
                # Look for download confirmation link
                download_link_patterns = [
                    r'href="(/uc\?export=download[^"]*)"',
                    r'"downloadUrl":"([^"]*)"',
                    r'href="(https://drive\.google\.com/uc\?export=download[^"]*)"'
                ]
                
                download_link = None
                for pattern in download_link_patterns:
                    matches = re.findall(pattern, html_content)
                    if matches:
                        download_link = matches[0]
                        if download_link.startswith('/'):
                            download_link = f"https://drive.google.com{download_link}"
                        download_link = download_link.replace('&amp;', '&')
                        print(f"🔗 Found download link: {download_link}")
                        break
                
                if download_link:
                    print(f"🔄 Retrying with extracted link...")
                    response = requests.get(download_link, stream=True, timeout=300)
                    print(f"📊 Retry response status: {response.status_code}")
                    content_type = response.headers.get('content-type', 'unknown')
                    print(f"📋 Retry content type: {content_type}")
        
        response.raise_for_status()
        
        # Check content type for validation (skip validation for Google Drive)
        if is_google_drive:
            print(f"Skipping content type validation for Google Drive file: {content_type}")
        elif not _is_valid_content_type(content_type, file_path, is_google_drive):
            raise DownloadError(f"Invalid content type: {content_type}")
        
        # Save the file
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Verify the downloaded file
        file_size = os.path.getsize(file_path)
        print(f"📦 Downloaded file size: {file_size} bytes")
        
        if file_size < 100:  # File too small, might be an error page
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content_preview = f.read(500)
                print(f"🔍 Small file content preview: {content_preview[:200]}...")
                
                if 'error' in content_preview.lower() or 'html' in content_preview.lower():
                    raise DownloadError(f"Downloaded file appears to be an error page: {content_preview[:100]}...")
        
        return file_path
        
    except requests.exceptions.RequestException as e:
        raise DownloadError(f"Failed to download {url}: {str(e)}")
    except Exception as e:
        raise DownloadError(f"Error downloading file: {str(e)}")

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