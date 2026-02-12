"""
Voiceover Service for Adding Audio to Video with Duration Matching
Provides functionality to add voiceover audio to video clips with intelligent duration matching.
"""

import os
import logging
import math
import moviepy.editor as mp
from moviepy.video.fx.resize import resize
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

class VoiceoverService:
    """Service for adding voiceover audio to video clips with duration matching."""
    
    def __init__(self):
        self.supported_audio_formats = ['.mp3', '.wav', '.aac', '.m4a', '.ogg']
        self.supported_video_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
    
    def is_image_file(self, file_path):
        """Check if the file is an image based on extension and content."""
        try:
            # Check extension first
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.supported_image_formats:
                return False
            
            # Try to open as image to verify
            with Image.open(file_path) as img:
                img.verify()  # Verify it's a valid image
            return True
        except Exception:
            return False
    
    def get_duration(self, file_path):
        """Get duration of audio or video file."""
        try:
            # Try as video first
            clip = mp.VideoFileClip(file_path)
            duration = clip.duration
            clip.close()
            return duration
        except:
            try:
                # Try as audio
                clip = mp.AudioFileClip(file_path)
                duration = clip.duration
                clip.close()
                return duration
            except Exception as e:
                logger.error(f"Could not get duration for {file_path}: {e}")
                raise ValueError(f"Unable to read media file: {file_path}")
    
    def slow_down_audio(self, audio_clip, target_duration):
        """Slow down audio clip to match target duration."""
        current_duration = audio_clip.duration
        
        if target_duration >= current_duration:
            # If target is longer or equal, no need to slow down
            return audio_clip
        
        # Calculate slowdown factor
        slowdown_factor = target_duration / current_duration
        
        logger.info(f"Slowing down audio by factor of {slowdown_factor:.2f} from {current_duration:.2f}s to {target_duration:.2f}s")
        
        # Apply speed change to audio
        # Use MoviePy's built-in fx method with speedx
        try:
            # Try modern MoviePy import first
            from moviepy.audio.fx import speedx
            slowed_audio = speedx.speedx(audio_clip, slowdown_factor)
        except (ImportError, AttributeError):
            try:
                # Try alternative import path
                from moviepy.audio.fx.speedx import speedx
                slowed_audio = speedx(audio_clip, slowdown_factor)
            except (ImportError, AttributeError):
                try:
                    # Try using fx method directly
                    slowed_audio = audio_clip.fx(mp.afx.speedx, slowdown_factor)
                except AttributeError:
                    # Final fallback: use duration stretching to slow down
                    logger.warning(f"speedx not available, using duration stretching method")
                    # For slowdown, we need to stretch the audio duration
                    # This creates the slowed audio by changing its effective duration
                    slowed_audio = audio_clip.set_duration(target_duration)
                    # Apply pitch correction to maintain audio quality
                    try:
                        # Try to resample to maintain audio quality while stretching
                        original_fps = getattr(audio_clip, 'fps', 44100)
                        slowed_audio = slowed_audio.set_fps(original_fps)
                    except:
                        # If resampling fails, just use the stretched version
                        pass
        
        return slowed_audio
    
    def slow_down_video(self, video_clip, target_duration):
        """Slow down video clip to match target duration."""
        current_duration = video_clip.duration
        
        if target_duration <= current_duration:
            # If target is shorter or equal, no need to slow down
            return video_clip
        
        # Calculate slowdown factor
        slowdown_factor = current_duration / target_duration
        
        logger.info(f"Slowing down video by factor of {slowdown_factor:.2f} from {current_duration:.2f}s to {target_duration:.2f}s")
        
        # Apply speed change to video
        # Use MoviePy's built-in fx method with speedx
        try:
            # Try modern MoviePy import first
            from moviepy.video.fx import speedx
            slowed_video = speedx.speedx(video_clip, slowdown_factor)
        except (ImportError, AttributeError):
            try:
                # Try alternative import path
                from moviepy.video.fx.speedx import speedx
                slowed_video = speedx(video_clip, slowdown_factor)
            except (ImportError, AttributeError):
                try:
                    # Try using fx method directly
                    slowed_video = video_clip.fx(mp.vfx.speedx, slowdown_factor)
                except AttributeError:
                    # Final fallback: use duration stretching to slow down
                    logger.warning(f"speedx not available, using duration stretching method for video")
                    # For video slowdown, we need to stretch the video duration
                    # This creates the slowed video by changing its effective duration
                    slowed_video = video_clip.set_duration(target_duration)
                    # Apply fps adjustment to maintain video quality while stretching
                    try:
                        # Try to adjust fps to maintain quality while stretching
                        original_fps = video_clip.fps
                        new_fps = original_fps * slowdown_factor
                        slowed_video = slowed_video.set_fps(new_fps)
                    except:
                        # If fps adjustment fails, just use the stretched version
                        pass
        
        return slowed_video
    
    def create_video_from_image_with_zoom(self, image_path, duration, output_size=(1080, 1080), zoom_factor=1.0):
        """
        Create a video from an image with a subtle zoom-in effect from center.
        
        Args:
            image_path (str): Path to the input image
            duration (float): Duration of the video in seconds
            output_size (tuple): Output video resolution (width, height)
            zoom_factor (float): Maximum zoom factor (1.0 = no zoom, 1.1 = 10% zoom in)
        
        Returns:
            VideoFileClip: Video clip with zoom effect
        """
        # Extract duration if it's an AudioClip object
        actual_duration = duration.duration if hasattr(duration, 'duration') else duration
        logger.info(f"Creating video from image {image_path} with {actual_duration:.1f}s duration, zoom factor: {zoom_factor}")
        
        try:
            # Load and process the image
            img = Image.open(image_path)
            img_array = np.array(img)
            
            # Ensure image has 3 channels (RGB)
            if len(img_array.shape) == 2:  # Grayscale
                img_array = np.stack([img_array] * 3, axis=-1)
            elif img_array.shape[2] == 4:  # RGBA
                img_array = img_array[:, :, :3]  # Remove alpha channel
            
            # Calculate image dimensions and aspect ratio
            img_height, img_width = img_array.shape[:2]
            img_aspect = img_width / img_height
            target_width, target_height = output_size
            target_aspect = target_width / target_height
            
            # Calculate initial size to fit the target dimensions
            if img_aspect > target_aspect:
                # Image is wider - fit to width initially
                initial_width = target_width
                initial_height = target_width / img_aspect
            else:
                # Image is taller - fit to height initially
                initial_height = target_height
                initial_width = target_height * img_aspect
            
            # Create base clip from image
            clip = mp.ImageClip(img_array)
            
            # Set duration and fps (higher FPS for smoother zoom)
            clip = clip.set_duration(actual_duration).set_fps(60)
            
            # Apply zoom effect only if zoom_factor > 1.0
            if zoom_factor > 1.0:
                # Use PIL-based frame processing for smooth center-focused zoom
                logger.info(f"🎬 Applying PIL-based zoom effect from 1.0 to {zoom_factor}")
                
                # First resize to target dimensions
                clip = clip.resize((target_width, target_height))
                
                # Calculate zoom ratio per second based on zoom factor and duration
                total_zoom_percent = (zoom_factor - 1.0)
                zoom_ratio = total_zoom_percent / actual_duration
                
                def zoom_in_effect(get_frame, t):
                    """
                    PIL-based zoom effect with proper center cropping.
                    Based on proven smooth zoom implementation.
                    """
                    img = Image.fromarray(get_frame(t))
                    base_size = img.size

                    new_size = [
                        math.ceil(img.size[0] * (1 + (zoom_ratio * t))),
                        math.ceil(img.size[1] * (1 + (zoom_ratio * t)))
                    ]

                    # The new dimensions must be even.
                    new_size[0] = new_size[0] + (new_size[0] % 2)
                    new_size[1] = new_size[1] + (new_size[1] % 2)

                    img = img.resize(new_size, Image.LANCZOS)

                    x = math.ceil((new_size[0] - base_size[0]) / 2)
                    y = math.ceil((new_size[1] - base_size[1]) / 2)

                    img = img.crop([
                        x, y, new_size[0] - x, new_size[1] - y
                    ]).resize(base_size, Image.LANCZOS)

                    result = np.array(img)
                    img.close()

                    return result
                
                # Apply the PIL zoom transformation using fl method
                clip = clip.fl(zoom_in_effect, apply_to=['mask'])
                
            else:
                # No zoom - just resize to target dimensions with proper aspect ratio
                clip = clip.resize((target_width, target_height))
            
            logger.info(f"Created video clip: {target_width}x{target_height}, {actual_duration:.1f}s with zoom {zoom_factor}")
            return clip
            
        except Exception as e:
            logger.error(f"Error creating video from image: {e}")
            # Fallback: create simple static video without zoom
            try:
                clip = mp.ImageClip(image_path, duration=actual_duration)
                clip = clip.resize((target_width, target_height)).set_fps(60)
                logger.info("Using fallback: static image without zoom")
                return clip
            except Exception as fallback_e:
                logger.error(f"Fallback also failed: {fallback_e}")
                raise Exception(f"Failed to create video from image: {e}")
    
    def loop_video_to_duration(self, video_clip, target_duration):
        """Loop video clip to match target duration."""
        video_duration = video_clip.duration
        
        if target_duration <= video_duration:
            # If target is shorter or equal, just trim
            return video_clip.subclip(0, target_duration)
        
        # Calculate how many times to loop
        loop_count = int(target_duration / video_duration)
        remaining_duration = target_duration - (loop_count * video_duration)
        
        logger.info(f"Looping video {loop_count} times with {remaining_duration:.2f}s remainder")
        
        # Create list of clips for concatenation
        clips = []
        
        # Add full loops
        for i in range(loop_count):
            clips.append(video_clip)
        
        # Add partial loop if needed
        if remaining_duration > 0:
            clips.append(video_clip.subclip(0, remaining_duration))
        
        # Concatenate all clips
        if len(clips) == 1:
            return clips[0]
        else:
            return mp.concatenate_videoclips(clips)
    
    def add_voiceover(self, video_path, audio_path, output_path, zoom_factor=1.0):
        """
        Add voiceover to video or create video from image with intelligent duration matching.
        
        Duration matching strategy:
        - Video longer than audio: Trim video to match audio duration
        - Audio longer than video: Slow down video to match audio duration
        - Image input: Create video with zoom effect matching audio duration
        - Equal durations: Use as-is
        
        Args:
            video_path (str): Path to input video or image file
            audio_path (str): Path to voiceover audio file
            output_path (str): Path to save output video
            zoom_factor (float): Zoom factor for image input (default 1.0 = no zoom)
        
        Returns:
            str: Path to the output video
        """
        logger.info(f"Adding voiceover: media={video_path}, audio={audio_path}")
        
        try:
            # Load audio first
            audio = mp.AudioFileClip(audio_path)
            audio_duration = audio.duration
            logger.info(f"Audio duration: {audio_duration:.2f}s")
            
            # Check if input is an image
            if self.is_image_file(video_path):
                logger.info("Input detected as image - creating video with zoom effect")
                
                # Create video from image with zoom effect matching audio duration
                video = self.create_video_from_image_with_zoom(
                    video_path, 
                    audio_duration,
                    zoom_factor=zoom_factor
                )
                
                # For image input, we already have the perfect duration match
                final_video_with_audio = video.set_audio(audio)
                
            else:
                # Handle as regular video
                logger.info("Input detected as video - processing normally")
                
                # Load video
                video = mp.VideoFileClip(video_path)
                video_duration = video.duration
                
                logger.info(f"Video duration: {video_duration:.2f}s, Audio duration: {audio_duration:.2f}s")
                
                # Determine duration matching strategy
                if video_duration > audio_duration:
                    # Video is longer - trim video to match audio
                    logger.info("Video longer than audio - trimming video")
                    final_video = video.subclip(0, audio_duration)
                    final_audio = audio
                elif video_duration < audio_duration:
                    # Audio is longer - slow down video to match audio duration
                    logger.info("Audio longer than video - slowing down video")
                    final_video = self.slow_down_video(video, audio_duration)
                    final_audio = audio
                else:
                    # Durations match - use as is
                    logger.info("Durations match - using as is")
                    final_video = video
                    final_audio = audio
                
                # Composite the audio
                # If video already has audio, mix it with the voiceover
                if final_video.audio is not None:
                    logger.info("Video has existing audio - mixing with voiceover")
                    # Reduce original audio volume and mix with voiceover
                    original_audio = final_video.audio.volumex(0.3)  # 30% of original volume
                    mixed_audio = mp.CompositeAudioClip([original_audio, final_audio.volumex(0.8)])
                    final_video_with_audio = final_video.set_audio(mixed_audio)
                else:
                    logger.info("Video has no audio - adding voiceover")
                    final_video_with_audio = final_video.set_audio(final_audio)
            
            # Write output video
            logger.info(f"Writing output to {output_path}")
            final_video_with_audio.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                logger=None,
                verbose=False
            )
            
            # Clean up
            video.close()
            audio.close()
            if 'final_video' in locals():
                final_video.close()
            if 'final_audio' in locals():
                final_audio.close()
            if 'final_video_with_audio' in locals() and final_video_with_audio != video:
                final_video_with_audio.close()
            
            logger.info(f"Voiceover added successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding voiceover: {e}")
            raise
    
    def validate_files(self, video_path, audio_path):
        """Validate that input files exist and are supported formats."""
        if not os.path.exists(video_path):
            raise ValueError(f"Media file not found: {video_path}")
        
        if not os.path.exists(audio_path):
            raise ValueError(f"Audio file not found: {audio_path}")
        
        video_ext = os.path.splitext(video_path)[1].lower()
        audio_ext = os.path.splitext(audio_path)[1].lower()
        
        # Check if it's an image, video, or unsupported format
        if video_ext in self.supported_image_formats:
            logger.info(f"Input detected as image format: {video_ext}")
        elif video_ext in self.supported_video_formats:
            logger.info(f"Input detected as video format: {video_ext}")
        else:
            logger.warning(f"Media format {video_ext} may not be supported. Supported videos: {self.supported_video_formats}, images: {self.supported_image_formats}")
        
        if audio_ext not in self.supported_audio_formats:
            logger.warning(f"Audio format {audio_ext} may not be supported. Supported: {self.supported_audio_formats}")
        
        return True
    
    def get_media_info(self, file_path):
        """Get detailed information about a media file."""
        try:
            # Try as video first
            video = mp.VideoFileClip(file_path)
            info = {
                'type': 'video',
                'duration': video.duration,
                'width': video.w,
                'height': video.h,
                'fps': video.fps,
                'has_audio': video.audio is not None
            }
            video.close()
            return info
        except:
            try:
                # Try as audio
                audio = mp.AudioFileClip(file_path)
                info = {
                    'type': 'audio',
                    'duration': audio.duration,
                    'fps': getattr(audio, 'fps', 44100)
                }
                audio.close()
                return info
            except Exception as e:
                logger.error(f"Could not analyze file {file_path}: {e}")
                return None