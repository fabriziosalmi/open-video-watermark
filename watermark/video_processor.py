import cv2
import numpy as np
import os
from typing import Callable, Optional

class VideoProcessor:
    """
    Video processing class for embedding watermarks in video files.
    Handles frame-by-frame processing with progress tracking.
    """
    
    def __init__(self):
        pass
    
    def get_video_info(self, video_path):
        """Get basic information about a video file"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        info = {
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'codec': int(cap.get(cv2.CAP_PROP_FOURCC))
        }
        
        cap.release()
        return info
    
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
                    print(f"Error processing frame {frame_count}: {e}")
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
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error processing video: {e}")
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
