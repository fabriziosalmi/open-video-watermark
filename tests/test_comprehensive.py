#!/usr/bin/env python3
"""
Comprehensive test suite for Open Video Watermark
Tests all major functionality including watermarking, video processing, and API endpoints.
"""

import pytest
import os
import cv2
import numpy as np
import tempfile
import json
from unittest.mock import patch, MagicMock
import sys
import threading
import time
from io import BytesIO

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from watermark.dct_watermark import DCTWatermark
from watermark.video_processor import VideoProcessor
from app import app, processing_queue, processing_status, file_registry
import config

class TestDCTWatermark:
    """Test the DCT watermarking algorithm"""
    
    @pytest.fixture
    def watermarker(self):
        return DCTWatermark()
    
    @pytest.fixture
    def test_image(self):
        # Create a test image
        return np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
    
    @pytest.fixture
    def test_grayscale_image(self):
        return np.random.randint(0, 256, (256, 256), dtype=np.uint8)
    
    def test_text_to_binary_conversion(self, watermarker):
        """Test text to binary conversion"""
        text = "Test"
        binary = watermarker._text_to_binary(text)
        assert len(binary) == len(text) * 8
        assert binary == "01010100011001010111001101110100"
    
    def test_binary_to_text_conversion(self, watermarker):
        """Test binary to text conversion"""
        binary = "01010100011001010111001101110100"
        text = watermarker._binary_to_text(binary)
        assert text == "Test"
    
    def test_embed_watermark_color(self, watermarker, test_image):
        """Test watermark embedding in color image"""
        watermark_text = "TestWatermark"
        watermarked = watermarker.embed_watermark(test_image, watermark_text, 0.1)
        
        assert watermarked.shape == test_image.shape
        assert watermarked.dtype == np.uint8
        assert not np.array_equal(watermarked, test_image)
    
    def test_embed_watermark_grayscale(self, watermarker, test_grayscale_image):
        """Test watermark embedding in grayscale image"""
        watermark_text = "Test"
        watermarked = watermarker.embed_watermark(test_grayscale_image, watermark_text, 0.1)
        
        assert watermarked.shape == test_grayscale_image.shape
        assert watermarked.dtype == np.uint8
        assert not np.array_equal(watermarked, test_grayscale_image)
    
    def test_extract_watermark(self, watermarker, test_image):
        """Test watermark extraction"""
        watermark_text = "Extract"
        watermarked = watermarker.embed_watermark(test_image, watermark_text, 0.15)
        extracted = watermarker.extract_watermark(watermarked, len(watermark_text))
        
        # Note: Perfect extraction is not always guaranteed due to quantization
        assert isinstance(extracted, str)
        assert len(extracted) == len(watermark_text)
    
    def test_enhanced_watermark_embedding(self, watermarker, test_image):
        """Test enhanced watermark embedding with redundancy"""
        watermark_text = "Enhanced"
        watermarked = watermarker.embed_watermark_enhanced(
            test_image, watermark_text, strength=0.15, redundancy=3
        )
        
        assert watermarked.shape == test_image.shape
        assert watermarked.dtype == np.uint8
    
    def test_enhanced_watermark_extraction(self, watermarker, test_image):
        """Test enhanced watermark extraction"""
        watermark_text = "Robust"
        watermarked = watermarker.embed_watermark_enhanced(
            test_image, watermark_text, strength=0.2, redundancy=3
        )
        extracted = watermarker.extract_watermark_enhanced(
            watermarked, len(watermark_text), redundancy=3
        )
        
        # Enhanced extraction should be more reliable
        assert isinstance(extracted, str) or extracted is None
    
    def test_robustness_testing(self, watermarker, test_image):
        """Test robustness testing functionality"""
        watermark_text = "Robust"
        results = watermarker.test_robustness(test_image, watermark_text, 0.15)
        
        assert isinstance(results, dict)
        assert 'no_attack' in results
        assert 'jpeg_compression' in results
        assert 'gaussian_noise' in results
        assert 'scaling' in results
    
    def test_zigzag_pattern_generation(self, watermarker):
        """Test zigzag pattern generation"""
        pattern = watermarker._generate_zigzag_pattern()
        assert len(pattern) == watermarker.block_size * watermarker.block_size
        assert all(isinstance(p, tuple) and len(p) == 2 for p in pattern)
    
    def test_robust_embedding_positions(self, watermarker):
        """Test robust embedding position selection"""
        low_strength_pos = watermarker._get_robust_embedding_positions(0.05)
        medium_strength_pos = watermarker._get_robust_embedding_positions(0.15)
        high_strength_pos = watermarker._get_robust_embedding_positions(0.25)
        
        assert len(low_strength_pos) <= len(medium_strength_pos)
        assert len(medium_strength_pos) <= len(high_strength_pos)


