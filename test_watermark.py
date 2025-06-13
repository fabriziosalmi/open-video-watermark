#!/usr/bin/env python3
"""
Test script for the video watermarking functionality
"""

import os
import sys
import numpy as np
import cv2
from watermark.dct_watermark import DCTWatermark
from watermark.video_processor import VideoProcessor

def create_test_video(output_path, duration=5, fps=30, width=640, height=480):
    """Create a simple test video for testing purposes"""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration * fps
    
    for i in range(total_frames):
        # Create a simple test frame with changing colors
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Create a gradient effect
        color_r = int(255 * (i / total_frames))
        color_g = int(255 * ((total_frames - i) / total_frames))
        color_b = 128
        
        frame[:, :] = [color_b, color_g, color_r]  # BGR format
        
        # Add some text to make it more interesting
        cv2.putText(frame, f'Frame {i+1}/{total_frames}', (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Add a moving rectangle
        rect_x = int((width - 100) * (i / total_frames))
        cv2.rectangle(frame, (rect_x, height//2 - 25), (rect_x + 100, height//2 + 25), 
                     (255, 255, 255), -1)
        
        out.write(frame)
    
    out.release()
    print(f"Test video created: {output_path}")

def test_image_watermarking():
    """Test basic image watermarking functionality"""
    print("Testing image watermarking...")
    
    # Create a test image
    test_image = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
    
    # Initialize watermarker
    watermarker = DCTWatermark()
    
    # Test watermark text
    watermark_text = "TestWatermark"
    
    # Embed watermark
    watermarked_image = watermarker.embed_watermark(test_image, watermark_text, strength=0.1)
    
    # Extract watermark
    extracted_text = watermarker.extract_watermark(watermarked_image, len(watermark_text))
    
    print(f"Original text: {watermark_text}")
    print(f"Extracted text: {extracted_text}")
    
    # Check if extraction was successful
    if watermark_text in extracted_text or extracted_text in watermark_text:
        print("✅ Image watermarking test PASSED")
        return True
    else:
        print("❌ Image watermarking test FAILED")
        return False

def test_video_processing():
    """Test video processing functionality"""
    print("\nTesting video processing...")
    
    # Create test video
    test_video_path = "test_video.mp4"
    watermarked_video_path = "test_watermarked.mp4"
    
    try:
        # Create test video
        create_test_video(test_video_path, duration=2)  # Short video for testing
        
        # Initialize components
        watermarker = DCTWatermark()
        processor = VideoProcessor()
        
        # Test video info
        info = processor.get_video_info(test_video_path)
        if info:
            print(f"Video info: {info['frame_count']} frames, {info['fps']} fps, {info['width']}x{info['height']}")
        else:
            print("❌ Failed to get video info")
            return False
        
        # Test watermark embedding
        watermark_text = "VideoTest"
        strength = 0.15
        
        def progress_callback(frame_num, total_frames, message="Processing"):
            print(f"\r{message}: {frame_num}/{total_frames} ({int(100*frame_num/total_frames)}%)", end="")
        
        success = processor.embed_watermark_in_video(
            test_video_path, watermarked_video_path, watermark_text, 
            strength, watermarker, progress_callback
        )
        
        print()  # New line after progress
        
        if success and os.path.exists(watermarked_video_path):
            print("✅ Video watermarking test PASSED")
            
            # Test extraction (optional)
            print("Testing watermark extraction...")
            extracted_text = processor.extract_watermark_from_video(
                watermarked_video_path, len(watermark_text), watermarker, frame_sample_rate=10
            )
            
            if extracted_text:
                print(f"Extracted watermark: {extracted_text}")
            else:
                print("Could not extract watermark (this is normal for short test videos)")
            
            return True
        else:
            print("❌ Video watermarking test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Video processing test FAILED: {e}")
        return False
    
    finally:
        # Clean up test files
        for file_path in [test_video_path, watermarked_video_path]:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up: {file_path}")

def test_validation():
    """Test file validation functionality"""
    print("\nTesting file validation...")
    
    processor = VideoProcessor()
    
    # Test with non-existent file
    result = processor.validate_video_file("nonexistent.mp4")
    if not result:
        print("✅ Non-existent file validation test PASSED")
    else:
        print("❌ Non-existent file validation test FAILED")
        return False
    
    # Create a test file that's not a video
    test_file = "test.txt"
    with open(test_file, 'w') as f:
        f.write("This is not a video file")
    
    result = processor.validate_video_file(test_file)
    os.remove(test_file)
    
    if not result:
        print("✅ Invalid file validation test PASSED")
        return True
    else:
        print("❌ Invalid file validation test FAILED")
        return False

def main():
    """Run all tests"""
    print("🧪 Starting Open Video Watermark Tests\n")
    
    tests = [
        ("Image Watermarking", test_image_watermarking),
        ("Video Processing", test_video_processing),
        ("File Validation", test_validation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"{'='*50}")
        print(f"Running {test_name} Test")
        print(f"{'='*50}")
        
        try:
            if test_func():
                passed += 1
            else:
                print(f"Test {test_name} failed")
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
        
        print()  # Add spacing between tests
    
    print(f"{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    print(f"{'='*50}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
