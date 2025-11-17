#!/usr/bin/env python3
"""
Performance testing script for VideoEditorAPI optimizations
Tests memory usage, processing speed, and resource efficiency
"""

import requests
import time
import psutil
import json
import sys
import os
from datetime import datetime
import subprocess
import matplotlib.pyplot as plt
import numpy as np

# API Configuration
API_BASE = "http://localhost:8080"

class PerformanceMonitor:
    def __init__(self):
        self.memory_samples = []
        self.cpu_samples = []
        self.start_time = None
        self.monitoring = False
        
    def start_monitoring(self):
        """Start collecting performance metrics."""
        self.start_time = time.time()
        self.monitoring = True
        self.memory_samples = []
        self.cpu_samples = []
        print("📊 Starting performance monitoring...")
        
    def sample_metrics(self):
        """Sample current system metrics."""
        if self.monitoring:
            elapsed = time.time() - self.start_time
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.1)
            
            self.memory_samples.append({
                'timestamp': elapsed,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024)
            })
            
            self.cpu_samples.append({
                'timestamp': elapsed,
                'cpu_percent': cpu
            })
    
    def stop_monitoring(self):
        """Stop monitoring and return summary."""
        if not self.monitoring:
            return None
            
        self.monitoring = False
        duration = time.time() - self.start_time
        
        if not self.memory_samples:
            return {"duration": duration, "samples": 0}
        
        memory_values = [s['memory_percent'] for s in self.memory_samples]
        cpu_values = [s['cpu_percent'] for s in self.cpu_samples]
        
        return {
            "duration": duration,
            "samples": len(self.memory_samples),
            "memory": {
                "peak_percent": max(memory_values),
                "average_percent": np.mean(memory_values),
                "min_available_mb": min([s['memory_available_mb'] for s in self.memory_samples])
            },
            "cpu": {
                "peak_percent": max(cpu_values) if cpu_values else 0,
                "average_percent": np.mean(cpu_values) if cpu_values else 0
            }
        }

