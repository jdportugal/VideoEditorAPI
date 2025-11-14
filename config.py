import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024))  # 500MB
    
    # Directory configurations
    TEMP_DIR = os.environ.get('TEMP_DIR', 'temp')
    UPLOADS_DIR = os.environ.get('UPLOADS_DIR', 'uploads')
    JOBS_DIR = os.environ.get('JOBS_DIR', 'jobs')
    STATIC_DIR = os.environ.get('STATIC_DIR', 'static')
    
    # Processing configurations
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 4))
    DOWNLOAD_TIMEOUT = int(os.environ.get('DOWNLOAD_TIMEOUT', 300))  # 5 minutes
    
    # Whisper configurations
    WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'base')
    
    # Video processing configurations
    DEFAULT_VIDEO_CODEC = os.environ.get('DEFAULT_VIDEO_CODEC', 'libx264')
    DEFAULT_AUDIO_CODEC = os.environ.get('DEFAULT_AUDIO_CODEC', 'aac')
    
    # Job cleanup
    JOB_CLEANUP_DAYS = int(os.environ.get('JOB_CLEANUP_DAYS', 7))
    TEMP_FILE_CLEANUP_HOURS = int(os.environ.get('TEMP_FILE_CLEANUP_HOURS', 24))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    FLASK_ENV = 'testing'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}