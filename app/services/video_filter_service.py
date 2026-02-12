"""
Video Filter Service for Visual Effects
Provides video effects like CRT monitor filter, vintage effects, etc.
"""

import os
import tempfile
import logging
import cv2
import numpy as np
import moviepy.editor as mp
from moviepy.video.fx.resize import resize
import math

logger = logging.getLogger(__name__)

class VideoFilterService:
    """Service for video filtering and visual effects."""
    
    def __init__(self):
        self.supported_filters = {
            'crt': {
                'name': 'CRT Monitor',
                'description': 'Retro CRT monitor effect with scanlines and curvature',
                'parameters': {
                    'resolution_down_scale': 6.0,
                    'hard_scan': -8.0,
                    'hard_pix': -3.0,
                    'mask_dark': 0.5,
                    'mask_light': 1.5,
                    'scanline_intensity': 0.3,
                    'curvature': 0.02
                }
            },
            'vintage': {
                'name': 'Vintage Film',
                'description': 'Old film effect with grain and color shift',
                'parameters': {
                    'sepia_intensity': 0.7,
                    'grain_intensity': 0.15,
                    'vignette_intensity': 0.3,
                    'contrast_boost': 1.2
                }
            },
            'vhs': {
                'name': 'VHS Tape',
                'description': 'VHS tape effect with tracking lines and color bleeding',
                'parameters': {
                    'tracking_lines': 3,
                    'color_bleed': 0.4,
                    'noise_intensity': 0.1,
                    'chroma_shift': 2
                }
            },
            'fish-eye': {
                'name': 'Barrel Distortion',
                'description': 'Barrel distortion effect that maintains rectangular frame with curved content',
                'parameters': {
                    'distortion_strength': 0.2,
                    'zoom_factor': 1.0,
                    'circular_crop': False,
                    'vignette_intensity': 0.0,
                    'center_x': 0.5,
                    'center_y': 0.5
                }
            }
        }
    
    def apply_crt_filter(self, frame, params):
        """Apply CRT monitor effect to a single frame."""
        height, width = frame.shape[:2]
        
        # Resolution downscale
        down_scale = params.get('resolution_down_scale', 6.0)
        if down_scale > 1:
            small_height = int(height / down_scale)
            small_width = int(width / down_scale)
            frame = cv2.resize(frame, (small_width, small_height), interpolation=cv2.INTER_NEAREST)
            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_NEAREST)
        
        # Add scanlines
        scanline_intensity = params.get('scanline_intensity', 0.3)
        if scanline_intensity > 0:
            scanlines = np.ones_like(frame, dtype=np.float32)
            for y in range(0, height, 2):
                if y < height:
                    scanlines[y, :] *= (1.0 - scanline_intensity)
            frame = (frame.astype(np.float32) * scanlines).astype(np.uint8)
        
        # Add slight curvature effect (barrel distortion)
        curvature = params.get('curvature', 0.02)
        if curvature > 0:
            frame = self._apply_barrel_distortion(frame, curvature)
        
        # Add phosphor glow effect
        mask_dark = params.get('mask_dark', 0.5)
        mask_light = params.get('mask_light', 1.5)
        
        # Create RGB mask pattern
        mask = np.ones_like(frame, dtype=np.float32)
        for x in range(0, width, 3):
            if x < width:
                mask[:, x, 0] *= mask_light  # Red
            if x + 1 < width:
                mask[:, x + 1, 1] *= mask_light  # Green
            if x + 2 < width:
                mask[:, x + 2, 2] *= mask_light  # Blue
        
        # Apply darker mask to other pixels
        for x in range(width):
            channel = x % 3
            for c in range(3):
                if c != channel:
                    mask[:, x, c] *= mask_dark
        
        frame = np.clip(frame.astype(np.float32) * mask, 0, 255).astype(np.uint8)
        
        return frame
    
    def _apply_barrel_distortion(self, frame, strength):
        """Apply barrel distortion for CRT curvature effect."""
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2
        
        # Create coordinate arrays
        y, x = np.ogrid[:height, :width]
        x = x.astype(np.float32) - center_x
        y = y.astype(np.float32) - center_y
        
        # Normalize coordinates
        r = np.sqrt(x*x + y*y)
        max_radius = min(center_x, center_y)
        r_norm = r / max_radius
        
        # Apply barrel distortion
        r_distorted = r_norm * (1 + strength * r_norm * r_norm)
        
        # Convert back to image coordinates
        scale = np.where(r_norm > 0, r_distorted / r_norm, 1)
        x_new = (x * scale + center_x).astype(np.float32)
        y_new = (y * scale + center_y).astype(np.float32)
        
        # Remap the image
        distorted = cv2.remap(frame, x_new, y_new, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        
        return distorted
    
    def apply_vintage_filter(self, frame, params):
        """Apply vintage film effect to a single frame."""
        # Convert to float for processing
        frame_float = frame.astype(np.float32) / 255.0
        
        # Apply sepia tone
        sepia_intensity = params.get('sepia_intensity', 0.7)
        if sepia_intensity > 0:
            sepia_matrix = np.array([
                [0.393 + 0.607 * (1 - sepia_intensity), 0.769 - 0.769 * (1 - sepia_intensity), 0.189 - 0.189 * (1 - sepia_intensity)],
                [0.349 - 0.349 * (1 - sepia_intensity), 0.686 + 0.314 * (1 - sepia_intensity), 0.168 - 0.168 * (1 - sepia_intensity)],
                [0.272 - 0.272 * (1 - sepia_intensity), 0.534 - 0.534 * (1 - sepia_intensity), 0.131 + 0.869 * (1 - sepia_intensity)]
            ])
            frame_float = np.dot(frame_float, sepia_matrix.T)
        
        # Add film grain
        grain_intensity = params.get('grain_intensity', 0.15)
        if grain_intensity > 0:
            height, width = frame_float.shape[:2]
            grain = np.random.normal(0, grain_intensity, (height, width, 3))
            frame_float += grain
        
        # Add vignette effect
        vignette_intensity = params.get('vignette_intensity', 0.3)
        if vignette_intensity > 0:
            height, width = frame_float.shape[:2]
            center_x, center_y = width // 2, height // 2
            y, x = np.ogrid[:height, :width]
            
            # Calculate distance from center
            distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            max_distance = np.sqrt(center_x**2 + center_y**2)
            
            # Create vignette mask
            vignette = 1 - vignette_intensity * (distance / max_distance)**2
            vignette = np.clip(vignette, 0, 1)
            
            frame_float *= vignette[:, :, np.newaxis]
        
        # Adjust contrast
        contrast_boost = params.get('contrast_boost', 1.2)
        if contrast_boost != 1.0:
            frame_float = np.clip((frame_float - 0.5) * contrast_boost + 0.5, 0, 1)
        
        return np.clip(frame_float * 255, 0, 255).astype(np.uint8)
    
    def apply_vhs_filter(self, frame, params):
        """Apply VHS tape effect to a single frame."""
        height, width = frame.shape[:2]
        
        # Add tracking lines
        tracking_lines = params.get('tracking_lines', 3)
        if tracking_lines > 0:
            for i in range(tracking_lines):
                y_pos = int(height * (0.2 + 0.6 * i / max(1, tracking_lines - 1)))
                if 0 <= y_pos < height:
                    # Create horizontal line distortion
                    shift = int(10 * np.sin(i * 2))
                    if shift > 0:
                        frame[y_pos:min(y_pos+2, height), shift:] = frame[y_pos:min(y_pos+2, height), :-shift]
                    else:
                        frame[y_pos:min(y_pos+2, height), :shift] = frame[y_pos:min(y_pos+2, height), -shift:]
        
        # Add chroma shift (color bleeding)
        chroma_shift = int(params.get('chroma_shift', 2))
        if chroma_shift > 0:
            # Shift red channel
            frame_shifted = frame.copy()
            frame_shifted[:, chroma_shift:, 0] = frame[:, :-chroma_shift, 0]
            frame = frame_shifted
        
        # Add noise
        noise_intensity = params.get('noise_intensity', 0.1)
        if noise_intensity > 0:
            noise = np.random.normal(0, noise_intensity * 255, frame.shape)
            frame = np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        
        # Add color bleeding effect
        color_bleed = params.get('color_bleed', 0.4)
        if color_bleed > 0:
            # Blur red and blue channels slightly
            frame[:, :, 0] = cv2.GaussianBlur(frame[:, :, 0], (3, 3), color_bleed)
            frame[:, :, 2] = cv2.GaussianBlur(frame[:, :, 2], (3, 3), color_bleed)
        
        return frame
    
    def apply_fish_eye_filter(self, frame, params):
        """Apply barrel distortion effect to a single frame (maintains rectangular frame)."""
        height, width = frame.shape[:2]
        
        # Get parameters
        distortion_strength = params.get('distortion_strength', 0.8)
        zoom_factor = params.get('zoom_factor', 1.2)
        circular_crop = params.get('circular_crop', True)
        vignette_intensity = params.get('vignette_intensity', 0.3)
        center_x_ratio = params.get('center_x', 0.5)
        center_y_ratio = params.get('center_y', 0.5)
        
        # Calculate center point
        center_x = int(width * center_x_ratio)
        center_y = int(height * center_y_ratio)
        
        # Create coordinate grids
        y, x = np.ogrid[:height, :width]
        x = x.astype(np.float32) - center_x
        y = y.astype(np.float32) - center_y
        
        # Normalize coordinates to [-1, 1] range based on frame dimensions
        # This ensures distortion applies to entire rectangular frame
        x_norm = x / (width / 2.0)
        y_norm = y / (height / 2.0)
        
        # Calculate radial distance in normalized space
        r_norm = np.sqrt(x_norm*x_norm + y_norm*y_norm)
        
        # Apply barrel distortion formula
        # For barrel distortion: r_distorted = r * (1 + k * r^2)
        # For pincushion (inverse): r_distorted = r / (1 + k * r^2)
        if distortion_strength >= 0:
            # Barrel distortion (bulge outward)
            r_distorted = r_norm * (1 + distortion_strength * r_norm * r_norm)
        else:
            # Pincushion distortion (squeeze inward) 
            r_distorted = r_norm / (1 + abs(distortion_strength) * r_norm * r_norm)
        
        # Apply zoom factor
        r_distorted *= zoom_factor
        
        # Convert back to pixel coordinates
        # Avoid division by zero
        scale = np.where(r_norm > 1e-6, r_distorted / r_norm, 1)
        x_new = (x_norm * scale * (width / 2.0) + center_x).astype(np.float32)
        y_new = (y_norm * scale * (height / 2.0) + center_y).astype(np.float32)
        
        # Apply the distortion mapping with proper border handling
        # For rectangular barrel distortion, use BORDER_CONSTANT to avoid reflections
        # For circular fish-eye, BORDER_REFLECT can be used
        border_mode = cv2.BORDER_CONSTANT
        border_value = [0, 0, 0]  # Black borders
        
        fish_eye_frame = cv2.remap(frame, x_new, y_new, cv2.INTER_LINEAR, 
                                 borderMode=border_mode, borderValue=border_value)
        
        # Apply circular crop if requested (for traditional fish-eye look)
        if circular_crop:
            # Calculate radius for circular mask based on smaller dimension
            mask_radius = min(center_x, center_y, width - center_x, height - center_y)
            
            # Create circular mask
            mask = np.zeros((height, width), dtype=np.uint8)
            cv2.circle(mask, (center_x, center_y), int(mask_radius * 0.95), 255, -1)
            
            # Apply smooth edges to the mask
            mask_blur = cv2.GaussianBlur(mask, (21, 21), 0)
            mask_norm = mask_blur.astype(np.float32) / 255.0
            
            # Apply mask to each channel
            for c in range(3):
                fish_eye_frame[:, :, c] = (fish_eye_frame[:, :, c].astype(np.float32) * mask_norm).astype(np.uint8)
        
        # Add optional vignette effect
        if vignette_intensity > 0:
            # Create vignette mask
            y_v, x_v = np.ogrid[:height, :width]
            distance = np.sqrt((x_v - center_x)**2 + (y_v - center_y)**2)
            
            # Use diagonal for vignette normalization to cover full frame
            max_distance = np.sqrt((width/2)**2 + (height/2)**2)
            
            # Normalize distance and apply vignette
            distance_norm = distance / max_distance
            vignette = 1 - vignette_intensity * distance_norm**2
            vignette = np.clip(vignette, 0, 1)
            
            # Apply vignette
            fish_eye_frame = (fish_eye_frame.astype(np.float32) * vignette[:, :, np.newaxis]).astype(np.uint8)
        
        return fish_eye_frame
    
    def apply_video_filter(self, input_path, output_path, filter_type='crt', custom_params=None):
        """
        Apply video filter to a video file.
        
        Args:
            input_path (str): Path to input video file
            output_path (str): Path to save filtered output
            filter_type (str): Type of filter to apply ('crt', 'vintage', 'vhs')
            custom_params (dict): Custom parameters to override defaults
        
        Returns:
            str: Path to the filtered output file
        """
        if filter_type not in self.supported_filters:
            raise ValueError(f"Unsupported filter type: {filter_type}. Available: {list(self.supported_filters.keys())}")
        
        filter_config = self.supported_filters[filter_type]
        params = filter_config['parameters'].copy()
        
        # Override with custom parameters
        if custom_params:
            params.update(custom_params)
        
        logger.info(f"Applying {filter_config['name']} filter to {input_path}")
        
        try:
            # Load video
            video = mp.VideoFileClip(input_path)
            
            def filter_frame(get_frame, t):
                """Apply filter to each frame."""
                frame = get_frame(t)
                
                # Convert RGB to BGR for OpenCV
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Apply the appropriate filter
                if filter_type == 'crt':
                    filtered_frame = self.apply_crt_filter(frame_bgr, params)
                elif filter_type == 'vintage':
                    filtered_frame = self.apply_vintage_filter(frame_bgr, params)
                elif filter_type == 'vhs':
                    filtered_frame = self.apply_vhs_filter(frame_bgr, params)
                elif filter_type == 'fish-eye':
                    filtered_frame = self.apply_fish_eye_filter(frame_bgr, params)
                else:
                    filtered_frame = frame_bgr
                
                # Convert back to RGB for MoviePy
                return cv2.cvtColor(filtered_frame, cv2.COLOR_BGR2RGB)
            
            # Apply filter to video
            filtered_video = video.fl(filter_frame)
            
            # Write output video
            filtered_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac' if video.audio else None,
                logger=None,
                verbose=False
            )
            
            # Clean up
            video.close()
            filtered_video.close()
            
            logger.info(f"Video filter applied successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error applying video filter: {e}")
            raise
    
    def get_supported_filters(self):
        """Get list of supported video filters with their descriptions."""
        return {
            filter_type: {
                'name': config['name'],
                'description': config['description'],
                'parameters': list(config['parameters'].keys())
            }
            for filter_type, config in self.supported_filters.items()
        }
    
    def get_filter_parameters(self, filter_type):
        """Get default parameters for a specific filter."""
        if filter_type not in self.supported_filters:
            return None
        return self.supported_filters[filter_type]['parameters']