def test_api_health():
    """Test API health and get system info."""
    print("\n🔍 Testing API health...")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ API is healthy")
            
            resources = data.get('resources', {})
            print(f"   Memory: {resources.get('memory_usage_percent', 0):.1f}%")
            print(f"   Workers: {resources.get('workers', 0)}")
            
            whisper_model = data.get('whisper_model', {})
            if whisper_model.get('current_model'):
                print(f"   Whisper Model: {whisper_model['current_model']}")
            
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def test_video_processing_performance(video_urls, test_name="Performance Test"):
    """Test video processing with different video lengths."""
    print(f"\n🎬 {test_name}")
    print("=" * 50)
    
    results = []
    
    for i, (name, url) in enumerate(video_urls):
        print(f"\nTest {i+1}: {name}")
        print(f"URL: {url}")
        
        # Start monitoring
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        try:
            # Submit job
            start_time = time.time()
            
            payload = {
                "url": url,
                "language": "en",
                "return_subtitles_file": True,
                "settings": {
                    "font-size": 80,  # Optimized size
                    "font-family": "DejaVu-Sans-Bold",
                    "line-color": "#FFFFFF",
                    "outline-width": 5
                }
            }
            
            response = requests.post(f"{API_BASE}/add-subtitles", json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Job submission failed: {response.status_code}")
                print(f"   Response: {response.text}")
                continue
            
            job_data = response.json()
            job_id = job_data['job_id']
            print(f"✅ Job submitted: {job_id}")
            
            # Monitor job progress
            completed = False
            max_wait = 1800  # 30 minutes max
            check_interval = 10  # Check every 10 seconds
            
            while not completed and (time.time() - start_time) < max_wait:
                monitor.sample_metrics()
                time.sleep(check_interval)
                
                try:
                    status_response = requests.get(f"{API_BASE}/job-status/{job_id}", timeout=10)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        job_status = status_data['status']
                        progress = status_data.get('progress', 0)
                        
                        print(f"   Status: {job_status}, Progress: {progress}%")
                        
                        if job_status == 'completed':
                            completed = True
                            processing_info = status_data.get('processing_info', {})
                            
                            # Get final metrics
                            metrics = monitor.stop_monitoring()
                            total_time = time.time() - start_time
                            
                            result = {
                                "test_name": name,
                                "url": url,
                                "success": True,
                                "total_time": total_time,
                                "processing_time": processing_info.get('processing_time_seconds', total_time),
                                "model_used": processing_info.get('model_used', 'unknown'),
                                "memory_before": processing_info.get('memory_usage_before', 'unknown'),
                                "memory_after": processing_info.get('memory_usage_after', 'unknown'),
                                "performance_metrics": metrics
                            }
                            
                            results.append(result)
                            
                            print(f"✅ Completed in {total_time:.1f}s")
                            print(f"   Model: {result['model_used']}")
                            print(f"   Peak Memory: {metrics['memory']['peak_percent']:.1f}%")
                            print(f"   Avg CPU: {metrics['cpu']['average_percent']:.1f}%")
                            
                        elif job_status == 'failed':
                            error_msg = status_data.get('error', 'Unknown error')
                            print(f"❌ Job failed: {error_msg}")
                            
                            result = {
                                "test_name": name,
                                "url": url,
                                "success": False,
                                "error": error_msg,
                                "total_time": time.time() - start_time,
                                "performance_metrics": monitor.stop_monitoring()
                            }
                            results.append(result)
                            break
                    else:
                        print(f"⚠️  Status check failed: {status_response.status_code}")
                        
                except Exception as e:
                    print(f"⚠️  Status check error: {e}")
            
            if not completed and (time.time() - start_time) >= max_wait:
                print(f"⏰ Test timed out after {max_wait/60:.1f} minutes")
                result = {
                    "test_name": name,
                    "url": url,
                    "success": False,
                    "error": "Timeout",
                    "total_time": time.time() - start_time,
                    "performance_metrics": monitor.stop_monitoring()
                }
                results.append(result)
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            result = {
                "test_name": name,
                "url": url,
                "success": False,
                "error": str(e),
                "total_time": time.time() - start_time if 'start_time' in locals() else 0,
                "performance_metrics": monitor.stop_monitoring()
            }
            results.append(result)
    
    return results

def generate_performance_report(results, output_file="performance_report.json"):
    """Generate a comprehensive performance report."""
    print(f"\n📊 Generating Performance Report")
    print("=" * 50)
    
    # Summary statistics
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    if successful_tests:
        avg_time = np.mean([r['total_time'] for r in successful_tests])
        avg_memory = np.mean([r['performance_metrics']['memory']['peak_percent'] 
                             for r in successful_tests 
                             if r['performance_metrics']])
        avg_cpu = np.mean([r['performance_metrics']['cpu']['average_percent'] 
                          for r in successful_tests 
                          if r['performance_metrics']])
        
        print(f"✅ Successful Tests: {len(successful_tests)}/{len(results)}")
        print(f"   Average Processing Time: {avg_time:.1f}s")
        print(f"   Average Peak Memory: {avg_memory:.1f}%")
        print(f"   Average CPU Usage: {avg_cpu:.1f}%")
        
        # Model usage statistics
        models_used = {}
        for r in successful_tests:
            model = r.get('model_used', 'unknown')
            models_used[model] = models_used.get(model, 0) + 1
        
        print(f"\n🧠 Whisper Models Used:")
        for model, count in models_used.items():
            print(f"   {model}: {count} times")
    
    if failed_tests:
        print(f"\n❌ Failed Tests: {len(failed_tests)}")
        for test in failed_tests:
            print(f"   {test['test_name']}: {test['error']}")
    
    # Save detailed report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": len(results),
            "successful": len(successful_tests),
            "failed": len(failed_tests),
            "success_rate": len(successful_tests) / len(results) if results else 0
        },
        "results": results
    }
    
    if successful_tests:
        report["summary"]["performance"] = {
            "average_time": avg_time,
            "average_peak_memory": avg_memory,
            "average_cpu": avg_cpu,
            "models_used": models_used
        }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {output_file}")
    return report

