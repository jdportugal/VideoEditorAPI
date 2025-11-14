#!/usr/bin/env python3
"""
ShortsCreator Setup and Validation Script
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8+"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} OK")
    return True

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print("🎬 Checking FFmpeg...")
    if shutil.which('ffmpeg') is None:
        print("❌ FFmpeg not found. Install with:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu: sudo apt-get install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/")
        return False
    print("✅ FFmpeg found")
    return True

def check_docker():
    """Check if Docker is installed"""
    print("🐳 Checking Docker...")
    if shutil.which('docker') is None:
        print("⚠️ Docker not found (optional for containerized deployment)")
        return False
    print("✅ Docker found")
    return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = ['temp', 'uploads', 'jobs', 'static']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ {directory}/ created")

def create_virtual_environment():
    """Create Python virtual environment"""
    print("🔧 Setting up virtual environment...")
    if not Path('venv').exists():
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    
    # Determine the correct pip path
    if os.name == 'nt':  # Windows
        pip_path = 'venv/Scripts/pip'
        python_path = 'venv/Scripts/python'
    else:  # Unix/Linux/macOS
        pip_path = 'venv/bin/pip'
        python_path = 'venv/bin/python'
    
    try:
        # Upgrade pip
        subprocess.run([python_path, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      check=True, capture_output=True)
        
        # Install requirements
        subprocess.run([pip_path, 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def validate_project_structure():
    """Validate project structure"""
    print("🔍 Validating project structure...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        'app/services/video_service.py',
        'app/services/subtitle_service.py',
        'app/services/job_manager.py',
        'app/utils/download_utils.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    print("✅ Project structure valid")
    return True

def run_basic_tests():
    """Run basic import tests"""
    print("🧪 Running basic tests...")
    
    # Determine the correct python path
    if os.name == 'nt':  # Windows
        python_path = 'venv/Scripts/python'
    else:  # Unix/Linux/macOS
        python_path = 'venv/bin/python'
    
    test_code = """
import sys
sys.path.insert(0, '.')

try:
    from app.services.video_service import VideoService
    from app.services.subtitle_service import SubtitleService
    from app.services.job_manager import JobManager
    from app.utils.download_utils import download_file
    import flask
    import moviepy
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
"""
    
    try:
        result = subprocess.run([python_path, '-c', test_code], 
                              capture_output=True, text=True, check=True)
        print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Test failed: {e.stderr}")
        return False

def show_next_steps():
    """Show next steps after successful setup"""
    print("\n🎉 Setup Complete!")
    print("=" * 50)
    print("Next steps:")
    print("")
    print("1. Start the API server:")
    print("   ./start.sh")
    print("   OR manually:")
    print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
    print("   python app.py")
    print("")
    print("2. Test the API:")
    print("   python test_api.py")
    print("")
    print("3. View examples:")
    print("   python examples.py")
    print("")
    print("4. Docker deployment:")
    print("   docker-compose up --build")
    print("   OR")
    print("   ./deploy.sh")
    print("")
    print("🌐 API will be available at: http://localhost:5000")
    print("📋 Health check: http://localhost:5000/health")

def main():
    """Run setup process"""
    print("🎬 ShortsCreator Setup")
    print("=" * 30)
    
    checks_passed = True
    
    # Run checks
    if not check_python_version():
        checks_passed = False
    
    if not check_ffmpeg():
        checks_passed = False
    
    check_docker()  # Optional
    
    if not validate_project_structure():
        checks_passed = False
    
    if not checks_passed:
        print("\n❌ Setup failed. Please fix the issues above.")
        return 1
    
    # Setup steps
    create_directories()
    create_virtual_environment()
    
    if not install_dependencies():
        print("\n❌ Failed to install dependencies.")
        return 1
    
    if not run_basic_tests():
        print("\n❌ Basic tests failed.")
        return 1
    
    show_next_steps()
    return 0

if __name__ == "__main__":
    sys.exit(main())