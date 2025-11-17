import os
import psutil
from dotenv import load_dotenv

load_dotenv()

class OptimizedConfig:
    """Resource-aware configuration for low-memory systems"""
    
    def __init__(self):
        self.system_memory_gb = psutil.virtual_memory().total / (1024**3)
        self.cpu_count = psutil.cpu_count()
        
    def get_optimal_settings(self):
        """
        Return optimal settings based on system resources.
        """
        # Detect resource constraints
        is_low_memory = self.system_memory_gb <= 6  # 6GB or less
        is_low_cpu = self.cpu_count <= 4           # 4 cores or less
        
        print(f"🖥️  System detected: {self.system_memory_gb:.1f}GB RAM, {self.cpu_count} CPU cores")
        
        if is_low_memory and is_low_cpu:
            return self._get_constrained_config()
        elif is_low_memory:
            return self._get_memory_constrained_config()
        elif is_low_cpu:
            return self._get_cpu_constrained_config()
        else:
            return self._get_standard_config()
    
    def _get_constrained_config(self):
        """Configuration for highly resource-constrained systems (4GB RAM, 2 vCPUs)"""
        return {
            # Basic settings
            'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
            'MAX_CONTENT_LENGTH': 200 * 1024 * 1024,  # Reduce to 200MB
            
            # Directory configurations
            'TEMP_DIR': os.environ.get('TEMP_DIR', 'temp'),
            'UPLOADS_DIR': os.environ.get('UPLOADS_DIR', 'uploads'),
            'JOBS_DIR': os.environ.get('JOBS_DIR', 'jobs'),
            'STATIC_DIR': os.environ.get('STATIC_DIR', 'static'),
            
            # Processing configurations
            'MAX_WORKERS': 1,  # Only 1 concurrent job
            'DOWNLOAD_TIMEOUT': 600,  # Longer timeout for slow systems
            
            # Memory management
            'MAX_MEMORY_USAGE_GB': 3.0,  # Leave 1GB for system
            'ENABLE_MEMORY_MONITORING': True,
            'FORCE_CLEANUP_THRESHOLD': 0.8,  # Force cleanup at 80% memory
            
            # Video processing
            'VIDEO_CHUNK_DURATION': 30,  # 30-second chunks
            'DEFAULT_VIDEO_CODEC': 'libx264',
            'DEFAULT_AUDIO_CODEC': 'aac',
            'FFMPEG_PRESET': 'ultrafast',  # Fastest encoding
            'FFMPEG_THREADS': 1,
            'ENABLE_CHUNKED_PROCESSING': True,
            
            # Whisper configurations
            'WHISPER_MODEL': 'tiny',  # Smallest model
            'WHISPER_MAX_MEMORY_GB': 1.0,
            'ENABLE_DYNAMIC_MODEL_SELECTION': True,
            'UNLOAD_MODEL_AFTER_USE': True,
            'ENABLE_AUDIO_CHUNKING': True,
            'AUDIO_CHUNK_DURATION': 180,  # 3-minute chunks
            
            # Subtitle optimizations
            'MAX_SUBTITLE_CLIPS': 50,  # Limit simultaneous clips
            'SUBTITLE_BATCH_SIZE': 10,
            'MAX_FONT_SIZE': 60,  # Smaller fonts for memory
            'MAX_OUTLINE_WIDTH': 3,
            
            # Job cleanup
            'JOB_CLEANUP_DAYS': 1,  # Clean up after 1 day
            'TEMP_FILE_CLEANUP_HOURS': 6,  # Clean temp files every 6 hours
            'AUTO_CLEANUP_ENABLED': True,
            
            # Performance monitoring
            'ENABLE_PERFORMANCE_LOGGING': True,
            'MEMORY_WARNING_THRESHOLD': 0.7,
            'CPU_WARNING_THRESHOLD': 0.9,
            
            # System label
            'SYSTEM_TYPE': 'highly_constrained'
        }
    
    def _get_memory_constrained_config(self):
        """Configuration for memory-constrained systems (4-6GB RAM, 4+ vCPUs)"""
        config = self._get_constrained_config()
        config.update({
            'MAX_WORKERS': 2,  # Can handle 2 jobs with more CPU
            'MAX_CONTENT_LENGTH': 300 * 1024 * 1024,  # 300MB
            'VIDEO_CHUNK_DURATION': 45,  # Slightly larger chunks
            'WHISPER_MODEL': 'base',  # Can use base model
            'WHISPER_MAX_MEMORY_GB': 1.5,
            'FFMPEG_THREADS': 2,
            'SYSTEM_TYPE': 'memory_constrained'
        })
        return config
    
    def _get_cpu_constrained_config(self):
        """Configuration for CPU-constrained systems (8GB+ RAM, 2 vCPUs)"""
        config = self._get_constrained_config()
        config.update({
            'MAX_WORKERS': 1,  # Still only 1 job due to CPU limit
            'MAX_CONTENT_LENGTH': 500 * 1024 * 1024,  # 500MB
            'MAX_MEMORY_USAGE_GB': 6.0,  # Can use more memory
            'VIDEO_CHUNK_DURATION': 60,  # Larger chunks
            'WHISPER_MODEL': 'small',  # Better model with more memory
            'WHISPER_MAX_MEMORY_GB': 2.0,
            'UNLOAD_MODEL_AFTER_USE': False,  # Keep model loaded
            'MAX_FONT_SIZE': 100,  # Larger fonts allowed
            'MAX_OUTLINE_WIDTH': 5,
            'SYSTEM_TYPE': 'cpu_constrained'
        })
        return config
    
    def _get_standard_config(self):
        """Configuration for standard systems (8GB+ RAM, 4+ vCPUs)"""
        return {
            # Standard settings
            'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
            'MAX_CONTENT_LENGTH': 500 * 1024 * 1024,  # 500MB
            
            # Directory configurations  
            'TEMP_DIR': os.environ.get('TEMP_DIR', 'temp'),
            'UPLOADS_DIR': os.environ.get('UPLOADS_DIR', 'uploads'),
            'JOBS_DIR': os.environ.get('JOBS_DIR', 'jobs'),
            'STATIC_DIR': os.environ.get('STATIC_DIR', 'static'),
            
            # Processing configurations
            'MAX_WORKERS': min(4, self.cpu_count),
            'DOWNLOAD_TIMEOUT': 300,
            
            # Memory management
            'MAX_MEMORY_USAGE_GB': min(6.0, self.system_memory_gb * 0.75),
            'ENABLE_MEMORY_MONITORING': True,
            'FORCE_CLEANUP_THRESHOLD': 0.85,
            
            # Video processing
            'VIDEO_CHUNK_DURATION': 120,  # 2-minute chunks
            'DEFAULT_VIDEO_CODEC': 'libx264',
            'DEFAULT_AUDIO_CODEC': 'aac',
            'FFMPEG_PRESET': 'fast',
            'FFMPEG_THREADS': min(4, self.cpu_count),
            'ENABLE_CHUNKED_PROCESSING': False,  # Optional for standard systems
            
            # Whisper configurations
            'WHISPER_MODEL': 'base',
            'WHISPER_MAX_MEMORY_GB': 2.0,
            'ENABLE_DYNAMIC_MODEL_SELECTION': True,
            'UNLOAD_MODEL_AFTER_USE': False,
            'ENABLE_AUDIO_CHUNKING': False,
            
            # Subtitle optimizations
            'MAX_SUBTITLE_CLIPS': 200,
            'SUBTITLE_BATCH_SIZE': 25,
            'MAX_FONT_SIZE': 120,
            'MAX_OUTLINE_WIDTH': 10,
            
            # Job cleanup
            'JOB_CLEANUP_DAYS': 7,
            'TEMP_FILE_CLEANUP_HOURS': 24,
            'AUTO_CLEANUP_ENABLED': True,
            
            # Performance monitoring
            'ENABLE_PERFORMANCE_LOGGING': False,
            'MEMORY_WARNING_THRESHOLD': 0.8,
            'CPU_WARNING_THRESHOLD': 0.95,
            
            # System label
            'SYSTEM_TYPE': 'standard'
        }

