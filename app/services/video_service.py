from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
import os
from typing import List, Dict, Any, Tuple
import math

class VideoService:
    def __init__(self):
        # PIL/Pillow verification - check if it's available for text rendering
        self._verify_pil()
    
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
    
    def add_subtitles_to_video(self, video_path: str, subtitles: List[Dict[str, Any]], 
                             output_path: str, settings: Dict[str, Any], word_level_mode: str = "off") -> str:
        """
        Add subtitles to a video with custom styling.
        
        Args:
            video_path: Path to input video
            subtitles: List of subtitle segments with timing and text
            output_path: Path for output video
            settings: Styling settings for subtitles
            word_level_mode: Word-level display mode ("off", "karaoke", "popup", "typewriter")
            
        Returns:
            Path to the output video
        """
        try:
            # Load the video
            video = VideoFileClip(video_path)
            
            # Create subtitle clips based on mode
            subtitle_clips = []
            
            print(f"🎬 Video processing mode: '{word_level_mode}'")
            
            if word_level_mode == "off":
                # Traditional sentence-level subtitles
                for subtitle in subtitles:
                    # Format text for display
                    from app.services.subtitle_service import SubtitleService
                    subtitle_service = SubtitleService()
                    formatted_text = subtitle_service.format_text_for_video(
                        subtitle["text"], 
                        settings.get("max-words-per-line", 4)
                    )
                    
                    # Create text clip with styling
                    txt_clip = self._create_styled_text_clip(
                        formatted_text,
                        video.size,
                        settings,
                        duration=subtitle["end"] - subtitle["start"]
                    ).set_start(subtitle["start"])
                    
                    subtitle_clips.append(txt_clip)
            
            elif word_level_mode == "karaoke":
                # Karaoke-style word highlighting
                subtitle_clips.extend(self._create_karaoke_clips(subtitles, video.size, settings))
                
            elif word_level_mode == "popup":
                # Pop-up individual words
                subtitle_clips.extend(self._create_popup_word_clips(subtitles, video.size, settings))
                
            elif word_level_mode == "typewriter":
                # Typewriter accumulating words
                subtitle_clips.extend(self._create_typewriter_clips(subtitles, video.size, settings))
            
            # Composite video with subtitles
            if subtitle_clips:
                final_video = CompositeVideoClip([video] + subtitle_clips)
            else:
                final_video = video
            
            # Write output video
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # Clean up
            video.close()
            final_video.close()
            for clip in subtitle_clips:
                clip.close()
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error adding subtitles to video: {str(e)}")
    
    def _create_styled_text_clip(self, text: str, video_size: Tuple[int, int], 
                               settings: Dict[str, Any], duration: float) -> TextClip:
        """Create a styled text clip based on settings."""
        
        # Position mapping
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
        
        position = settings.get("position", "center-center")
        h_align, v_align = position_map.get(position, ("center", "center"))
        
        print(f"📋 Position requested: '{position}' -> h_align='{h_align}', v_align='{v_align}'")
        
        # Create base text clip
        font_requested = settings.get("font-family", "DejaVu-Sans-Bold")
        
        # Use full path for Luckiest Guy to ensure it's found
        if font_requested == "Luckiest Guy":
            font_path = "/usr/share/fonts/truetype/luckiest-guy/LuckiestGuy-Regular.ttf"
            print(f"🔤 FONT DEBUG: Using full path for Luckiest Guy: '{font_path}'")
            font_requested = font_path
        
        print(f"🔤 FONT DEBUG: Final font: '{font_requested}'")
        print(f"🔤 FONT DEBUG: Text: '{text}'")
        print(f"🔤 FONT DEBUG: Method: {'caption' if len(text) > 50 else 'label'}")
        
        txt_clip = TextClip(
            text,
            fontsize=settings.get("font-size", 100),
            font=font_requested,
            color=settings.get("line-color", "#FFFFFF"),
            stroke_color=settings.get("outline-color", "#000000"),
            stroke_width=settings.get("outline-width", 3),
            method='caption' if len(text) > 50 else 'label'
        ).set_duration(duration)
        
        # Set position based on alignment with explicit pixel calculations
        if h_align == "center" and v_align == "center":
            # True vertical and horizontal centering - calculate exact pixel position
            x_pos = 'center'
            y_pos = video_size[1] // 2  # Exact vertical center in pixels
            txt_clip = txt_clip.set_position((x_pos, y_pos))
            print(f"🎯 Setting subtitle to TRUE CENTER: x='center', y={y_pos} (video height: {video_size[1]})")
            
        elif h_align == "center" and v_align == "bottom":
            txt_clip = txt_clip.set_position(('center', video_size[1] - 150))
            print(f"🔻 Setting subtitle to BOTTOM: x='center', y={video_size[1] - 150}")
            
        elif h_align == "center" and v_align == "top":
            txt_clip = txt_clip.set_position(('center', 50))
            print(f"🔺 Setting subtitle to TOP: x='center', y=50")
            
        else:
            # Handle other positions
            x_pos = "center" if h_align == "center" else (50 if h_align == "left" else video_size[0] - 50)
            y_pos = (video_size[1] // 2) if v_align == "center" else (50 if v_align == "top" else video_size[1] - 150)
            txt_clip = txt_clip.set_position((x_pos, y_pos))
            print(f"📍 Setting subtitle to CUSTOM: x={x_pos}, y={y_pos}")
        
        return txt_clip
    
    def _create_karaoke_clips(self, subtitles: List[Dict[str, Any]], video_size: tuple, settings: Dict[str, Any]) -> List:
        """Create karaoke-style subtitle clips with word highlighting."""
        clips = []
        
        highlight_color = settings.get("highlight_color", "#FFFF00")
        normal_color = settings.get("line-color", "#FFFFFF")
        
        print(f"🎤 Creating karaoke clips with highlight color: {highlight_color}")
        print(f"🎤 Total subtitles to process: {len(subtitles)}")
        
        karaoke_clips_created = 0
        sentence_fallbacks = 0
        
        for i, subtitle in enumerate(subtitles):
            if not subtitle.get("words"):
                print(f"   ⚠️  Subtitle {i+1} has NO word data - creating sentence fallback")
                sentence_fallbacks += 1
                
                # Fallback to sentence-level subtitle for this segment
                formatted_text = subtitle_service.format_text_for_video(
                    subtitle["text"], 
                    settings.get("max-words-per-line", 4)
                )
                
                sentence_clip = self._create_styled_text_clip(
                    formatted_text,
                    video_size,
                    {**settings, "line-color": normal_color},
                    duration=subtitle["end"] - subtitle["start"]
                ).set_start(subtitle["start"])
                
                clips.append(sentence_clip)
                continue
            
            print(f"   ✅ Subtitle {i+1} has {len(subtitle['words'])} words for karaoke")
            karaoke_clips_created += 1
                
            # Skip background text clip - show only individual highlighted words
            
            # Create individual word highlights that appear only when that word is spoken
            for word in subtitle["words"]:
                word_text = word["word"].strip()
                if word_text:
                    # Create highlighted word overlay
                    highlight_clip = self._create_styled_text_clip(
                        word_text,
                        video_size,
                        {
                            **settings, 
                            "line-color": highlight_color,
                            "stroke_width": settings.get("stroke_width", 3) + 2,  # Thicker stroke for visibility
                            "font-size": settings.get("font-size", 100) + 5  # Slightly larger for emphasis
                        },
                        duration=word["end"] - word["start"]
                    ).set_start(word["start"])
                    
                    clips.append(highlight_clip)
        
        print(f"🎤 Karaoke summary: {karaoke_clips_created} segments with words, {sentence_fallbacks} sentence fallbacks")
        print(f"🎤 Total clips created: {len(clips)}")
        
        return clips
    
    def _create_popup_word_clips(self, subtitles: List[Dict[str, Any]], video_size: tuple, settings: Dict[str, Any]) -> List:
        """Create pop-up style clips showing one word at a time."""
        clips = []
        
        for subtitle in subtitles:
            if not subtitle.get("words"):
                continue
                
            for word in subtitle["words"]:
                # Create individual word clip
                word_clip = self._create_styled_text_clip(
                    word["word"].strip(),
                    video_size,
                    settings,
                    duration=word["end"] - word["start"]
                ).set_start(word["start"])
                
                clips.append(word_clip)
        
        return clips
    
    def _create_typewriter_clips(self, subtitles: List[Dict[str, Any]], video_size: tuple, settings: Dict[str, Any]) -> List:
        """Create typewriter style clips that build text word by word."""
        clips = []
        
        for subtitle in subtitles:
            if not subtitle.get("words"):
                continue
                
            accumulated_text = ""
            
            for i, word in enumerate(subtitle["words"]):
                accumulated_text += word["word"]
                
                # Create clip with accumulated text
                typewriter_clip = self._create_styled_text_clip(
                    accumulated_text.strip(),
                    video_size,
                    settings,
                    duration=word["end"] - word["start"]
                ).set_start(word["start"])
                
                clips.append(typewriter_clip)
        
        return clips
    
    def split_video(self, video_path: str, start_time: float, end_time: float, output_path: str) -> str:
        """
        Split a video from start_time to end_time.
        
        Args:
            video_path: Path to input video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Path for output video
            
        Returns:
            Path to the output video
        """
        try:
            # Load video
            video = VideoFileClip(video_path)
            
            # Validate times
            if start_time < 0:
                start_time = 0
            if end_time > video.duration:
                end_time = video.duration
            if start_time >= end_time:
                raise ValueError("Start time must be less than end time")
            
            # Split video
            split_video = video.subclip(start_time, end_time)
            
            # Write output
            split_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            
            # Clean up
            video.close()
            split_video.close()
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error splitting video: {str(e)}")
    
    def join_videos(self, video_paths: List[str], output_path: str) -> str:
        """
        Join multiple videos into one.
        
        Args:
            video_paths: List of paths to video files
            output_path: Path for output video
            
        Returns:
            Path to the output video
        """
        try:
            # Load all videos
            video_clips = []
            for path in video_paths:
                if os.path.exists(path):
                    clip = VideoFileClip(path)
                    video_clips.append(clip)
                else:
                    raise FileNotFoundError(f"Video file not found: {path}")
            
            if not video_clips:
                raise ValueError("No valid video clips to join")
            
            # Concatenate videos
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # Write output
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            
            # Clean up
            for clip in video_clips:
                clip.close()
            final_video.close()
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error joining videos: {str(e)}")
    
    def add_music_to_video(self, video_path: str, music_path: str, output_path: str, 
                          settings: Dict[str, Any]) -> str:
        """
        Add background music to a video.
        
        Args:
            video_path: Path to input video
            music_path: Path to music file
            output_path: Path for output video
            settings: Music settings (volume, fade_in, fade_out, loop_music)
            
        Returns:
            Path to the output video
        """
        try:
            # Load video and audio
            video = VideoFileClip(video_path)
            music = AudioFileClip(music_path)
            
            # Get settings
            volume = settings.get("volume", 0.5)
            fade_in = settings.get("fade_in", 0)
            fade_out = settings.get("fade_out", 0)
            loop_music = settings.get("loop_music", False)
            
            # Adjust music volume
            music = music.volumex(volume)
            
            # Loop music if requested and video is longer
            if loop_music and music.duration < video.duration:
                # Calculate how many times to loop
                loops_needed = math.ceil(video.duration / music.duration)
                music_clips = [music] * loops_needed
                music = concatenate_audioclips(music_clips)
            
            # Trim music to video length
            if music.duration > video.duration:
                music = music.subclip(0, video.duration)
            
            # Apply fade effects
            if fade_in > 0:
                music = music.fadeout(fade_in)
            if fade_out > 0:
                music = music.fadeout(fade_out)
            
            # Composite original audio with music
            if video.audio is not None:
                # Mix original audio with music
                final_audio = CompositeAudioClip([video.audio, music])
            else:
                # Use only music
                final_audio = music
            
            # Create final video
            final_video = video.set_audio(final_audio)
            
            # Write output
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            
            # Clean up
            video.close()
            music.close()
            final_video.close()
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error adding music to video: {str(e)}")
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get information about a video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video information
        """
        try:
            video = VideoFileClip(video_path)
            
            info = {
                "duration": video.duration,
                "fps": video.fps,
                "size": video.size,
                "width": video.w,
                "height": video.h,
                "has_audio": video.audio is not None
            }
            
            video.close()
            return info
            
        except Exception as e:
            raise Exception(f"Error getting video info: {str(e)}")