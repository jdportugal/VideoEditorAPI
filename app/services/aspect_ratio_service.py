"""
Aspect Ratio Service for Video Dimension Changes
Provides functionality to change video aspect ratios with different scaling modes.
"""

import os
import psutil
import logging
import moviepy.editor as mp
from moviepy.video.fx.resize import resize

logger = logging.getLogger(__name__)

class AspectRatioService:
    """Service for changing video aspect ratios."""
    
    def __init__(self):
        # Performance optimization settings
        self._cpu_cores = psutil.cpu_count(logical=False) or 1  # Physical cores
        self._logical_cores = psutil.cpu_count(logical=True) or 1  # Logical cores
        
        # Adaptive threading based on machine capabilities
        if self._cpu_cores >= 8:
            self._optimal_threads = min(6, self._logical_cores)  # High-end machines
        elif self._cpu_cores >= 4:
            self._optimal_threads = min(4, self._logical_cores)  # Mid-range machines
        else:
            self._optimal_threads = min(2, self._logical_cores)  # Low-end machines
        
        logger.info(f"AspectRatioService initialized: {self._cpu_cores} physical cores, {self._logical_cores} logical cores, using {self._optimal_threads} threads")
        self.common_ratios = {
            '16:9': (16, 9),    # Widescreen
            '9:16': (9, 16),    # Vertical/Portrait 
            '4:3': (4, 3),      # Traditional TV
            '3:4': (3, 4),      # Portrait traditional
            '1:1': (1, 1),      # Square
            '21:9': (21, 9),    # Ultra-wide
            '2:1': (2, 1),      # Cinema
            '16:10': (16, 10),  # Computer monitor
            '3:2': (3, 2),      # Photo standard
            '2:3': (2, 3)       # Photo portrait
        }
        
        self.scale_modes = {
            'fit': {
                'name': 'Scale to Fit',
                'description': 'Scale video to fit within new dimensions, maintaining aspect ratio (may add letterboxing)'
            },
            'fill': {
                'name': 'Scale to Fill', 
                'description': 'Scale video to fill new dimensions completely (may crop content)'
            },
            'stretch': {
                'name': 'Stretch',
                'description': 'Stretch video to exact dimensions (may distort aspect ratio)'
            },
            'square-fill': {
                'name': 'Square Center Fill (9:16 Output)',
                'description': 'Creates 9:16 portrait video with content completely filling a square region in the center (may crop to fill)'
            },
            'square': {
                'name': 'True Square (1:1)',
                'description': 'Creates a true square video output (1:1 aspect ratio) with content scaled to fit or fill'
            }
        }
    
    def _get_memory_usage(self):
        """Get current memory usage percentage."""
        return psutil.virtual_memory().percent / 100.0
    
    def _is_large_resolution_change(self, original_width, original_height, target_width, target_height):
        """Determine if this is a large resolution change requiring optimization."""
        original_pixels = original_width * original_height
        target_pixels = target_width * target_height
        
        # Consider it large if:
        # 1. Target resolution > 4MP (4,000,000 pixels)
        # 2. Pixel increase > 2x original
        # 3. Either dimension > 3000 pixels
        return (target_pixels > 4000000 or 
                target_pixels > original_pixels * 2 or
                target_width > 3000 or 
                target_height > 3000)
    
    def _get_adaptive_encoding_settings(self, is_large_resolution, duration):
        """Get encoding settings optimized for machine capabilities and content."""
        memory_usage = self._get_memory_usage()
        
        # Adaptive preset based on machine load and content
        if memory_usage > 0.8:
            preset = 'ultrafast'  # Fastest encoding when memory is tight
            threads = max(2, self._optimal_threads // 2)  # Use half threads but minimum 2
        elif is_large_resolution or duration > 300:  # Large resolution or 5+ minute video
            preset = 'faster' if self._cpu_cores >= 4 else 'ultrafast'
            threads = max(2, self._optimal_threads - 1)  # Leave one core free, minimum 2 threads
        else:
            preset = 'fast' if self._cpu_cores >= 4 else 'faster'
            threads = self._optimal_threads
        
        # Audio bitrate based on content type
        audio_bitrate = '192k' if is_large_resolution else '320k'
        
        logger.info(f"Encoding settings: preset={preset}, threads={threads}, audio_bitrate={audio_bitrate}, memory_usage={memory_usage:.1%}")
        
        return {
            'preset': preset,
            'threads': threads,
            'audio_bitrate': audio_bitrate
        }
    
    def parse_aspect_ratio(self, aspect_ratio_str):
        """Parse aspect ratio string into width:height tuple."""
        if aspect_ratio_str in self.common_ratios:
            return self.common_ratios[aspect_ratio_str]
        
        # Try to parse custom ratio like "16:9" or "1.77:1"
        if ':' in aspect_ratio_str:
            try:
                parts = aspect_ratio_str.split(':')
                if len(parts) == 2:
                    width_ratio = float(parts[0])
                    height_ratio = float(parts[1])
                    return (width_ratio, height_ratio)
            except ValueError:
                pass
        
        # Try to parse decimal ratio like "1.77" (assumes height = 1)
        try:
            ratio = float(aspect_ratio_str)
            return (ratio, 1)
        except ValueError:
            pass
        
        raise ValueError(f"Invalid aspect ratio format: {aspect_ratio_str}")
    
    def calculate_dimensions(self, original_width, original_height, target_ratio_w, target_ratio_h, target_height=None):
        """Calculate reasonable dimensions for target aspect ratio."""
        target_aspect = target_ratio_w / target_ratio_h
        
        if target_height:
            # Use specified target height
            new_height = target_height
            new_width = int(new_height * target_aspect)
        else:
            # Calculate reasonable dimensions without extreme scaling
            # Use the smaller original dimension as the base to avoid huge videos
            base_dimension = min(original_width, original_height)
            
            if target_aspect >= 1:
                # Target is landscape or square (width >= height)
                new_width = base_dimension
                new_height = int(new_width / target_aspect)
            else:
                # Target is portrait (height > width)
                new_height = base_dimension
                new_width = int(new_height * target_aspect)
            
            # Ensure we don't create dimensions smaller than 1080p
            min_dimension = 1080
            if min(new_width, new_height) < min_dimension:
                if new_width < new_height:
                    new_width = min_dimension
                    new_height = int(new_width / target_aspect)
                else:
                    new_height = min_dimension
                    new_width = int(new_height * target_aspect)
        
        # Ensure dimensions are even numbers (required for video encoding)
        new_width = new_width if new_width % 2 == 0 else new_width - 1
        new_height = new_height if new_height % 2 == 0 else new_height - 1
        
        return new_width, new_height
    
    def apply_scale_to_fit(self, video, target_width, target_height):
        """Scale video to fit within target dimensions, maintaining aspect ratio."""
        original_width, original_height = video.w, video.h
        original_aspect = original_width / original_height
        target_aspect = target_width / target_height
        
        if original_aspect > target_aspect:
            # Video is wider - fit by width
            scale_factor = target_width / original_width
            new_width = target_width
            new_height = int(original_height * scale_factor)
        else:
            # Video is taller - fit by height
            scale_factor = target_height / original_height
            new_height = target_height
            new_width = int(original_width * scale_factor)
        
        # Ensure even dimensions
        new_width = new_width if new_width % 2 == 0 else new_width - 1
        new_height = new_height if new_height % 2 == 0 else new_height - 1
        
        # Resize video
        resized_video = resize(video, (new_width, new_height))
        
        # Add letterboxing/pillarboxing if needed
        if new_width != target_width or new_height != target_height:
            # Create background
            from moviepy.video.VideoClip import ColorClip
            background = ColorClip(size=(target_width, target_height), color=(0,0,0), duration=video.duration)
            
            # Center the resized video on the background
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            
            final_video = mp.CompositeVideoClip([
                background,
                resized_video.set_position((x_offset, y_offset))
            ])
        else:
            final_video = resized_video
        
        return final_video
    
    def apply_scale_to_fill(self, video, target_width, target_height):
        """Scale video to fill target dimensions completely, cropping if necessary."""
        original_width, original_height = video.w, video.h
        original_aspect = original_width / original_height
        target_aspect = target_width / target_height
        
        if original_aspect > target_aspect:
            # Video is wider - scale by height and crop width
            scale_factor = target_height / original_height
            new_height = target_height
            new_width = int(original_width * scale_factor)
        else:
            # Video is taller - scale by width and crop height
            scale_factor = target_width / original_width
            new_width = target_width
            new_height = int(original_height * scale_factor)
        
        # Ensure even dimensions
        new_width = new_width if new_width % 2 == 0 else new_width - 1
        new_height = new_height if new_height % 2 == 0 else new_height - 1
        
        # Resize video
        resized_video = resize(video, (new_width, new_height))
        
        # Crop to target dimensions if needed
        if new_width > target_width or new_height > target_height:
            x_offset = (new_width - target_width) // 2
            y_offset = (new_height - target_height) // 2
            
            final_video = resized_video.crop(
                x1=x_offset, y1=y_offset,
                x2=x_offset + target_width, 
                y2=y_offset + target_height
            )
        else:
            final_video = resized_video
        
        return final_video
    
    def apply_stretch(self, video, target_width, target_height):
        """Stretch video to exact target dimensions."""
        return resize(video, (target_width, target_height))
    
    def apply_square_fill(self, video, target_width, target_height):
        """
        Scale video to completely fill a square region centered in a 9:16 output.
        Creates a 9:16 portrait video with the content completely filling a square area in the center.
        Video is scaled to fill the entire square (may crop to ensure full coverage).
        """
        original_width, original_height = video.w, video.h
        
        # Force output to be 9:16 aspect ratio (portrait)
        # Calculate 9:16 dimensions based on target width or default
        if target_width:
            output_width = target_width
            output_height = int(output_width * 16 / 9)
        else:
            # Default to 1080x1920 (9:16 portrait)
            output_width = 1080
            output_height = 1920
        
        # Ensure dimensions are even numbers
        output_width = output_width if output_width % 2 == 0 else output_width - 1
        output_height = output_height if output_height % 2 == 0 else output_height - 1
        
        # Calculate square region size (use width of 9:16 frame for square)
        square_size = output_width
        
        # Calculate scale factors for both width and height to fill the square completely
        width_scale = square_size / original_width
        height_scale = square_size / original_height
        
        # Use the larger scale factor to ensure the square is completely filled
        # This may result in cropping, but guarantees full coverage
        scale_factor = max(width_scale, height_scale)
        
        # Apply the scale factor to both dimensions
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Ensure even dimensions for video encoding
        new_width = new_width if new_width % 2 == 0 else new_width - 1
        new_height = new_height if new_height % 2 == 0 else new_height - 1
        
        # Resize the video proportionally
        resized_video = resize(video, (new_width, new_height))
        
        # Create a 9:16 background
        from moviepy.video.VideoClip import ColorClip
        background = ColorClip(
            size=(output_width, output_height), 
            color=(0, 0, 0),  # Black background
            duration=video.duration
        )
        
        # Calculate positioning for the square region in the 9:16 frame
        # Center the square region vertically in the 9:16 frame
        square_y_offset = (output_height - square_size) // 2  # Center square vertically
        
        # If video is larger than square, crop it by centering within the square
        if new_width > square_size or new_height > square_size:
            # Calculate crop offsets to center the video within the square
            crop_x = max(0, (new_width - square_size) // 2)
            crop_y = max(0, (new_height - square_size) // 2)
            
            # Crop the resized video to fit exactly in the square
            resized_video = resized_video.crop(
                x1=crop_x, 
                y1=crop_y,
                x2=crop_x + square_size,
                y2=crop_y + square_size
            )
            
            final_x_offset = 0  # Square starts at left edge of output
            final_y_offset = square_y_offset
        else:
            # Center the video within the square region
            video_x_offset = (square_size - new_width) // 2
            video_y_offset = (square_size - new_height) // 2
            
            final_x_offset = video_x_offset
            final_y_offset = square_y_offset + video_y_offset
        
        # Composite the resized video onto the 9:16 background
        final_video = mp.CompositeVideoClip([
            background,
            resized_video.set_position((final_x_offset, final_y_offset))
        ])
        
        return final_video
    
    def apply_square(self, video, target_width, target_height):
        """
        Create a true square (1:1) video output.
        Scales content to completely fill the square dimensions.
        
        Args:
            video: MoviePy VideoFileClip
            target_width (int): Target width (will be used for both width and height to create square)
            target_height (int): Target height (ignored, square uses target_width for both dimensions)
        
        Returns:
            VideoFileClip: Square video with 1:1 aspect ratio
        """
        # Get original dimensions
        original_width = video.w
        original_height = video.h
        
        # For square output, use the target_width as both width and height
        square_size = target_width
        
        logger.info(f"🟫 Creating square video: {original_width}x{original_height} → {square_size}x{square_size}")
        
        # Calculate scale factors for both dimensions
        width_scale = square_size / original_width
        height_scale = square_size / original_height
        
        # Use the larger scale factor to ensure the square is completely filled (may crop)
        scale_factor = max(width_scale, height_scale)
        
        # Calculate new dimensions after scaling
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        logger.info(f"🔍 Scale factor: {scale_factor:.3f}, intermediate size: {new_width}x{new_height}")
        
        # Apply scaling
        resized_video = video.resize((new_width, new_height))
        
        # If the scaled video is larger than the square, crop it to fit exactly
        if new_width > square_size or new_height > square_size:
            # Calculate crop offsets to center the video within the square
            crop_x = max(0, (new_width - square_size) // 2)
            crop_y = max(0, (new_height - square_size) // 2)
            
            logger.info(f"✂️ Cropping to center: offset ({crop_x}, {crop_y})")
            
            # Crop the resized video to fit exactly in the square
            final_video = resized_video.crop(
                x1=crop_x, y1=crop_y,
                x2=crop_x + square_size,
                y2=crop_y + square_size
            )
        else:
            # Video fits within square, center it with black background
            logger.info(f"🎯 Centering video in square background")
            
            # Create black square background
            background = mp.ColorClip(
                size=(square_size, square_size),
                color=(0, 0, 0),
                duration=video.duration
            )
            
            # Center the scaled video within the square
            x_offset = (square_size - new_width) // 2
            y_offset = (square_size - new_height) // 2
            
            logger.info(f"📍 Positioning video at offset ({x_offset}, {y_offset})")
            
            # Composite the video onto the square background
            final_video = mp.CompositeVideoClip([
                background,
                resized_video.set_position((x_offset, y_offset))
            ])
        
        logger.info(f"✅ Square video created: {final_video.w}x{final_video.h}")
        return final_video
    
    def change_aspect_ratio(self, input_path, output_path, aspect_ratio, scale_mode='fit', target_height=None, job_manager=None, job_id=None):
        """
        Change video aspect ratio with detailed progress logging.
        
        Args:
            input_path (str): Path to input video
            output_path (str): Path to save output video
            aspect_ratio (str): Target aspect ratio (e.g., '16:9', '9:16', '1:1')
            scale_mode (str): How to scale ('fit', 'fill', 'stretch')
            target_height (int, optional): Specific target height in pixels
            job_manager: Job manager instance for progress updates
            job_id (str): Job ID for progress tracking
        
        Returns:
            str: Path to the output video
        """
        if scale_mode not in self.scale_modes:
            raise ValueError(f"Invalid scale mode: {scale_mode}. Available: {list(self.scale_modes.keys())}")
        
        logger.info(f"🎬 ASPECT RATIO JOB STARTED - Job ID: {job_id}")
        logger.info(f"📐 Target: {aspect_ratio} | Mode: {scale_mode} | Input: {input_path}")
        
        if job_manager and job_id:
            job_manager.update_job_status(job_id, "processing", 10, "🎬 Starting aspect ratio processing...")
        
        try:
            # Parse aspect ratio
            logger.info(f"🔍 Parsing aspect ratio: {aspect_ratio}")
            ratio_w, ratio_h = self.parse_aspect_ratio(aspect_ratio)
            logger.info(f"✅ Aspect ratio parsed: {ratio_w}:{ratio_h}")
            
            if job_manager and job_id:
                job_manager.update_job_status(job_id, "processing", 20, "🎥 Loading video file...")
            
            # Load video
            logger.info(f"📼 Loading video file: {input_path}")
            video = mp.VideoFileClip(input_path)
            original_width, original_height = video.w, video.h
            duration = video.duration
            
            logger.info(f"📏 Original dimensions: {original_width}x{original_height}")
            logger.info(f"⏱️ Duration: {duration:.2f} seconds")
            
            if job_manager and job_id:
                job_manager.update_job_status(job_id, "processing", 30, f"📏 Video loaded: {original_width}x{original_height}")
            
            # Calculate target dimensions
            logger.info(f"🧮 Calculating target dimensions...")
            target_width, target_height = self.calculate_dimensions(
                original_width, original_height, ratio_w, ratio_h, target_height
            )
            
            # Analyze processing requirements
            is_large_resolution = self._is_large_resolution_change(
                original_width, original_height, target_width, target_height
            )
            
            logger.info(f"🎯 Target dimensions: {target_width}x{target_height}")
            logger.info(f"📊 Scale mode: {self.scale_modes[scale_mode]['name']}")
            logger.info(f"🔍 Large resolution change: {is_large_resolution}")
            logger.info(f"📐 Original dimensions: {video.w}x{video.h}")
            logger.info(f"📏 Resolution scale factor: {(target_width * target_height) / (video.w * video.h):.2f}x")
            
            if job_manager and job_id:
                status_msg = f"🎯 Processing {scale_mode} scaling ({target_width}x{target_height})"
                if is_large_resolution:
                    status_msg += " - Large resolution detected"
                job_manager.update_job_status(job_id, "processing", 40, status_msg)
            
            # Apply scaling mode
            logger.info(f"⚙️ Applying {scale_mode} scaling...")
            if scale_mode == 'fit':
                logger.info(f"📦 Applying scale-to-fit (letterboxing/pillarboxing)")
                processed_video = self.apply_scale_to_fit(video, target_width, target_height)
            elif scale_mode == 'fill':
                logger.info(f"🔍 Applying scale-to-fill (cropping)")
                processed_video = self.apply_scale_to_fill(video, target_width, target_height)
            elif scale_mode == 'stretch':
                logger.info(f"📏 Applying stretch scaling (may distort)")
                processed_video = self.apply_stretch(video, target_width, target_height)
            elif scale_mode == 'square-fill':
                logger.info(f"⬜ Applying square center fill (9:16 portrait output, fully filled square in center)")
                processed_video = self.apply_square_fill(video, target_width, target_height)
            elif scale_mode == 'square':
                logger.info(f"🟫 Applying true square (1:1) output")
                processed_video = self.apply_square(video, target_width, target_height)
            
            logger.info(f"✅ Scaling complete, final dimensions: {processed_video.w}x{processed_video.h}")
            
            # Get optimized encoding settings
            encoding_settings = self._get_adaptive_encoding_settings(is_large_resolution, duration)
            
            if job_manager and job_id:
                job_manager.update_job_status(job_id, "processing", 60, f"💾 Encoding video to {output_path}...")
            
            # Write output video with optimized settings
            logger.info(f"💾 Starting optimized video encoding...")
            logger.info(f"📝 Output path: {output_path}")
            logger.info(f"🎞️ Codec: libx264 | Audio: {'aac' if video.audio else 'none'}")
            logger.info(f"⚙️ Settings: {encoding_settings['preset']} preset, {encoding_settings['threads']} threads")
            
            # Use simple, reliable encoding settings to avoid hangs
            logger.info(f"💾 Starting simplified video encoding...")
            
            processed_video.write_videofile(
                output_path,
                codec='libx264',
                preset='medium',  # Reliable preset
                logger=None,
                verbose=False
            )
            
            # Update progress after encoding completes
            if job_manager and job_id:
                job_manager.update_job_status(job_id, "processing", 95, "✅ Encoding completed")
            
            logger.info(f"✅ Video encoding completed successfully")
            
            if job_manager and job_id:
                job_manager.update_job_status(job_id, "processing", 95, "🧹 Cleaning up resources...")
            
            # Clean up
            logger.info(f"🧹 Cleaning up video resources...")
            video.close()
            processed_video.close()
            
            # Verify output file
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"✅ Output file verified: {output_path} ({file_size:,} bytes)")
            else:
                raise Exception(f"Output file not created: {output_path}")
            
            if job_manager and job_id:
                job_manager.update_job_status(job_id, "completed", 100, "✅ Aspect ratio change completed!")
            
            logger.info(f"🎉 ASPECT RATIO JOB COMPLETED - Job ID: {job_id}")
            logger.info(f"📐 Successfully changed aspect ratio: {aspect_ratio} ({scale_mode} mode)")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ ASPECT RATIO JOB FAILED - Job ID: {job_id}")
            logger.error(f"💥 Error details: {str(e)}")
            if job_manager and job_id:
                job_manager.update_job_status(job_id, "failed", 0, f"❌ Failed: {str(e)}")
            raise
    
    def get_common_ratios(self):
        """Get list of common aspect ratios."""
        return {
            ratio: {
                'width': w,
                'height': h,
                'decimal': round(w/h, 2),
                'name': self._get_ratio_name(ratio)
            }
            for ratio, (w, h) in self.common_ratios.items()
        }
    
    def get_scale_modes(self):
        """Get list of available scale modes."""
        return self.scale_modes
    
    def _get_ratio_name(self, ratio):
        """Get friendly name for aspect ratio."""
        names = {
            '16:9': 'Widescreen (YouTube, TV)',
            '9:16': 'Vertical (TikTok, Instagram Stories)',
            '4:3': 'Traditional TV',
            '3:4': 'Portrait Traditional',
            '1:1': 'Square (Instagram Post)',
            '21:9': 'Ultra-wide Cinema',
            '2:1': 'Cinema',
            '16:10': 'Computer Monitor',
            '3:2': 'Photography Standard',
            '2:3': 'Photography Portrait'
        }
        return names.get(ratio, 'Custom')
    
    def get_video_info(self, file_path):
        """Get video dimensions and aspect ratio info."""
        try:
            video = mp.VideoFileClip(file_path)
            width, height = video.w, video.h
            aspect_ratio = round(width / height, 2)
            
            # Find closest common ratio
            closest_ratio = None
            closest_diff = float('inf')
            for ratio_str, (w, h) in self.common_ratios.items():
                ratio_val = w / h
                diff = abs(aspect_ratio - ratio_val)
                if diff < closest_diff:
                    closest_diff = diff
                    closest_ratio = ratio_str
            
            video.close()
            
            return {
                'width': width,
                'height': height,
                'aspect_ratio': aspect_ratio,
                'closest_common_ratio': closest_ratio,
                'duration': video.duration
            }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None