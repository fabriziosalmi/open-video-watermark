import cv2
import numpy as np
import os
import logging
import time
from typing import Callable, Optional, Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    Video processing class for embedding watermarks in video files.
    Handles frame-by-frame processing with progress tracking.
    """
    
    def __init__(self):
        self.supported_codecs = ['mp4v', 'XVID', 'MJPG', 'X264']
        self.max_resolution = (3840, 2160)  # 4K max
        self.min_resolution = (320, 240)    # Minimum viable resolution
    
    def get_video_info(self, video_path):
        """Get basic information about a video file"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Could not open video file: {video_path}")
                return None
            
            info = {
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'codec': int(cap.get(cv2.CAP_PROP_FOURCC))
            }
            
            cap.release()
            logger.debug(f"Video info for {video_path}: {info}")
            return info
        except Exception as e:
            logger.error(f"Error getting video info for {video_path}: {e}")
            return None
    
    def embed_watermark_in_video(self, input_path, output_path, watermark_text, 
                                strength, watermarker, progress_callback: Optional[Callable] = None):
        """
        Embed watermark in a video file
        
        Args:
            input_path: Path to input video
            output_path: Path to output video
            watermark_text: Text to embed as watermark
            strength: Watermark embedding strength
            watermarker: DCTWatermark instance
            progress_callback: Function to call with progress updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Open input video
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return False
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames == 0:
                cap.release()
                return False
            
            # Define codec and create VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            if not out.isOpened():
                cap.release()
                return False
            
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Embed watermark in frame
                try:
                    watermarked_frame = watermarker.embed_watermark(frame, watermark_text, strength)
                    out.write(watermarked_frame)
                except Exception as e:
                    logger.warning(f"Error processing frame {frame_count}: {e}")
                    # Write original frame if watermarking fails
                    out.write(frame)
                
                # Update progress
                if progress_callback:
                    progress_callback(frame_count, total_frames, "Processing")
            
            # Release resources
            cap.release()
            out.release()
            
            # Verify output file was created and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Video processing completed successfully: {output_path}")
                return True
            else:
                logger.error(f"Output video file is empty or missing: {output_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing video {input_path}: {e}", exc_info=True)
            return False
    
    def extract_watermark_from_video(self, video_path, watermark_length, watermarker, 
                                   frame_sample_rate=30):
        """
        Extract watermark from a video file by sampling frames
        
        Args:
            video_path: Path to watermarked video
            watermark_length: Expected length of watermark text
            watermarker: DCTWatermark instance
            frame_sample_rate: Sample every Nth frame
            
        Returns:
            Most likely watermark text based on frame sampling
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_count = 0
            extracted_texts = []
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Sample frames at specified rate
                if frame_count % frame_sample_rate == 0:
                    try:
                        extracted_text = watermarker.extract_watermark(frame, watermark_length)
                        if extracted_text and "Error" not in extracted_text:
                            extracted_texts.append(extracted_text)
                    except Exception as e:
                        print(f"Error extracting from frame {frame_count}: {e}")
                
                frame_count += 1
                
                # Don't need to process all frames for extraction
                if len(extracted_texts) >= 10:
                    break
            
            cap.release()
            
            if extracted_texts:
                # Return the most common extracted text
                from collections import Counter
                counter = Counter(extracted_texts)
                return counter.most_common(1)[0][0]
            else:
                return None
                
        except Exception as e:
            print(f"Error extracting watermark from video: {e}")
            return None
    
    def validate_video_file(self, file_path):
        """
        Validate that a file is a readable video
        
        Args:
            file_path: Path to video file
            
        Returns:
            True if valid video, False otherwise
        """
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return False
            
            # Try to read the first frame
            ret, frame = cap.read()
            cap.release()
            
            return ret and frame is not None
            
        except Exception:
            return False
    
    def get_video_duration(self, video_path):
        """Get video duration in seconds"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return 0
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()
            
            return frame_count / fps if fps > 0 else 0
            
        except Exception:
            return 0
    
    def validate_video_comprehensive(self, file_path: str) -> Dict[str, Any]:
        """
        Comprehensive video validation with detailed report
        
        Args:
            file_path: Path to video file
            
        Returns:
            Dict with validation results and details
        """
        validation_result = {
            'valid': False,
            'file_exists': False,
            'file_size': 0,
            'readable': False,
            'has_video_stream': False,
            'has_audio_stream': False,
            'duration': 0,
            'frame_count': 0,
            'fps': 0,
            'resolution': (0, 0),
            'codec': None,
            'format': None,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check file existence and size
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                validation_result['errors'].append('File does not exist')
                return validation_result
            
            validation_result['file_exists'] = True
            validation_result['file_size'] = file_path_obj.stat().st_size
            
            if validation_result['file_size'] == 0:
                validation_result['errors'].append('File is empty')
                return validation_result
            
            # Try to open with OpenCV
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                validation_result['errors'].append('Cannot open video with OpenCV')
                cap.release()
                return validation_result
            
            validation_result['readable'] = True
            
            # Get video properties
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            
            validation_result['frame_count'] = frame_count
            validation_result['fps'] = fps
            validation_result['resolution'] = (width, height)
            validation_result['codec'] = fourcc
            
            # Calculate duration
            if fps > 0:
                validation_result['duration'] = frame_count / fps
            
            # Check if we can read frames
            ret, frame = cap.read()
            if ret and frame is not None:
                validation_result['has_video_stream'] = True
            else:
                validation_result['errors'].append('Cannot read video frames')
            
            # Validate resolution
            if width < self.min_resolution[0] or height < self.min_resolution[1]:
                validation_result['warnings'].append(f'Resolution {width}x{height} is below minimum {self.min_resolution}')
            
            if width > self.max_resolution[0] or height > self.max_resolution[1]:
                validation_result['warnings'].append(f'Resolution {width}x{height} exceeds maximum {self.max_resolution}')
            
            # Validate frame rate
            if fps < 1 or fps > 120:
                validation_result['warnings'].append(f'Unusual frame rate: {fps} FPS')
            
            # Validate duration
            if validation_result['duration'] < 0.1:
                validation_result['warnings'].append('Video duration is very short')
            elif validation_result['duration'] > 7200:  # 2 hours
                validation_result['warnings'].append('Video duration is very long')
            
            cap.release()
            
            # Overall validation status
            validation_result['valid'] = (
                validation_result['readable'] and 
                validation_result['has_video_stream'] and 
                len(validation_result['errors']) == 0
            )
            
        except Exception as e:
            validation_result['errors'].append(f'Validation error: {str(e)}')
            logger.error(f"Comprehensive validation failed for {file_path}: {e}")
        
        return validation_result
    
    def estimate_processing_time(self, video_path: str, watermark_text: str) -> Dict[str, float]:
        """
        Estimate processing time for watermarking a video
        
        Args:
            video_path: Path to video file
            watermark_text: Watermark text to embed
            
        Returns:
            Dict with time estimates
        """
        try:
            info = self.get_video_info(video_path)
            if not info:
                return {'estimated_seconds': 0, 'confidence': 0}
            
            # Base processing rate (frames per second on average hardware)
            base_fps_rate = 30
            
            # Factors that affect processing speed
            resolution_factor = (info['width'] * info['height']) / (1920 * 1080)  # 1080p baseline
            watermark_factor = len(watermark_text) / 20  # 20 char baseline
            
            # Adjusted processing rate
            adjusted_rate = base_fps_rate / (resolution_factor * watermark_factor)
            
            # Estimated time
            estimated_seconds = info['frame_count'] / max(adjusted_rate, 1)
            
            return {
                'estimated_seconds': round(estimated_seconds, 1),
                'estimated_minutes': round(estimated_seconds / 60, 1),
                'confidence': 0.7,  # Moderate confidence in estimates
                'factors': {
                    'resolution_factor': round(resolution_factor, 2),
                    'watermark_factor': round(watermark_factor, 2),
                    'adjusted_rate': round(adjusted_rate, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Error estimating processing time: {e}")
            return {'estimated_seconds': 0, 'confidence': 0}
    
    def get_optimal_codec(self, input_path: str) -> str:
        """
        Determine optimal codec for output video based on input
        
        Args:
            input_path: Path to input video
            
        Returns:
            Optimal codec identifier
        """
        try:
            info = self.get_video_info(input_path)
            if not info:
                return 'mp4v'  # Default fallback
            
            width, height = info['width'], info['height']
            
            # Choose codec based on resolution and quality needs
            if width >= 1920 and height >= 1080:  # HD+
                return 'X264'  # Better quality for high resolution
            elif width >= 1280 and height >= 720:  # HD
                return 'mp4v'  # Good balance
            else:  # SD
                return 'XVID'  # Efficient for lower resolutions
                
        except Exception:
            return 'mp4v'  # Safe default
    
    def create_processing_stats(self) -> Dict[str, Any]:
        """
        Create processing statistics for monitoring
        
        Returns:
            Dict with current processing statistics
        """
        return {
            'timestamp': time.time(),
            'opencv_version': cv2.__version__,
            'available_codecs': self.supported_codecs,
            'max_resolution': self.max_resolution,
            'min_resolution': self.min_resolution
        }