class ResourceMonitor:
    """Real-time resource monitoring and adaptive configuration"""
    
    @staticmethod
    def get_current_usage():
        """Get current system resource usage"""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            'memory_used_gb': memory.used / (1024**3),
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'cpu_percent': cpu_percent,
            'swap_percent': psutil.swap_memory().percent if psutil.swap_memory().total > 0 else 0
        }
    
    @staticmethod
    def should_enable_aggressive_optimization():
        """Check if system needs aggressive optimization"""
        usage = ResourceMonitor.get_current_usage()
        
        # Enable aggressive optimization if:
        # - Memory usage > 75%
        # - CPU usage > 85% 
        # - Swap usage > 10%
        return (
            usage['memory_percent'] > 75 or
            usage['cpu_percent'] > 85 or
            usage['swap_percent'] > 10
        )
    
    @staticmethod
    def get_adaptive_chunk_size(video_duration: float, memory_usage_percent: float):
        """Dynamically adjust chunk size based on current memory pressure"""
        base_chunk_size = 60  # seconds
        
        if memory_usage_percent > 80:
            return 30  # Very small chunks
        elif memory_usage_percent > 60:
            return 45  # Small chunks  
        else:
            return base_chunk_size
    
    @staticmethod
    def recommend_whisper_model(memory_usage_percent: float, video_duration: float):
        """Recommend Whisper model based on current system state"""
        if memory_usage_percent > 70:
            return "tiny"
        elif memory_usage_percent > 50:
            return "base"
        elif video_duration > 600:  # Long videos
            return "base"  # Balance quality vs speed
        else:
            return "small"

