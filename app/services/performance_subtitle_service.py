"""
High-Performance Subtitle Service
Uses all available system resources for maximum processing speed.
"""

import whisper
import torch
import gc
import os
import tempfile
import concurrent.futures
from typing import List, Dict, Any, Optional
import psutil
import time
from app.config.performance_config import PerformanceConfig

import logging
logger = logging.getLogger(__name__)

class PerformanceSubtitleService:
    """High-performance subtitle service using all available system resources."""
    
    def __init__(self):
        self.config = PerformanceConfig()
        self.config.optimize_pytorch()
        
        self.current_model = None
        self.current_model_name = None
        
        # Print performance info
        self.config.print_performance_info()
        
    def generate_subtitles(self, video_path: str, language: str = "en", timing_offset: float = 0.0, progress_callback=None) -> List[Dict[str, Any]]:
        """
        Generate subtitles using high-performance configuration.
        """
        try:
            logger.info("🚀 Starting HIGH-PERFORMANCE subtitle generation")
            
            # Load optimal model for available resources
            whisper_config = self.config.get_whisper_config()
            self._load_model_if_needed(whisper_config["model"])
            
            if progress_callback:
                progress_callback(15, "🚀 High-performance mode initialized")
            
            # Check if we should use parallel processing
            video_duration = self._get_video_duration(video_path)
            video_config = self.config.get_video_processing_config()
            
            if video_duration > 600:  # 10+ minute videos
                logger.info("🔥 Using parallel chunked processing for maximum speed")
                return self._generate_subtitles_parallel(video_path, language, timing_offset, progress_callback)
            else:
                logger.info("⚡ Using optimized single-pass processing")
                return self._generate_subtitles_optimized(video_path, language, timing_offset, progress_callback)
                
        except Exception as e:
            self._cleanup_memory()
            raise Exception(f"High-performance subtitle generation failed: {str(e)}")
    
    def _generate_subtitles_optimized(self, video_path: str, language: str, timing_offset: float, progress_callback=None) -> List[Dict[str, Any]]:
        """Optimized single-pass processing with all resources."""
        
        whisper_config = self.config.get_whisper_config()
        
        logger.info("🎙️ Starting optimized Whisper transcription")
        logger.info(f"📝 Model: {self.current_model_name} (FP16: {whisper_config['fp16']})")
        logger.info(f"🧵 Using {whisper_config['threads']} CPU threads")
        
        if progress_callback:
            progress_callback(25, f"🎙️ Transcribing with {self.current_model_name} model...")
            
        start_time = time.time()
        
        # Transcribe with all optimizations
        result = self.current_model.transcribe(
            video_path,
            language=language,
            word_timestamps=True,
            fp16=whisper_config["fp16"],
            verbose=True,
            beam_size=5,  # Higher quality
            best_of=5,    # Multiple attempts for best result
            temperature=0  # Deterministic output
        )
        
        processing_time = time.time() - start_time
        segments_found = len(result.get("segments", []))
        
        logger.info(f"✅ Transcription completed in {processing_time:.1f}s! Found {segments_found} segments")
        logger.info(f"📊 Processing speed: {self._get_video_duration(video_path)/processing_time:.2f}x realtime")
        
        if progress_callback:
            progress_callback(60, f"✅ Transcription completed! {segments_found} segments in {processing_time:.1f}s")
        
        # Process segments with word-level timing
        return self._process_segments(result["segments"], timing_offset)
    
    def _generate_subtitles_parallel(self, video_path: str, language: str, timing_offset: float, progress_callback=None) -> List[Dict[str, Any]]:
        """Parallel processing for large videos using all CPU cores."""
        
        video_duration = self._get_video_duration(video_path)
        video_config = self.config.get_video_processing_config()
        chunk_duration = video_config["chunk_size_minutes"] * 60
        parallel_chunks = video_config["parallel_chunks"]
        
        logger.info(f"🔥 Starting parallel processing")
        logger.info(f"📊 Video duration: {video_duration:.1f}s, Chunk size: {chunk_duration}s")
        logger.info(f"🧵 Using {parallel_chunks} parallel workers")
        
        # Create audio chunks
        chunks = []
        current_time = 0
        chunk_index = 0
        
        temp_dir = tempfile.mkdtemp(prefix="parallel_audio_")
        
        try:
            # Extract all audio chunks first
            while current_time < video_duration:
                chunk_end = min(current_time + chunk_duration, video_duration)
                chunk_path = os.path.join(temp_dir, f"chunk_{chunk_index:04d}.wav")
                
                chunks.append({
                    "index": chunk_index,
                    "start": current_time,
                    "end": chunk_end,
                    "path": chunk_path
                })
                
                self._extract_audio_chunk(video_path, chunk_path, current_time, chunk_end)
                current_time = chunk_end
                chunk_index += 1
                
            total_chunks = len(chunks)
            logger.info(f"📦 Created {total_chunks} audio chunks for parallel processing")
            
            if progress_callback:
                progress_callback(30, f"📦 Created {total_chunks} chunks for parallel processing")
            
            # Process chunks in parallel
            all_subtitles = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_chunks) as executor:
                # Submit all chunks for processing
                future_to_chunk = {
                    executor.submit(self._process_chunk_parallel, chunk, language): chunk
                    for chunk in chunks
                }
                
                completed = 0
                for future in concurrent.futures.as_completed(future_to_chunk):
                    chunk = future_to_chunk[future]
                    
                    try:
                        chunk_subtitles = future.result()
                        
                        # Adjust timings for this chunk
                        for subtitle in chunk_subtitles:
                            subtitle["start"] += chunk["start"] + timing_offset
                            subtitle["end"] += chunk["start"] + timing_offset
                            
                            # Adjust word timings
                            for word in subtitle.get("words", []):
                                word["start"] += chunk["start"] + timing_offset
                                word["end"] += chunk["start"] + timing_offset
                        
                        all_subtitles.extend(chunk_subtitles)
                        completed += 1
                        
                        progress = 30 + int((completed / total_chunks) * 35)
                        if progress_callback:
                            progress_callback(progress, f"🔥 Processed chunk {completed}/{total_chunks}")
                            
                        logger.info(f"✅ Chunk {chunk['index']+1}/{total_chunks} completed ({len(chunk_subtitles)} segments)")
                        
                    except Exception as e:
                        logger.error(f"❌ Chunk {chunk['index']+1} failed: {e}")
            
            # Sort by start time
            all_subtitles.sort(key=lambda x: x["start"])
            
            logger.info(f"🎉 Parallel processing completed! Total segments: {len(all_subtitles)}")
            
            if progress_callback:
                progress_callback(65, f"🎉 Parallel processing completed! {len(all_subtitles)} segments")
            
            return all_subtitles
            
        finally:
            # Cleanup temporary directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _process_chunk_parallel(self, chunk: Dict, language: str) -> List[Dict[str, Any]]:
        """Process a single chunk in parallel."""
        # Each thread gets its own model instance to avoid conflicts
        chunk_model = whisper.load_model(self.current_model_name)
        
        try:
            result = chunk_model.transcribe(
                chunk["path"],
                language=language,
                word_timestamps=True,
                fp16=self.config.get_whisper_config()["fp16"],
                verbose=False  # Reduce log spam from parallel threads
            )
            
            return self._process_segments(result["segments"], 0)
            
        finally:
            # Clean up this thread's model
            del chunk_model
            gc.collect()
    
    def _process_segments(self, segments: List[Dict], timing_offset: float) -> List[Dict[str, Any]]:
        """Process Whisper segments into subtitle format."""
        subtitles = []
        
        for segment in segments:
            adjusted_start = max(0, segment["start"] + timing_offset)
            adjusted_end = max(adjusted_start + 0.1, segment["end"] + timing_offset)
            
            subtitle_segment = {
                "start": adjusted_start,
                "end": adjusted_end,
                "text": segment["text"].strip(),
                "words": []
            }
            
            # Add word-level timestamps
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
    
    def _load_model_if_needed(self, model_name: str):
        """Load Whisper model optimized for high performance."""
        if self.current_model_name == model_name and self.current_model is not None:
            logger.info(f"🎯 Model '{model_name}' already loaded")
            return
        
        # Unload current model
        if self.current_model is not None:
            logger.info(f"🔄 Unloading current model '{self.current_model_name}'")
            del self.current_model
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            gc.collect()
        
        # Load new model with performance optimizations
        logger.info(f"🚀 Loading Whisper model '{model_name}' (high-performance mode)")
        
        memory_before = psutil.virtual_memory().used / (1024**3)
        
        # Load with device optimization
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.current_model = whisper.load_model(model_name, device=device)
        self.current_model_name = model_name
        
        memory_after = psutil.virtual_memory().used / (1024**3)
        memory_used = memory_after - memory_before
        
        logger.info(f"✅ Model '{model_name}' loaded! Used {memory_used:.1f}GB RAM")
        
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds."""
        import moviepy.editor as mp
        try:
            with mp.VideoFileClip(video_path) as video:
                return video.duration
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
            return 0.0
    
    def _extract_audio_chunk(self, video_path: str, output_path: str, start_time: float, end_time: float):
        """Extract audio chunk using FFmpeg with performance optimizations."""
        import subprocess
        
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", video_path,
            "-t", str(end_time - start_time),
            "-vn",  # No video
            "-acodec", "pcm_s16le",
            "-ar", "16000",  # 16kHz for Whisper
            "-ac", "1",  # Mono
            "-threads", str(self.config.system_info["total_cpu_cores"]),
            "-loglevel", "quiet",
            output_path
        ]
        
        subprocess.run(ffmpeg_cmd, check=True)
    
    def _cleanup_memory(self):
        """Emergency memory cleanup."""
        logger.info("🧹 Performing memory cleanup")
        
        if self.current_model is not None:
            del self.current_model
            self.current_model = None
            self.current_model_name = None
        
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        gc.collect()
    
    def unload_model(self):
        """Unload the current model to free memory."""
        self._cleanup_memory()
        logger.info("🎯 Whisper model unloaded")