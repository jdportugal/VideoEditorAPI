"""
High-Performance Configuration for VideoEditorAPI
Optimized to use all available system resources for maximum speed.
"""

import os
import psutil
import torch
from typing import Dict, Any

class PerformanceConfig:
    """Configuration for high-performance mode using all available resources."""
    
    def __init__(self):
        self.system_info = self._detect_system_resources()
        self.performance_mode = "HIGH_PERFORMANCE"
        
    def _detect_system_resources(self) -> Dict[str, Any]:
        """Detect available system resources."""
        memory = psutil.virtual_memory()
        
        return {
            "total_cpu_cores": psutil.cpu_count(logical=True),
            "physical_cpu_cores": psutil.cpu_count(logical=False),
            "total_memory_gb": memory.total / (1024**3),
            "available_memory_gb": memory.available / (1024**3),
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "memory_usage_percent": memory.percent,
            "pytorch_threads": torch.get_num_threads(),
            "cuda_available": torch.cuda.is_available()
        }
    
    def get_whisper_config(self) -> Dict[str, Any]:
        """Get Whisper configuration for high-performance mode."""
        # Always use tiny model for maximum speed as requested
        available_gb = self.system_info["available_memory_gb"]
        
        # Force tiny model for maximum processing speed
        model = "tiny"  # 100MB, fastest processing
            
        return {
            "model": model,
            "fp16": True,  # Use half precision for speed
            "threads": self.system_info["total_cpu_cores"],
            "batch_size": min(16, max(1, int(available_gb))),
            "verbose": True
        }
    
    def get_video_processing_config(self) -> Dict[str, Any]:
        """Get video processing configuration for high-performance mode."""
        return {
            "workers": min(self.system_info["total_cpu_cores"], 8),
            "chunk_size_minutes": 2,  # Smaller chunks for faster processing
            "parallel_chunks": min(4, self.system_info["physical_cpu_cores"]),
            "ffmpeg_threads": self.system_info["total_cpu_cores"],
            "preset": "ultrafast",
            "memory_limit_percent": 85  # Use up to 85% of available memory
        }
    
    def get_flask_config(self) -> Dict[str, Any]:
        """Get Flask configuration for high-performance mode."""
        return {
            "workers": min(self.system_info["total_cpu_cores"] * 2, 16),
            "threaded": True,
            "worker_class": "gthread",
            "worker_connections": 1000,
            "max_requests": 10000,
            "timeout": 300
        }
    
    def get_resource_limits(self) -> Dict[str, Any]:
        """Get resource limits for high-performance mode."""
        total_memory = self.system_info["total_memory_gb"]
        
        return {
            "max_memory_percent": 90,
            "emergency_cleanup_threshold": 95,
            "cpu_throttle_threshold": 95,
            "max_concurrent_jobs": min(4, self.system_info["physical_cpu_cores"]),
            "memory_buffer_gb": max(0.5, total_memory * 0.1)  # 10% buffer
        }
    
    def optimize_pytorch(self):
        """Optimize PyTorch for maximum performance."""
        # Set number of threads for PyTorch operations
        torch.set_num_threads(self.system_info["total_cpu_cores"])
        
        # Enable optimizations
        torch.backends.cudnn.benchmark = True if torch.cuda.is_available() else False
        torch.set_grad_enabled(False)  # Disable gradients for inference
        
        # Set environment variables for performance
        os.environ["OMP_NUM_THREADS"] = str(self.system_info["total_cpu_cores"])
        os.environ["MKL_NUM_THREADS"] = str(self.system_info["total_cpu_cores"])
        os.environ["VECLIB_MAXIMUM_THREADS"] = str(self.system_info["total_cpu_cores"])
        os.environ["NUMEXPR_NUM_THREADS"] = str(self.system_info["total_cpu_cores"])
        
    def print_performance_info(self):
        """Print performance mode information."""
        print("\n🚀 HIGH-PERFORMANCE MODE ACTIVATED")
        print("=" * 50)
        print(f"💻 CPU Cores: {self.system_info['total_cpu_cores']} logical, {self.system_info['physical_cpu_cores']} physical")
        print(f"🧠 Memory: {self.system_info['total_memory_gb']:.1f}GB total, {self.system_info['available_memory_gb']:.1f}GB available")
        print(f"🎙️ Whisper Model: {self.get_whisper_config()['model']} (FP16: {self.get_whisper_config()['fp16']})")
        print(f"🎬 Video Workers: {self.get_video_processing_config()['workers']}")
        print(f"🔗 Parallel Chunks: {self.get_video_processing_config()['parallel_chunks']}")
        print(f"⚡ PyTorch Threads: {self.system_info['pytorch_threads']}")
        print(f"🎯 Max Concurrent Jobs: {self.get_resource_limits()['max_concurrent_jobs']}")
        print("=" * 50)