def visualize_performance_trends(results, output_dir="performance_charts"):
    """Create performance visualization charts."""
    print(f"\n📈 Creating Performance Visualizations")
    
    successful_results = [r for r in results if r['success'] and r.get('performance_metrics')]
    
    if len(successful_results) < 2:
        print("⚠️  Not enough successful tests for visualization")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Memory usage over time
    plt.figure(figsize=(12, 8))
    
    # Plot 1: Memory vs Processing Time
    plt.subplot(2, 2, 1)
    times = [r['total_time'] for r in successful_results]
    memory_peaks = [r['performance_metrics']['memory']['peak_percent'] for r in successful_results]
    
    plt.scatter(times, memory_peaks, alpha=0.7)
    plt.xlabel('Processing Time (seconds)')
    plt.ylabel('Peak Memory Usage (%)')
    plt.title('Memory Usage vs Processing Time')
    plt.grid(True)
    
    # Plot 2: CPU vs Processing Time
    plt.subplot(2, 2, 2)
    cpu_avg = [r['performance_metrics']['cpu']['average_percent'] for r in successful_results]
    
    plt.scatter(times, cpu_avg, alpha=0.7, color='orange')
    plt.xlabel('Processing Time (seconds)')
    plt.ylabel('Average CPU Usage (%)')
    plt.title('CPU Usage vs Processing Time')
    plt.grid(True)
    
    # Plot 3: Model Performance
    plt.subplot(2, 2, 3)
    models = [r.get('model_used', 'unknown') for r in successful_results]
    model_times = {}
    
    for i, model in enumerate(models):
        if model not in model_times:
            model_times[model] = []
        model_times[model].append(times[i])
    
    model_names = list(model_times.keys())
    avg_times = [np.mean(model_times[m]) for m in model_names]
    
    plt.bar(model_names, avg_times)
    plt.xlabel('Whisper Model')
    plt.ylabel('Average Processing Time (s)')
    plt.title('Performance by Model')
    plt.xticks(rotation=45)
    
    # Plot 4: Resource Efficiency
    plt.subplot(2, 2, 4)
    efficiency = [t / m for t, m in zip(times, memory_peaks)]  # Time per memory %
    
    plt.hist(efficiency, bins=10, alpha=0.7)
    plt.xlabel('Processing Efficiency (sec/%memory)')
    plt.ylabel('Frequency')
    plt.title('Resource Efficiency Distribution')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/performance_analysis.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"📈 Charts saved to: {output_dir}/performance_analysis.png")

def run_comprehensive_test():
    """Run a comprehensive performance test suite."""
    print("🚀 VideoEditorAPI Performance Test Suite")
    print("=" * 60)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # System information
    memory = psutil.virtual_memory()
    print(f"\n💾 System Information:")
    print(f"   Total Memory: {memory.total / (1024**3):.1f} GB")
    print(f"   Available Memory: {memory.available / (1024**3):.1f} GB") 
    print(f"   CPU Cores: {psutil.cpu_count()}")
    print(f"   Current Memory Usage: {memory.percent:.1f}%")
    
    # Check API health
    if not test_api_health():
        print("\n❌ API is not healthy. Please start the optimized app:")
        print("   python app_optimized.py")
        return
    
    # Test video URLs with different lengths and complexity
    test_videos = [
        ("Short Video (30s)", "https://sample-videos.com/zip/10/mp4/SampleVideo_360x240_1mb.mp4"),
        ("Medium Video (2min)", "https://sample-videos.com/zip/10/mp4/SampleVideo_720x480_2mb.mp4"),
        # Add more test videos as available
    ]
    
    # Note: For real testing, replace with actual long video URLs
    print(f"\n⚠️  Using sample videos for testing")
    print("   For real performance testing, replace URLs with:")
    print("   - 5-minute video URL")
    print("   - 10-minute video URL")
    print("   - 20+ minute video URL")
    
    # Run performance tests
    results = test_video_processing_performance(test_videos, "Optimized VideoAPI Performance")
    
    # Generate reports
    report = generate_performance_report(results, "optimized_performance_report.json")
    
    # Create visualizations
    try:
        visualize_performance_trends(results, "performance_charts")
    except ImportError:
        print("⚠️  Matplotlib not available - skipping charts")
    except Exception as e:
        print(f"⚠️  Chart generation failed: {e}")
    
    # Performance recommendations
    print(f"\n🎯 Performance Recommendations")
    print("=" * 50)
    
    if report['summary']['success_rate'] < 0.5:
        print("❌ Low success rate detected:")
        print("   - Check system memory availability")
        print("   - Reduce concurrent jobs")
        print("   - Use smaller Whisper models")
    
    if report['summary']['successful'] > 0:
        avg_memory = report['summary']['performance']['average_peak_memory']
        if avg_memory > 90:
            print("⚠️  High memory usage detected:")
            print("   - Consider upgrading system memory")
            print("   - Use 'tiny' Whisper model for large videos")
            print("   - Process videos in smaller chunks")
        elif avg_memory > 75:
            print("💡 Moderate memory usage:")
            print("   - Current optimization is working well")
            print("   - Consider 'base' model for better quality")
        else:
            print("✅ Excellent memory efficiency:")
            print("   - System is well-optimized for your workload")
            print("   - Can handle larger videos or higher quality models")
    
    print(f"\n✅ Performance test completed!")
    print(f"   Report: optimized_performance_report.json")
    print(f"   Charts: performance_charts/")

if __name__ == "__main__":
    # Add matplotlib for charts (optional)
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-GUI backend
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("📊 Matplotlib not installed - charts will be skipped")
        print("   Install with: pip install matplotlib numpy")
    
    run_comprehensive_test()