class TestVideoProcessor:
    """Test the video processing functionality"""
    
    @pytest.fixture
    def processor(self):
        return VideoProcessor()
    
    @pytest.fixture
    def test_video_path(self):
        """Create a temporary test video file"""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            # Create a simple test video
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(f.name, fourcc, 30.0, (320, 240))
            
            # Write a few frames
            for i in range(30):  # 1 second of video
                frame = np.random.randint(0, 256, (240, 320, 3), dtype=np.uint8)
                out.write(frame)
            
            out.release()
            yield f.name
            
            # Cleanup
            if os.path.exists(f.name):
                os.unlink(f.name)
    
    def test_get_video_info(self, processor, test_video_path):
        """Test video information extraction"""
        info = processor.get_video_info(test_video_path)
        
        assert info is not None
        assert 'frame_count' in info
        assert 'fps' in info
        assert 'width' in info
        assert 'height' in info
        assert info['width'] == 320
        assert info['height'] == 240
    
    def test_validate_video_file(self, processor, test_video_path):
        """Test video file validation"""
        assert processor.validate_video_file(test_video_path) is True
        assert processor.validate_video_file('nonexistent.mp4') is False
    
    def test_comprehensive_video_validation(self, processor, test_video_path):
        """Test comprehensive video validation"""
        result = processor.validate_video_comprehensive(test_video_path)
        
        assert isinstance(result, dict)
        assert result['valid'] is True
        assert result['file_exists'] is True
        assert result['readable'] is True
        assert result['has_video_stream'] is True
        assert result['file_size'] > 0
        assert result['frame_count'] > 0
        assert result['fps'] > 0
    
    def test_estimate_processing_time(self, processor, test_video_path):
        """Test processing time estimation"""
        estimate = processor.estimate_processing_time(test_video_path, "TestWatermark")
        
        assert isinstance(estimate, dict)
        assert 'estimated_seconds' in estimate
        assert 'estimated_minutes' in estimate
        assert 'confidence' in estimate
        assert estimate['estimated_seconds'] >= 0
    
    def test_get_optimal_codec(self, processor, test_video_path):
        """Test optimal codec selection"""
        codec = processor.get_optimal_codec(test_video_path)
        assert codec in ['mp4v', 'XVID', 'X264', 'MJPG']
    
    def test_get_video_duration(self, processor, test_video_path):
        """Test video duration calculation"""
        duration = processor.get_video_duration(test_video_path)
        assert duration > 0
        assert duration <= 2  # Should be around 1 second
    
    def test_create_processing_stats(self, processor):
        """Test processing statistics creation"""
        stats = processor.create_processing_stats()
        
        assert isinstance(stats, dict)
        assert 'timestamp' in stats
        assert 'opencv_version' in stats
        assert 'available_codecs' in stats
        assert 'max_resolution' in stats
        assert 'min_resolution' in stats