# Configuration factory
def get_config():
    """Get optimized configuration for current system"""
    optimizer = OptimizedConfig()
    return optimizer.get_optimal_settings()

def get_runtime_config():
    """Get configuration with real-time resource monitoring"""
    base_config = get_config()
    
    # Add runtime monitoring data
    current_usage = ResourceMonitor.get_current_usage()
    base_config.update({
        'current_memory_usage_gb': current_usage['memory_used_gb'],
        'current_memory_percent': current_usage['memory_percent'],
        'current_cpu_percent': current_usage['cpu_percent'],
        'adaptive_optimization_enabled': ResourceMonitor.should_enable_aggressive_optimization()
    })
    
    return base_config

# Development vs Production configurations
class DevelopmentOptimizedConfig(OptimizedConfig):
    """Development configuration with resource optimization"""
    def get_optimal_settings(self):
        config = super().get_optimal_settings()
        config.update({
            'DEBUG': True,
            'FLASK_ENV': 'development',
            'ENABLE_PERFORMANCE_LOGGING': True
        })
        return config

class ProductionOptimizedConfig(OptimizedConfig):
    """Production configuration with resource optimization"""
    def get_optimal_settings(self):
        config = super().get_optimal_settings()
        config.update({
            'DEBUG': False,
            'FLASK_ENV': 'production',
            'ENABLE_PERFORMANCE_LOGGING': False
        })
        return config

class TestingOptimizedConfig(OptimizedConfig):
    """Testing configuration with minimal resources"""
    def get_optimal_settings(self):
        return {
            'TESTING': True,
            'FLASK_ENV': 'testing',
            'MAX_WORKERS': 1,
            'WHISPER_MODEL': 'tiny',
            'VIDEO_CHUNK_DURATION': 10,
            'ENABLE_CHUNKED_PROCESSING': True,
            'MAX_CONTENT_LENGTH': 50 * 1024 * 1024,  # 50MB for testing
            'SYSTEM_TYPE': 'testing'
        }

# Environment-based configuration factory
optimized_config = {
    'development': DevelopmentOptimizedConfig,
    'production': ProductionOptimizedConfig, 
    'testing': TestingOptimizedConfig,
    'default': OptimizedConfig
}