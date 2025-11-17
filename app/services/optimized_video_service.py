import os
import gc
import psutil
import math
import tempfile
import subprocess
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
from typing import List, Dict, Any, Tuple
import logging

# Configure logging for performance monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedVideoService:
    def __init__(self):
        self._verify_pil()
        self.memory_threshold = 0.85  # 85% memory usage triggers cleanup
        self.chunk_duration = 60  # Process videos in 60-second chunks for large files
        self.min_chunk_duration = 30  # Minimum chunk size
        
    def _verify_pil(self):
        """Verify that PIL/Pillow is available for text rendering."""
        try:
            from PIL import Image
            return True
        except ImportError:
            raise ImportError(
                "Pillow (PIL) is required for text rendering in videos. "
                "Install it with: pip install Pillow"
            )
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage."""
        return psutil.virtual_memory().percent / 100.0
    
    def _should_use_chunked_processing(self, video_path: str) -> bool:
        """Determine if video should be processed in chunks based on duration and memory."""
        try:
            with VideoFileClip(video_path) as video:
                duration = video.duration
                
            # Use chunked processing for videos longer than 5 minutes OR if memory is already high
            return duration > 300 or self._get_memory_usage() > 0.6
        except Exception:
            return True  # Default to chunked processing if we can't determine
    
    def _get_optimal_chunk_size(self, total_duration: float) -> float:
        """Calculate optimal chunk size based on memory usage and video duration."""
        memory_usage = self._get_memory_usage()
        
        if memory_usage > 0.8:
            return self.min_chunk_duration  # Use smallest chunks if memory is tight
        elif memory_usage > 0.6:
            return 45  # Medium chunks for moderate memory usage
        elif total_duration > 1800:  # 30+ minutes
            return self.min_chunk_duration
        elif total_duration > 600:   # 10+ minutes
            return 45
        else:
            return self.chunk_duration
    
    def _cleanup_memory(self):
        """Force garbage collection to free memory."""
        gc.collect()
        logger.info(f"Memory usage after cleanup: {self._get_memory_usage():.2%}")
    
    def add_subtitles_to_video(self, video_path: str, subtitles: List[Dict[str, Any]], 
                             output_path: str, settings: Dict[str, Any], word_level_mode: str = "off") -> str:
        """
        Add subtitles to video with memory optimization for large videos.
        """
        try:
            # Check if we should use chunked processing
            if self._should_use_chunked_processing(video_path):
                logger.info("Using chunked processing for large video")
                return self._add_subtitles_chunked(video_path, subtitles, output_path, settings, word_level_mode)
            else:
                logger.info("Using standard processing for small video")
                return self._add_subtitles_standard(video_path, subtitles, output_path, settings, word_level_mode)
                
        except Exception as e:
            self._cleanup_memory()
            raise Exception(f"Error adding subtitles to video: {str(e)}")
    
    def _add_subtitles_chunked(self, video_path: str, subtitles: List[Dict[str, Any]], 
                              output_path: str, settings: Dict[str, Any], word_level_mode: str) -> str:
        """Process large videos in chunks to manage memory usage."""
        
        # Get video duration and determine chunk size
        with VideoFileClip(video_path) as video:
            total_duration = video.duration
            
        chunk_duration = self._get_optimal_chunk_size(total_duration)
        logger.info(f"Processing {total_duration:.1f}s video in {chunk_duration}s chunks")
        
        # Create temporary directory for chunks
        temp_dir = tempfile.mkdtemp(prefix="video_chunks_")
        chunk_files = []
        
        try:
            # Process video in chunks
            current_time = 0
            chunk_index = 0
            
            while current_time < total_duration:
                chunk_end = min(current_time + chunk_duration, total_duration)
                
                logger.info(f"Processing chunk {chunk_index + 1}: {current_time:.1f}s - {chunk_end:.1f}s")
                
                # Extract chunk subtitles
                chunk_subtitles = self._extract_subtitles_for_timerange(
                    subtitles, current_time, chunk_end
                )
                
                # Process this chunk
                chunk_output = os.path.join(temp_dir, f"chunk_{chunk_index:04d}.mp4")
                self._process_video_chunk(
                    video_path, chunk_subtitles, chunk_output, 
                    settings, word_level_mode, current_time, chunk_end
                )
                
                chunk_files.append(chunk_output)
                chunk_index += 1
                current_time = chunk_end
                
                # Cleanup memory after each chunk
                self._cleanup_memory()
                
                # Check memory usage and adjust chunk size if needed
                if self._get_memory_usage() > self.memory_threshold:
                    chunk_duration = max(self.min_chunk_duration, chunk_duration * 0.8)
                    logger.warning(f"High memory usage detected, reducing chunk size to {chunk_duration}s")
            
            # Concatenate all chunks using FFmpeg (more memory efficient than MoviePy)
            logger.info(f"Concatenating {len(chunk_files)} chunks")
            self._concatenate_chunks_ffmpeg(chunk_files, output_path)
            
            return output_path
            
        finally:
            # Cleanup temporary files
            for chunk_file in chunk_files:
                if os.path.exists(chunk_file):
                    os.remove(chunk_file)
            os.rmdir(temp_dir)
            self._cleanup_memory()
    
    def _add_subtitles_standard(self, video_path: str, subtitles: List[Dict[str, Any]], 
                               output_path: str, settings: Dict[str, Any], word_level_mode: str) -> str:
        """Standard subtitle processing for smaller videos."""
        
        video = VideoFileClip(video_path)
        subtitle_clips = []
        
        try:
            logger.info(f"Processing with mode: {word_level_mode}")
            
            if word_level_mode == "off":
                subtitle_clips = self._create_sentence_clips(subtitles, video.size, settings)
            elif word_level_mode == "karaoke":
                subtitle_clips = self._create_karaoke_clips_optimized(subtitles, video.size, settings)
            elif word_level_mode == "popup":
                subtitle_clips = self._create_popup_word_clips(subtitles, video.size, settings)
            elif word_level_mode == "typewriter":
                subtitle_clips = self._create_typewriter_clips(subtitles, video.size, settings)
            
            # Composite video with subtitles
            if subtitle_clips:
                final_video = CompositeVideoClip([video] + subtitle_clips)
            else:
                final_video = video
            
            # Use optimized encoding settings for performance
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                preset='ultrafast',  # Faster encoding
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None,
                threads=1  # Single thread for memory efficiency
            )
            
            return output_path
            
        finally:
            # Clean up all clips
            video.close()
            if 'final_video' in locals():
                final_video.close()
            for clip in subtitle_clips:
                if hasattr(clip, 'close'):
                    clip.close()
            self._cleanup_memory()
    
    def _extract_subtitles_for_timerange(self, subtitles: List[Dict[str, Any]], 
                                        start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Extract subtitles that fall within the specified time range."""
        chunk_subtitles = []
        
        for subtitle in subtitles:
            # Check if subtitle overlaps with chunk timerange
            sub_start = subtitle["start"]
            sub_end = subtitle["end"]
            
            if sub_start < end_time and sub_end > start_time:
                # Adjust timing relative to chunk start
                adjusted_subtitle = subtitle.copy()
                adjusted_subtitle["start"] = max(0, sub_start - start_time)
                adjusted_subtitle["end"] = min(end_time - start_time, sub_end - start_time)
                
                # Adjust word timings if present
                if "words" in subtitle and subtitle["words"]:
                    adjusted_words = []
                    for word in subtitle["words"]:
                        if word["start"] < end_time and word["end"] > start_time:
                            adjusted_word = word.copy()
                            adjusted_word["start"] = max(0, word["start"] - start_time)
                            adjusted_word["end"] = min(end_time - start_time, word["end"] - start_time)
                            adjusted_words.append(adjusted_word)
                    adjusted_subtitle["words"] = adjusted_words
                
                chunk_subtitles.append(adjusted_subtitle)
        
        return chunk_subtitles
    
    def _process_video_chunk(self, video_path: str, subtitles: List[Dict[str, Any]], 
                           output_path: str, settings: Dict[str, Any], word_level_mode: str,
                           start_time: float, end_time: float):
        """Process a single chunk of video with subtitles."""
        
        # Extract video chunk
        video = VideoFileClip(video_path).subclip(start_time, end_time)
        
        try:
            # Create subtitle clips for this chunk
            subtitle_clips = []
            
            if word_level_mode == "off":
                subtitle_clips = self._create_sentence_clips(subtitles, video.size, settings)
            elif word_level_mode == "karaoke":
                subtitle_clips = self._create_karaoke_clips_optimized(subtitles, video.size, settings)
            elif word_level_mode == "popup":
                subtitle_clips = self._create_popup_word_clips(subtitles, video.size, settings)
            elif word_level_mode == "typewriter":
                subtitle_clips = self._create_typewriter_clips(subtitles, video.size, settings)
            
            # Composite and save chunk
            if subtitle_clips:
                chunk_video = CompositeVideoClip([video] + subtitle_clips)
            else:
                chunk_video = video
            
            chunk_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                preset='ultrafast',
                verbose=False,
                logger=None,
                threads=1
            )
            
        finally:
            video.close()
            if 'chunk_video' in locals():
                chunk_video.close()
            for clip in subtitle_clips:
                if hasattr(clip, 'close'):
                    clip.close()
    
    def _concatenate_chunks_ffmpeg(self, chunk_files: List[str], output_path: str):
        """Concatenate video chunks using FFmpeg for memory efficiency."""
        
        # Create a text file listing all chunks
        list_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        
        try:
            for chunk_file in chunk_files:
                list_file.write(f"file '{chunk_file}'\n")
            list_file.close()
            
            # Use FFmpeg to concatenate
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', list_file.name,
                '-c', 'copy',  # Copy streams without re-encoding
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg concatenation failed: {result.stderr}")
                
        finally:
            os.unlink(list_file.name)
    
    def _create_sentence_clips(self, subtitles: List[Dict[str, Any]], video_size: tuple, 
                              settings: Dict[str, Any]) -> List:
        """Create sentence-level subtitle clips with memory optimization."""
        clips = []
        
        from app.services.subtitle_service import SubtitleService
        subtitle_service = SubtitleService()
        
        for subtitle in subtitles:
            formatted_text = subtitle_service.format_text_for_video(
                subtitle["text"], 
                settings.get("max-words-per-line", 4)
            )
            
            txt_clip = self._create_styled_text_clip_optimized(
                formatted_text,
                video_size,
                settings,
                duration=subtitle["end"] - subtitle["start"]
            ).set_start(subtitle["start"])
            
            clips.append(txt_clip)
        
        return clips
    
    def _create_karaoke_clips_optimized(self, subtitles: List[Dict[str, Any]], video_size: tuple, 
                                       settings: Dict[str, Any]) -> List:
        """Create optimized karaoke clips with batch processing."""
        clips = []
        
        # Process in smaller batches to manage memory
        batch_size = 10  # Process 10 subtitles at a time
        
        for i in range(0, len(subtitles), batch_size):
            batch = subtitles[i:i + batch_size]
            
            for subtitle in batch:
                if not subtitle.get("words"):
                    continue
                
                # Create word highlight clips
                for word in subtitle["words"]:
                    word_text = word["word"].strip()
                    if word_text:
                        highlight_clip = self._create_styled_text_clip_optimized(
                            word_text,
                            video_size,
                            {
                                **settings, 
                                "line-color": settings.get("normal-color", "#FFFFFF"),
                                "outline-width": settings.get("outline-width", 10) + 2,
                                "font-size": max(60, settings.get("font-size", 120) - 20)  # Smaller font for memory
                            },
                            duration=word["end"] - word["start"]
                        ).set_start(word["start"])
                        
                        clips.append(highlight_clip)
            
            # Cleanup after each batch
            if self._get_memory_usage() > self.memory_threshold:
                self._cleanup_memory()
        
        return clips
    
    def _create_styled_text_clip_optimized(self, text: str, video_size: Tuple[int, int], 
                                          settings: Dict[str, Any], duration: float) -> TextClip:
        """Create optimized text clip with reduced memory usage."""
        
        position_map = {
            "top-left": ("left", "top"),
            "top-center": ("center", "top"), 
            "top-right": ("right", "top"),
            "center-left": ("left", "center"),
            "center-center": ("center", "center"),
            "center-right": ("right", "center"),
            "bottom-left": ("left", "bottom"),
            "bottom-center": ("center", "bottom"),
            "bottom-right": ("right", "bottom")
        }
        
        position = settings.get("position", "bottom-center")
        h_align, v_align = position_map.get(position, ("center", "bottom"))
        
        # Use smaller font sizes for memory efficiency
        font_size = min(settings.get("font-size", 80), 80)  # Cap at 80px
        
        # Use simpler font to reduce memory
        font_requested = "DejaVu-Sans-Bold"  # Always use simple font for optimization
        
        txt_clip = TextClip(
            text,
            fontsize=font_size,
            font=font_requested,
            color=settings.get("line-color", "#FFFFFF"),
            stroke_color=settings.get("outline-color", "#000000"),
            stroke_width=min(settings.get("outline-width", 3), 5),  # Limit outline width
            method='label'  # Always use label for memory efficiency
        ).set_duration(duration)
        
        # Set position
        if h_align == "center" and v_align == "bottom":
            txt_clip = txt_clip.set_position(('center', video_size[1] - 100))
        elif h_align == "center" and v_align == "center":
            txt_clip = txt_clip.set_position(('center', video_size[1] // 2))
        elif h_align == "center" and v_align == "top":
            txt_clip = txt_clip.set_position(('center', 50))
        else:
            x_pos = "center" if h_align == "center" else (50 if h_align == "left" else video_size[0] - 50)
            y_pos = (video_size[1] // 2) if v_align == "center" else (50 if v_align == "top" else video_size[1] - 100)
            txt_clip = txt_clip.set_position((x_pos, y_pos))
        
        return txt_clip
    
    def _create_popup_word_clips(self, subtitles: List[Dict[str, Any]], video_size: tuple, 
                                settings: Dict[str, Any]) -> List:
        """Create popup word clips with memory optimization."""
        clips = []
        
        for subtitle in subtitles:
            if not subtitle.get("words"):
                continue
                
            for word in subtitle["words"]:
                word_clip = self._create_styled_text_clip_optimized(
                    word["word"].strip(),
                    video_size,
                    settings,
                    duration=word["end"] - word["start"]
                ).set_start(word["start"])
                
                clips.append(word_clip)
        
        return clips
    
    def _create_typewriter_clips(self, subtitles: List[Dict[str, Any]], video_size: tuple, 
                               settings: Dict[str, Any]) -> List:
        """Create typewriter clips with memory optimization."""
        clips = []
        
        for subtitle in subtitles:
            if not subtitle.get("words"):
                continue
                
            accumulated_text = ""
            
            for word in subtitle["words"]:
                accumulated_text += word["word"]
                
                typewriter_clip = self._create_styled_text_clip_optimized(
                    accumulated_text.strip(),
                    video_size,
                    settings,
                    duration=word["end"] - word["start"]
                ).set_start(word["start"])
                
                clips.append(typewriter_clip)
        
        return clips
    
    # Include optimized versions of other methods from the original VideoService
    def split_video(self, video_path: str, start_time: float, end_time: float, output_path: str) -> str:
        """Split video with memory optimization."""
        try:
            video = VideoFileClip(video_path)
            
            if start_time < 0:
                start_time = 0
            if end_time > video.duration:
                end_time = video.duration
            if start_time >= end_time:
                raise ValueError("Start time must be less than end time")
            
            split_video = video.subclip(start_time, end_time)
            
            split_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                preset='ultrafast',
                verbose=False,
                logger=None,
                threads=1
            )
            
            video.close()
            split_video.close()
            self._cleanup_memory()
            
            return output_path
            
        except Exception as e:
            self._cleanup_memory()
            raise Exception(f"Error splitting video: {str(e)}")
    
    def join_videos(self, video_paths: List[str], output_path: str) -> str:
        """Join videos with memory optimization using FFmpeg when possible."""
        try:
            # For large number of videos or memory constraints, use FFmpeg
            if len(video_paths) > 3 or self._get_memory_usage() > 0.6:
                return self._join_videos_ffmpeg(video_paths, output_path)
            
            # Use MoviePy for small joins
            video_clips = []
            for path in video_paths:
                if os.path.exists(path):
                    clip = VideoFileClip(path)
                    video_clips.append(clip)
                else:
                    raise FileNotFoundError(f"Video file not found: {path}")
            
            if not video_clips:
                raise ValueError("No valid video clips to join")
            
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                preset='ultrafast',
                verbose=False,
                logger=None,
                threads=1
            )
            
            for clip in video_clips:
                clip.close()
            final_video.close()
            self._cleanup_memory()
            
            return output_path
            
        except Exception as e:
            self._cleanup_memory()
            raise Exception(f"Error joining videos: {str(e)}")
    
    def _join_videos_ffmpeg(self, video_paths: List[str], output_path: str) -> str:
        """Join videos using FFmpeg for better memory efficiency."""
        list_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        
        try:
            for video_path in video_paths:
                list_file.write(f"file '{video_path}'\n")
            list_file.close()
            
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', list_file.name,
                '-c', 'copy',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg join failed: {result.stderr}")
                
            return output_path
            
        finally:
            os.unlink(list_file.name)
    
    def add_music_to_video(self, video_path: str, music_path: str, output_path: str, 
                          settings: Dict[str, Any]) -> str:
        """Add music with memory optimization."""
        try:
            video = VideoFileClip(video_path)
            music = AudioFileClip(music_path)
            
            volume = settings.get("volume", 0.5)
            fade_in = settings.get("fade_in", 0)
            fade_out = settings.get("fade_out", 0)
            loop_music = settings.get("loop_music", False)
            
            music = music.volumex(volume)
            
            if loop_music and music.duration < video.duration:
                loops_needed = math.ceil(video.duration / music.duration)
                # Instead of concatenating in memory, trim and loop more efficiently
                if loops_needed > 1:
                    music = music.loop(duration=video.duration)
            
            if music.duration > video.duration:
                music = music.subclip(0, video.duration)
            
            if fade_in > 0:
                music = music.fadein(fade_in)
            if fade_out > 0:
                music = music.fadeout(fade_out)
            
            if video.audio is not None:
                from moviepy.audio.fx import CompositeAudioClip
                final_audio = CompositeAudioClip([video.audio, music])
            else:
                final_audio = music
            
            final_video = video.set_audio(final_audio)
            
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                preset='ultrafast',
                verbose=False,
                logger=None,
                threads=1
            )
            
            video.close()
            music.close()
            final_video.close()
            self._cleanup_memory()
            
            return output_path
            
        except Exception as e:
            self._cleanup_memory()
            raise Exception(f"Error adding music to video: {str(e)}")