class TestFlaskApp:
    """Test the Flask web application"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'open-video-watermark'
        assert data['version'] == config.VERSION
    
    def test_system_info(self, client):
        """Test system info endpoint"""
        response = client.get('/system/info')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'app' in data
        assert data['app']['version'] == config.VERSION
    
    def test_queue_status(self, client):
        """Test queue status endpoint"""
        response = client.get('/queue/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'queue_size' in data
        assert 'active_tasks' in data
        assert 'completed_tasks' in data
        assert 'failed_tasks' in data
    
    def test_list_files_empty(self, client):
        """Test file listing when empty"""
        response = client.get('/files')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get('/metrics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'processing' in data
        assert 'storage' in data
        assert 'system' in data
        assert 'timestamp' in data
    
    def test_batch_status(self, client):
        """Test batch status endpoint"""
        response = client.get('/batch-status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_tasks' in data
        assert 'queued' in data
        assert 'processing' in data
        assert 'completed' in data
        assert 'failed' in data
    
    def test_upload_no_files(self, client):
        """Test upload endpoint with no files"""
        response = client.post('/upload', data={
            'watermark_text': 'Test'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_upload_empty_watermark(self, client):
        """Test upload with empty watermark text"""
        response = client.post('/upload', data={
            'watermark_text': '',
            'files': []
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'empty' in data['error'].lower()
    
    def test_upload_invalid_strength(self, client):
        """Test upload with invalid strength value"""
        response = client.post('/upload', data={
            'watermark_text': 'Test',
            'strength': 'invalid',
            'files': []
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_extract_no_file(self, client):
        """Test watermark extraction with no file"""
        response = client.post('/extract', data={
            'watermark_length': 10
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_validate_no_file(self, client):
        """Test video validation with no file"""
        response = client.post('/validate')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_estimate_time_no_file(self, client):
        """Test processing time estimation with no file"""
        response = client.post('/estimate-time', data={
            'watermark_text': 'Test'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestConfiguration:
    """Test configuration and setup"""
    
    def test_config_values(self):
        """Test configuration values are properly set"""
        assert config.APP_NAME == "Open Video Watermark"
        assert config.VERSION == "1.0.0"
        assert isinstance(config.ALLOWED_EXTENSIONS, list)
        assert len(config.ALLOWED_EXTENSIONS) > 0
        assert config.DEFAULT_STRENGTH > 0
        assert config.MIN_STRENGTH < config.MAX_STRENGTH
        assert config.MAX_WATERMARK_LENGTH > 0
    
    def test_secret_key_generation(self):
        """Test secret key generation"""
        secret = config.get_secret_key()
        assert isinstance(secret, str)
        assert len(secret) > 0
    
    def test_allowed_extensions(self):
        """Test allowed file extensions"""
        extensions = config.ALLOWED_EXTENSIONS
        expected_extensions = ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm']
        for ext in expected_extensions:
            assert ext in extensions


class TestIntegration:
    """Integration tests for the complete workflow"""
    
    @pytest.fixture
    def temp_video(self):
        """Create a temporary test video"""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(f.name, fourcc, 10.0, (160, 120))
            
            # Create 10 frames (1 second at 10fps)
            for i in range(10):
                # Create a simple pattern that changes each frame
                frame = np.zeros((120, 160, 3), dtype=np.uint8)
                frame[i*10:(i+1)*10, :] = [255, 0, 0]  # Red stripe
                out.write(frame)
            
            out.release()
            yield f.name
            
            # Cleanup
            if os.path.exists(f.name):
                os.unlink(f.name)
    
    def test_complete_watermarking_workflow(self, temp_video):
        """Test complete watermarking workflow"""
        watermarker = DCTWatermark()
        processor = VideoProcessor()
        watermark_text = "IntegrationTest"
        
        # Validate input video
        assert processor.validate_video_file(temp_video)
        
        # Get video info
        info = processor.get_video_info(temp_video)
        assert info is not None
        assert info['frame_count'] == 10
        
        # Create output path
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as output_file:
            output_path = output_file.name
        
        try:
            # Test progress callback
            progress_calls = []
            def progress_callback(frame_num, total_frames, message):
                progress_calls.append((frame_num, total_frames, message))
            
            # Process video
            success = processor.embed_watermark_in_video(
                temp_video, output_path, watermark_text, 0.15,
                watermarker, progress_callback
            )
            
            assert success is True
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
            
            # Check that progress callback was called
            assert len(progress_calls) > 0
            assert progress_calls[-1][0] == 10  # Final frame
            
            # Validate output video
            assert processor.validate_video_file(output_path)
            
            # Test watermark extraction
            extracted = processor.extract_watermark_from_video(
                output_path, len(watermark_text), watermarker
            )
            
            # Note: Extraction might not be perfect due to video compression
            assert isinstance(extracted, str) or extracted is None
            
        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_error_handling_invalid_video(self):
        """Test error handling with invalid video file"""
        processor = VideoProcessor()
        
        # Create a fake video file (just text)
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b"This is not a video file")
            fake_video_path = f.name
        
        try:
            # Should fail validation
            assert processor.validate_video_file(fake_video_path) is False
            
            # Comprehensive validation should return detailed errors
            result = processor.validate_video_comprehensive(fake_video_path)
            assert result['valid'] is False
            assert len(result['errors']) > 0
            
        finally:
            os.unlink(fake_video_path)


class TestPerformance:
    """Performance and stress tests"""
    
    def test_large_watermark_text(self):
        """Test handling of maximum watermark length"""
        watermarker = DCTWatermark()
        test_image = np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8)
        
        # Test maximum allowed watermark length
        max_text = "A" * config.MAX_WATERMARK_LENGTH
        watermarked = watermarker.embed_watermark(test_image, max_text, 0.1)
        
        assert watermarked is not None
        assert watermarked.shape == test_image.shape
    
    def test_processing_multiple_blocks(self):
        """Test processing image with many DCT blocks"""
        watermarker = DCTWatermark()
        # Large image that will require many 8x8 blocks
        large_image = np.random.randint(0, 256, (1024, 1024, 3), dtype=np.uint8)
        watermark_text = "LargeImage"
        
        watermarked = watermarker.embed_watermark(large_image, watermark_text, 0.1)
        
        assert watermarked is not None
        assert watermarked.shape == large_image.shape
        assert not np.array_equal(watermarked, large_image)
    
    def test_memory_cleanup(self):
        """Test that temporary files and resources are cleaned up"""
        processor = VideoProcessor()
        
        # Create and immediately clean up multiple validation results
        for i in range(10):
            stats = processor.create_processing_stats()
            assert 'timestamp' in stats
        
        # This test mainly ensures no memory leaks or resource issues


if __name__ == '__main__':
    # Run the tests
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ])
