#!/usr/bin/env python3
"""
Demo script to create a sample video for testing the watermarking application
"""

import cv2
import numpy as np
import os

def create_demo_video(output_path="demo_video.mp4", duration=10, fps=30, width=640, height=480):
    """Create a colorful demo video with moving elements"""
    
    print(f"Creating demo video: {output_path}")
    print(f"Duration: {duration}s, FPS: {fps}, Resolution: {width}x{height}")
    
    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        print("Error: Could not open video writer")
        return False
    
    total_frames = duration * fps
    
    for i in range(total_frames):
        # Create frame with gradient background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Create animated gradient
        progress = i / total_frames
        
        # RGB gradient that changes over time
        for y in range(height):
            for x in range(width):
                r = int(128 + 127 * np.sin(progress * 2 * np.pi + x * 0.01))
                g = int(128 + 127 * np.cos(progress * 2 * np.pi + y * 0.01))
                b = int(128 + 127 * np.sin(progress * 2 * np.pi + (x + y) * 0.005))
                frame[y, x] = [b, g, r]  # BGR format
        
        # Add title
        cv2.putText(frame, 'Open Video Watermark Demo', (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Add frame counter
        cv2.putText(frame, f'Frame: {i+1}/{total_frames}', (50, height - 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Add progress bar
        bar_width = width - 100
        bar_height = 20
        bar_x = 50
        bar_y = height - 60
        
        # Background bar
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                     (100, 100, 100), -1)
        
        # Progress bar
        progress_width = int(bar_width * progress)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), 
                     (0, 255, 0), -1)
        
        # Add moving circle
        circle_x = int(50 + (width - 100) * progress)
        circle_y = height // 2
        cv2.circle(frame, (circle_x, circle_y), 30, (255, 255, 0), -1)
        cv2.circle(frame, (circle_x, circle_y), 30, (0, 0, 255), 3)
        
        # Add rotating rectangle
        center = (width - 100, 100)
        angle = progress * 360 * 4  # 4 full rotations
        rect_size = (60, 40)
        
        # Calculate rectangle points
        cos_a = np.cos(np.radians(angle))
        sin_a = np.sin(np.radians(angle))
        
        w, h = rect_size[0] // 2, rect_size[1] // 2
        pts = np.array([
            [-w, -h], [w, -h], [w, h], [-w, h]
        ], dtype=np.float32)
        
        # Rotate points
        rotated_pts = []
        for pt in pts:
            x = pt[0] * cos_a - pt[1] * sin_a + center[0]
            y = pt[0] * sin_a + pt[1] * cos_a + center[1]
            rotated_pts.append([int(x), int(y)])
        
        rotated_pts = np.array(rotated_pts, dtype=np.int32)
        cv2.fillPoly(frame, [rotated_pts], (255, 0, 255))
        
        # Write frame
        out.write(frame)
        
        # Show progress
        if (i + 1) % (fps // 2) == 0:  # Update every 0.5 seconds
            print(f"Progress: {i+1}/{total_frames} frames ({100*progress:.1f}%)")
    
    # Release video writer
    out.release()
    
    # Verify file was created
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"✅ Demo video created successfully!")
        print(f"📁 File: {output_path}")
        print(f"📏 Size: {file_size:.2f} MB")
        return True
    else:
        print("❌ Failed to create demo video")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create a demo video for watermarking tests')
    parser.add_argument('--output', '-o', default='demo_video.mp4', 
                       help='Output video file path (default: demo_video.mp4)')
    parser.add_argument('--duration', '-d', type=int, default=10, 
                       help='Video duration in seconds (default: 10)')
    parser.add_argument('--fps', type=int, default=30, 
                       help='Frames per second (default: 30)')
    parser.add_argument('--width', '-w', type=int, default=640, 
                       help='Video width (default: 640)')
    parser.add_argument('--height', type=int, default=480, 
                       help='Video height (default: 480)')
    
    args = parser.parse_args()
    
    print("🎬 Demo Video Creator for Open Video Watermark")
    print("=" * 50)
    
    success = create_demo_video(
        output_path=args.output,
        duration=args.duration,
        fps=args.fps,
        width=args.width,
        height=args.height
    )
    
    if success:
        print("\n🚀 You can now use this video to test the watermarking application!")
        print("   1. Start the application: python app.py")
        print("   2. Open http://localhost:5000 in your browser")
        print(f"   3. Upload {args.output} and add a watermark")
    else:
        print("\n❌ Failed to create demo video")
        exit(1)
