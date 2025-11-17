import whisper
import os
import gc
import psutil
import tempfile
import json
import logging
from typing import List, Dict, Any, Optional
import torch

# Configure logging for performance monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedSubtitleService:
    def __init__(self):
        self.current_model = None
        self.current_model_name = None
        self.memory_threshold = 0.85  # 85% memory usage threshold
        
        # Model memory requirements (approximate)
        self.model_memory = {
            "tiny": 100,    # ~100MB
            "base": 500,    # ~500MB  
            "small": 1000,  # ~1GB
            "medium": 2500, # ~2.5GB
            "large": 5000   # ~5GB
        }
        
        # Performance/quality trade-offs
        self.model_performance = {
            "tiny": {"speed": 10, "quality": 6, "languages": "limited"},
            "base": {"speed": 8, "quality": 8, "languages": "good"}, 
            "small": {"speed": 6, "quality": 9, "languages": "excellent"},
            "medium": {"speed": 4, "quality": 9.5, "languages": "excellent"},
            "large": {"speed": 2, "quality": 10, "languages": "excellent"}
        }
        
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get detailed memory usage information."""
        memory = psutil.virtual_memory()
        return {
            "percent": memory.percent / 100.0,
            "available_mb": memory.available / (1024 * 1024),
            "total_mb": memory.total / (1024 * 1024),
            "used_mb": memory.used / (1024 * 1024)
        }
    
    def _select_optimal_model(self, available_memory_mb: float, video_duration: float = None) -> str:
        """
        Always use tiny model for maximum speed and reliability on constrained systems.
        
        Args:
            available_memory_mb: Available memory in MB (ignored, always use tiny)
            video_duration: Video duration in seconds (ignored, always use tiny)
            
        Returns:
            Always returns "tiny" for optimal performance
        """
        logger.info(f"ULTRA-FAST MODE: Always using 'tiny' model for optimal performance on 4GB systems")
        logger.info("Tiny model specs: 100MB RAM, 8/10 speed, 7/10 quality - perfect for constrained systems")
        return "tiny"
    
    def _load_model_if_needed(self, model_name: str):
        """Load Whisper model only if different from current model."""
        if self.current_model_name == model_name and self.current_model is not None:
            logger.info(f"Model '{model_name}' already loaded")
            return
        
        # Unload current model to free memory
        if self.current_model is not None:
            logger.info(f"Unloading current model '{self.current_model_name}'")
            del self.current_model
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            gc.collect()
        
        # Load new model
        logger.info(f"🚀 Loading Whisper model '{model_name}' (this may take 30-60 seconds)...")
        logger.info(f"📦 Model specs: {self.model_memory[model_name]}MB RAM, Speed: {self.model_performance[model_name]['speed']}/10")
        memory_before = self._get_memory_usage()["used_mb"]
        
        self.current_model = whisper.load_model(model_name)
        self.current_model_name = model_name
        
        memory_after = self._get_memory_usage()["used_mb"]
        memory_used = memory_after - memory_before
        logger.info(f"✅ Whisper model '{model_name}' loaded successfully! Used {memory_used:.1f}MB RAM")
        
        logger.info(f"Model '{model_name}' loaded successfully, using {memory_used:.0f}MB memory")
    
    def _should_process_in_chunks(self, video_duration: float, available_memory_mb: float) -> bool:
        """Determine if audio should be processed in chunks."""
        # Process in chunks if:
        # 1. Video is very long (20+ minutes)
        # 2. Memory is limited (<2GB available)
        # 3. Using a larger model on limited memory
        
        return (video_duration > 1200 or  # 20+ minutes
                available_memory_mb < 2000 or  # <2GB available
                (self.current_model_name in ["medium", "large"] and available_memory_mb < 4000))
    
    def generate_subtitles(self, video_path: str, language: str = "en", timing_offset: float = 0.0, progress_callback=None) -> List[Dict[str, Any]]:
        """
        Generate subtitles with dynamic model selection and memory optimization.
        """
        try:
            # Get video duration for model selection
            video_duration = self._get_video_duration(video_path)
            logger.info(f"Processing video: duration={video_duration:.1f}s")
            
            # Get current memory status
            memory_info = self._get_memory_usage()
            logger.info(f"Memory usage: {memory_info['percent']:.1%} ({memory_info['available_mb']:.0f}MB available)")
            
            # Select optimal model
            model_name = self._select_optimal_model(memory_info["available_mb"], video_duration)
            
            # Load model if needed
            self._load_model_if_needed(model_name)
            
            # Determine if chunked processing is needed
            if self._should_process_in_chunks(video_duration, memory_info["available_mb"]):
                logger.info("Using chunked audio processing for large file")
                return self._generate_subtitles_chunked(video_path, language, timing_offset, progress_callback)
            else:
                logger.info("Using standard audio processing")
                return self._generate_subtitles_standard(video_path, language, timing_offset, progress_callback)
            
        except Exception as e:
            # Cleanup on error
            self._cleanup_memory()
            raise Exception(f"Error generating subtitles: {str(e)}")
    
    def _generate_subtitles_standard(self, video_path: str, language: str, timing_offset: float, progress_callback=None) -> List[Dict[str, Any]]:
        """Standard subtitle generation for smaller files."""
        
        logger.info("🎙️ Starting Whisper transcription (standard mode)")
        logger.info(f"📝 Model: {self.current_model_name}, Language: {language}")
        logger.info("⏳ Whisper is processing audio... (this may take 2-5 minutes)")
        
        # Update progress: Starting Whisper processing (25%)
        if progress_callback:
            progress_callback(25, "🎙️ Starting Whisper transcription...")
        
        # Transcribe the audio
        result = self.current_model.transcribe(
            video_path,
            language=language,
            word_timestamps=True,
            verbose=True,  # Enable verbose for progress visibility
            fp16=False  # Use FP32 for better compatibility on limited hardware
        )
        
        # Update progress: Whisper completed (55%)
        if progress_callback:
            progress_callback(55, f"✅ Whisper completed! Found {len(result.get('segments', []))} segments")
        
        logger.info(f"✅ Whisper transcription completed! Found {len(result.get('segments', []))} segments")
        
        # Process segments
        subtitles = []
        for segment in result["segments"]:
            adjusted_start = max(0, segment["start"] + timing_offset)
            adjusted_end = max(adjusted_start + 0.1, segment["end"] + timing_offset)
            
            subtitle_segment = {
                "start": adjusted_start,
                "end": adjusted_end,
                "text": segment["text"].strip(),
                "words": []
            }
            
            # Add word-level timestamps if available
            if "words" in segment:
                for word in segment["words"]:
                    word_start = max(0, word["start"] + timing_offset)
                    word_end = max(word_start + 0.1, word["end"] + timing_offset)
                    subtitle_segment["words"].append({
                        "word": word["word"],
                        "start": word_start,
                        "end": word_end
                    })
            
            subtitles.append(subtitle_segment)
        
        return subtitles
    
    def _generate_subtitles_chunked(self, video_path: str, language: str, timing_offset: float, progress_callback=None) -> List[Dict[str, Any]]:
        """Generate subtitles by processing audio in chunks."""
        
        video_duration = self._get_video_duration(video_path)
        chunk_duration = 300  # 5-minute chunks
        
        # Adjust chunk size based on memory
        memory_info = self._get_memory_usage()
        if memory_info["available_mb"] < 1500:  # Very limited memory
            chunk_duration = 120  # 2-minute chunks
        elif memory_info["available_mb"] < 3000:  # Limited memory
            chunk_duration = 240  # 4-minute chunks
        
        logger.info(f"🎙️ Starting Whisper transcription (chunked mode)")
        logger.info(f"📝 Model: {self.current_model_name}, Language: {language}")
        logger.info(f"📊 Processing {video_duration:.1f}s video in {chunk_duration}s chunks")
        
        all_subtitles = []
        current_time = 0.0
        total_chunks = int(video_duration / chunk_duration) + 1
        
        # Create temporary directory for audio chunks
        temp_dir = tempfile.mkdtemp(prefix="audio_chunks_")
        
        try:
            chunk_index = 0
            
            while current_time < video_duration:
                chunk_end = min(current_time + chunk_duration, video_duration)
                
                # Calculate progress: 25% base + 30% for Whisper processing across chunks
                chunk_progress_base = 25 + int((chunk_index / total_chunks) * 30)
                
                logger.info(f"🎵 Processing audio chunk {chunk_index + 1}/{total_chunks}: {current_time:.1f}s - {chunk_end:.1f}s")
                
                # Update progress: Starting chunk
                if progress_callback:
                    progress_callback(chunk_progress_base, f"🎵 Processing audio chunk {chunk_index + 1}/{total_chunks}")
                
                # Extract audio chunk
                chunk_path = os.path.join(temp_dir, f"chunk_{chunk_index:04d}.wav")
                logger.info(f"🔄 Extracting audio chunk to {chunk_path}")
                self._extract_audio_chunk(video_path, chunk_path, current_time, chunk_end)
                
                # Process this chunk
                logger.info(f"⏳ Whisper processing chunk {chunk_index + 1}... (30-90 seconds)")
                if progress_callback:
                    progress_callback(chunk_progress_base + 5, f"⏳ Whisper processing chunk {chunk_index + 1}...")
                
                chunk_result = self.current_model.transcribe(
                    chunk_path,
                    language=language,
                    word_timestamps=True,
                    verbose=True,  # Enable verbose for chunk progress
                    fp16=False
                )
                
                segments_found = len(chunk_result.get("segments", []))
                logger.info(f"✅ Chunk {chunk_index + 1} completed! Found {segments_found} segments")
                
                # Update progress: Chunk completed
                if progress_callback:
                    progress_callback(chunk_progress_base + 10, f"✅ Chunk {chunk_index + 1} completed! Found {segments_found} segments")
                
                # Adjust timings and add to results
                for segment in chunk_result["segments"]:
                    adjusted_start = max(0, segment["start"] + current_time + timing_offset)
                    adjusted_end = max(adjusted_start + 0.1, segment["end"] + current_time + timing_offset)
                    
                    subtitle_segment = {
                        "start": adjusted_start,
                        "end": adjusted_end,
                        "text": segment["text"].strip(),
                        "words": []
                    }
                    
                    # Adjust word timings
                    if "words" in segment:
                        for word in segment["words"]:
                            word_start = max(0, word["start"] + current_time + timing_offset)
                            word_end = max(word_start + 0.1, word["end"] + current_time + timing_offset)
                            subtitle_segment["words"].append({
                                "word": word["word"],
                                "start": word_start,
                                "end": word_end
                            })
                    
                    all_subtitles.append(subtitle_segment)
                
                # Cleanup chunk file
                os.remove(chunk_path)
                
                # Force memory cleanup
                self._cleanup_memory()
                
                current_time = chunk_end
                chunk_index += 1
                
                # Check memory usage and adjust chunk size if needed
                memory_info = self._get_memory_usage()
                if memory_info["percent"] > self.memory_threshold:
                    chunk_duration = max(60, chunk_duration * 0.8)  # Reduce chunk size
                    logger.warning(f"High memory usage detected, reducing chunk size to {chunk_duration}s")
            
            return all_subtitles
            
        finally:
            # Cleanup temporary directory
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, file))
                os.rmdir(temp_dir)
    
    def _extract_audio_chunk(self, video_path: str, output_path: str, start_time: float, end_time: float):
        """Extract audio chunk using FFmpeg for memory efficiency."""
        import subprocess
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-ss', str(start_time),
            '-to', str(end_time),
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # Uncompressed audio for Whisper
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',  # Mono
            '-y',  # Overwrite output
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg audio extraction failed: {result.stderr}")
    
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration using FFprobe for efficiency."""
        import subprocess
        import json
        
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Fallback to VideoFileClip if ffprobe fails
            from moviepy.editor import VideoFileClip
            with VideoFileClip(video_path) as video:
                return video.duration
        
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    
    def _cleanup_memory(self):
        """Force garbage collection and cleanup."""
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        memory_info = self._get_memory_usage()
        logger.info(f"Memory usage after cleanup: {memory_info['percent']:.1%}")
    
    def save_subtitle_file(self, subtitles: List[Dict[str, Any]], output_path: str, format: str = "srt") -> str:
        """Save subtitles with memory optimization."""
        try:
            if format.lower() == "srt":
                self._save_srt(subtitles, output_path)
            elif format.lower() == "vtt":
                self._save_vtt(subtitles, output_path)
            elif format.lower() == "json":
                self._save_json(subtitles, output_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error saving subtitle file: {str(e)}")
    
    def _save_srt(self, subtitles: List[Dict[str, Any]], output_path: str):
        """Save subtitles in SRT format."""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, subtitle in enumerate(subtitles, 1):
                start_time = self._seconds_to_srt_time(subtitle["start"])
                end_time = self._seconds_to_srt_time(subtitle["end"])
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{subtitle['text']}\n\n")
    
    def _save_vtt(self, subtitles: List[Dict[str, Any]], output_path: str):
        """Save subtitles in WebVTT format."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            for subtitle in subtitles:
                start_time = self._seconds_to_vtt_time(subtitle["start"])
                end_time = self._seconds_to_vtt_time(subtitle["end"])
                
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{subtitle['text']}\n\n")
    
    def _save_json(self, subtitles: List[Dict[str, Any]], output_path: str):
        """Save subtitles in JSON format."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(subtitles, f, indent=2, ensure_ascii=False)
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to WebVTT time format (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
    
    def format_text_for_video(self, text: str, max_words_per_line: int = 4) -> str:
        """Format subtitle text for video display with word wrapping."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            if len(current_line) >= max_words_per_line:
                lines.append(' '.join(current_line))
                current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
    def analyze_timing_gaps(self, subtitles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze subtitle timing for optimization opportunities."""
        if len(subtitles) < 2:
            return {"status": "insufficient_data", "recommendation": "No timing analysis possible with < 2 segments"}
        
        gaps = []
        for i in range(len(subtitles) - 1):
            current_end = subtitles[i]["end"]
            next_start = subtitles[i + 1]["start"]
            gap = next_start - current_end
            
            if gap > 0.5:  # Significant gaps
                gaps.append({
                    "after_segment": i + 1,
                    "before_segment": i + 2,
                    "gap_duration": gap,
                    "gap_start": current_end,
                    "gap_end": next_start
                })
        
        analysis = {
            "total_segments": len(subtitles),
            "significant_gaps": len(gaps),
            "largest_gap": max(gaps, key=lambda x: x["gap_duration"]) if gaps else None,
            "timing_span": subtitles[-1]["end"] - subtitles[0]["start"] if subtitles else 0,
            "model_used": self.current_model_name,
            "processing_mode": "chunked" if hasattr(self, '_used_chunked_processing') else "standard"
        }
        
        # Generate performance-aware recommendations
        recommendations = []
        
        if gaps and len(gaps) > 0:
            largest_gap = analysis["largest_gap"]
            
            # Check for early large gaps that might indicate timing offset issues
            early_large_gaps = [g for g in gaps if g["gap_start"] < 30 and g["gap_duration"] > 5]
            
            if early_large_gaps:
                early_gap = early_large_gaps[0]
                suggested_offset = -early_gap["gap_duration"] / 2
                recommendations.append({
                    "type": "timing_offset",
                    "severity": "high",
                    "message": f"Large {early_gap['gap_duration']:.1f}s gap detected early in video",
                    "suggested_offset": suggested_offset,
                    "reasoning": "Early large gaps often indicate subtitle timing is off from the start"
                })
            
            if largest_gap["gap_duration"] > 10:
                recommendations.append({
                    "type": "content_gap",
                    "severity": "medium", 
                    "message": f"Very large gap ({largest_gap['gap_duration']:.1f}s) suggests silence or scene change",
                    "suggested_offset": 0,
                    "reasoning": "Large gaps may be intentional silence periods"
                })
        
        # Performance recommendations based on model used
        if self.current_model_name == "tiny":
            recommendations.append({
                "type": "quality_optimization",
                "severity": "low",
                "message": "Using 'tiny' model for memory efficiency - consider upgrading hardware for better quality",
                "suggested_action": "Use 'base' model if more memory becomes available",
                "reasoning": "Tiny model prioritizes speed over accuracy"
            })
        
        analysis["recommendations"] = recommendations
        return analysis
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the currently loaded model."""
        if not self.current_model_name:
            return {"status": "no_model_loaded"}
        
        memory_info = self._get_memory_usage()
        
        return {
            "current_model": self.current_model_name,
            "memory_usage_mb": self.model_memory[self.current_model_name],
            "performance": self.model_performance[self.current_model_name],
            "system_memory": memory_info,
            "model_loaded": self.current_model is not None
        }
    
    def unload_model(self):
        """Manually unload the current model to free memory."""
        if self.current_model is not None:
            logger.info(f"Manually unloading model '{self.current_model_name}'")
            del self.current_model
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            gc.collect()
            
            self.current_model = None
            self.current_model_name = None
            
            memory_info = self._get_memory_usage()
            logger.info(f"Model unloaded. Memory usage: {memory_info['percent']:.1%}")
            
            return True
        return False