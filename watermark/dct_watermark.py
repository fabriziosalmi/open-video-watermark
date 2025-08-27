import numpy as np
import cv2
from PIL import Image
import hashlib
import random
from typing import Tuple, Optional, List

class DCTWatermark:
    """
    Enhanced DCT-based watermarking for robust frequency-domain embedding.
    This implementation embeds watermarks in the DCT coefficients of image blocks
    with improved robustness against compression and noise.
    """
    
    def __init__(self, block_size=8):
        self.block_size = block_size
        self.quality_factor = 50  # JPEG quality factor for robustness testing
        self.zigzag_pattern = self._generate_zigzag_pattern()
        self.embedding_positions = [(1, 2), (2, 1), (2, 2), (1, 3), (3, 1), (3, 2), (2, 3)]
    
    def _text_to_binary(self, text):
        """Convert text to binary representation"""
        return ''.join(format(ord(char), '08b') for char in text)
    
    def _binary_to_text(self, binary):
        """Convert binary representation back to text"""
        text = ''
        for i in range(0, len(binary), 8):
            byte = binary[i:i+8]
            if len(byte) == 8:
                text += chr(int(byte, 2))
        return text
    
    def _embed_bit_in_block(self, block, bit, strength=0.1):
        """Embed a single bit in a DCT block"""
        # Apply DCT
        dct_block = cv2.dct(block.astype(np.float32))
        
        # Choose mid-frequency coefficients for embedding
        # These are less likely to be affected by compression
        coeff_pos = [(1, 2), (2, 1), (2, 2), (1, 3), (3, 1)]
        
        # Use the first available coefficient position
        for pos in coeff_pos:
            y, x = pos
            if y < block.shape[0] and x < block.shape[1]:
                # Embed bit by modifying the coefficient
                if bit == '1':
                    dct_block[y, x] = abs(dct_block[y, x]) + strength * 255
                else:
                    dct_block[y, x] = abs(dct_block[y, x]) - strength * 255
                break
        
        # Apply inverse DCT
        return cv2.idct(dct_block)
    
    def _extract_bit_from_block(self, block):
        """Extract a bit from a DCT block"""
        # Apply DCT
        dct_block = cv2.dct(block.astype(np.float32))
        
        # Use the same coefficient positions as embedding
        coeff_pos = [(1, 2), (2, 1), (2, 2), (1, 3), (3, 1)]
        
        for pos in coeff_pos:
            y, x = pos
            if y < block.shape[0] and x < block.shape[1]:
                # Extract bit based on coefficient value
                return '1' if dct_block[y, x] > 0 else '0'
        
        return '0'  # Default
    
    def embed_watermark(self, image, watermark_text, strength=0.1):
        """
        Embed watermark text into an image using DCT
        
        Args:
            image: Input image (numpy array)
            watermark_text: Text to embed
            strength: Embedding strength (0.0 to 1.0)
            
        Returns:
            Watermarked image (numpy array)
        """
        if len(image.shape) == 3:
            # Convert to grayscale for processing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Convert text to binary
        binary_watermark = self._text_to_binary(watermark_text)
        
        # Pad image to ensure it's divisible by block_size
        h, w = gray.shape
        pad_h = (self.block_size - h % self.block_size) % self.block_size
        pad_w = (self.block_size - w % self.block_size) % self.block_size
        
        if pad_h > 0 or pad_w > 0:
            gray = np.pad(gray, ((0, pad_h), (0, pad_w)), mode='edge')
        
        watermarked = gray.copy().astype(np.float32)
        
        # Calculate how many blocks we need
        blocks_h = gray.shape[0] // self.block_size
        blocks_w = gray.shape[1] // self.block_size
        total_blocks = blocks_h * blocks_w
        
        # Embed watermark bits
        bit_index = 0
        for i in range(blocks_h):
            for j in range(blocks_w):
                if bit_index < len(binary_watermark):
                    # Extract block
                    y_start = i * self.block_size
                    y_end = y_start + self.block_size
                    x_start = j * self.block_size
                    x_end = x_start + self.block_size
                    
                    block = watermarked[y_start:y_end, x_start:x_end]
                    
                    # Embed bit
                    bit = binary_watermark[bit_index]
                    modified_block = self._embed_bit_in_block(block, bit, strength)
                    
                    # Replace block
                    watermarked[y_start:y_end, x_start:x_end] = modified_block
                    
                    bit_index += 1
                else:
                    break
            if bit_index >= len(binary_watermark):
                break
        
        # Remove padding if it was added
        if pad_h > 0 or pad_w > 0:
            watermarked = watermarked[:h, :w]
        
        # Convert back to original image format
        watermarked = np.clip(watermarked, 0, 255).astype(np.uint8)
        
        if len(image.shape) == 3:
            # Convert back to color
            watermarked_color = image.copy()
            watermarked_color[:, :, 0] = watermarked  # Embed in blue channel
            return watermarked_color
        else:
            return watermarked
    
    def extract_watermark(self, image, watermark_length):
        """
        Extract watermark text from an image
        
        Args:
            image: Watermarked image (numpy array)
            watermark_length: Expected length of watermark text
            
        Returns:
            Extracted watermark text
        """
        if len(image.shape) == 3:
            # Use blue channel for extraction
            gray = image[:, :, 0]
        else:
            gray = image.copy()
        
        # Pad image to ensure it's divisible by block_size
        h, w = gray.shape
        pad_h = (self.block_size - h % self.block_size) % self.block_size
        pad_w = (self.block_size - w % self.block_size) % self.block_size
        
        if pad_h > 0 or pad_w > 0:
            gray = np.pad(gray, ((0, pad_h), (0, pad_w)), mode='edge')
        
        # Calculate how many blocks we need
        blocks_h = gray.shape[0] // self.block_size
        blocks_w = gray.shape[1] // self.block_size
        
        # Extract watermark bits
        binary_watermark = ''
        bits_needed = watermark_length * 8  # 8 bits per character
        
        bit_index = 0
        for i in range(blocks_h):
            for j in range(blocks_w):
                if bit_index < bits_needed:
                    # Extract block
                    y_start = i * self.block_size
                    y_end = y_start + self.block_size
                    x_start = j * self.block_size
                    x_end = x_start + self.block_size
                    
                    block = gray[y_start:y_end, x_start:x_end].astype(np.float32)
                    
                    # Extract bit
                    bit = self._extract_bit_from_block(block)
                    binary_watermark += bit
                    
                    bit_index += 1
                else:
                    break
            if bit_index >= bits_needed:
                break
        
        # Convert binary to text
        try:
            return self._binary_to_text(binary_watermark)
        except:
            return "Error: Could not extract watermark"
    
    def _generate_zigzag_pattern(self) -> List[Tuple[int, int]]:
        """
        Generate zigzag pattern for DCT coefficient selection
        
        Returns:
            List of (y, x) coordinate tuples in zigzag order
        """
        pattern = []
        for i in range(self.block_size):
            if i % 2 == 0:  # Even rows: left to right
                for j in range(self.block_size):
                    pattern.append((i, j))
            else:  # Odd rows: right to left
                for j in range(self.block_size - 1, -1, -1):
                    pattern.append((i, j))
        return pattern
    
    def _get_robust_embedding_positions(self, strength: float) -> List[Tuple[int, int]]:
        """
        Get DCT coefficient positions for robust embedding based on strength
        
        Args:
            strength: Embedding strength
            
        Returns:
            List of coefficient positions optimized for given strength
        """
        if strength < 0.1:  # Low strength - use mid-frequency coefficients
            return [(1, 2), (2, 1), (2, 2)]
        elif strength < 0.2:  # Medium strength - add more positions
            return [(1, 2), (2, 1), (2, 2), (1, 3), (3, 1)]
        else:  # High strength - use more coefficients
            return [(1, 2), (2, 1), (2, 2), (1, 3), (3, 1), (3, 2), (2, 3)]
    
    def _embed_bit_robust(self, block: np.ndarray, bit: str, strength: float, 
                         position_index: int = 0) -> np.ndarray:
        """
        Enhanced bit embedding with improved robustness
        
        Args:
            block: DCT block to modify
            bit: Bit to embed ('0' or '1')
            strength: Embedding strength
            position_index: Which coefficient position to use
            
        Returns:
            Modified DCT block
        """
        dct_block = cv2.dct(block.astype(np.float32))
        positions = self._get_robust_embedding_positions(strength)
        
        if position_index < len(positions):
            y, x = positions[position_index]
            if y < dct_block.shape[0] and x < dct_block.shape[1]:
                # Use quantization-based embedding for better robustness
                quantization_step = 16 * strength  # Adaptive quantization
                
                if bit == '1':
                    # Round to odd multiple of quantization step
                    dct_block[y, x] = quantization_step * (2 * round(dct_block[y, x] / (2 * quantization_step)) + 1)
                else:
                    # Round to even multiple of quantization step
                    dct_block[y, x] = quantization_step * (2 * round(dct_block[y, x] / (2 * quantization_step)))
        
        return cv2.idct(dct_block)
    
    def _extract_bit_robust(self, block: np.ndarray, position_index: int = 0) -> str:
        """
        Enhanced bit extraction with improved accuracy
        
        Args:
            block: DCT block to extract from
            position_index: Which coefficient position to use
            
        Returns:
            Extracted bit ('0' or '1')
        """
        dct_block = cv2.dct(block.astype(np.float32))
        positions = self._get_robust_embedding_positions(0.15)  # Use medium strength positions
        
        if position_index < len(positions):
            y, x = positions[position_index]
            if y < dct_block.shape[0] and x < dct_block.shape[1]:
                # Extract using quantization-based detection
                quantization_step = 16 * 0.15  # Use medium strength for detection
                quantized = round(dct_block[y, x] / quantization_step)
                return '1' if quantized % 2 == 1 else '0'
        
        return '0'
    
    def embed_watermark_enhanced(self, image: np.ndarray, watermark_text: str, 
                               strength: float = 0.1, redundancy: int = 3) -> np.ndarray:
        """
        Enhanced watermark embedding with error correction and redundancy
        
        Args:
            image: Input image
            watermark_text: Text to embed
            strength: Embedding strength
            redundancy: Number of times to repeat each bit
            
        Returns:
            Watermarked image
        """
        if len(image.shape) == 3:
            # Process all color channels for better robustness
            watermarked = image.copy()
            for channel in [0, 1, 2]:  # RGB channels
                watermarked[:, :, channel] = self._embed_in_channel(
                    image[:, :, channel], watermark_text, strength, redundancy
                )
            return watermarked
        else:
            return self._embed_in_channel(image, watermark_text, strength, redundancy)
    
    def _embed_in_channel(self, channel: np.ndarray, watermark_text: str, 
                         strength: float, redundancy: int) -> np.ndarray:
        """
        Embed watermark in a single channel with redundancy
        
        Args:
            channel: Single channel image
            watermark_text: Text to embed
            strength: Embedding strength
            redundancy: Redundancy factor
            
        Returns:
            Watermarked channel
        """
        # Convert text to binary with error correction
        binary_watermark = self._text_to_binary(watermark_text)
        
        # Add redundancy by repeating each bit
        redundant_binary = ''.join(bit * redundancy for bit in binary_watermark)
        
        # Pad image
        h, w = channel.shape
        pad_h = (self.block_size - h % self.block_size) % self.block_size
        pad_w = (self.block_size - w % self.block_size) % self.block_size
        
        padded = np.pad(channel, ((0, pad_h), (0, pad_w)), mode='edge') if pad_h > 0 or pad_w > 0 else channel
        watermarked = padded.copy().astype(np.float32)
        
        # Embed with multiple positions per bit for robustness
        blocks_h = padded.shape[0] // self.block_size
        blocks_w = padded.shape[1] // self.block_size
        
        bit_index = 0
        for i in range(blocks_h):
            for j in range(blocks_w):
                if bit_index < len(redundant_binary):
                    y_start = i * self.block_size
                    y_end = y_start + self.block_size
                    x_start = j * self.block_size
                    x_end = x_start + self.block_size
                    
                    block = watermarked[y_start:y_end, x_start:x_end]
                    bit = redundant_binary[bit_index]
                    
                    # Use robust embedding
                    modified_block = self._embed_bit_robust(block, bit, strength, bit_index % len(self.embedding_positions))
                    watermarked[y_start:y_end, x_start:x_end] = modified_block
                    
                    bit_index += 1
                else:
                    break
            if bit_index >= len(redundant_binary):
                break
        
        # Remove padding
        result = watermarked[:h, :w] if pad_h > 0 or pad_w > 0 else watermarked
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def extract_watermark_enhanced(self, image: np.ndarray, watermark_length: int, 
                                 redundancy: int = 3, voting: bool = True) -> Optional[str]:
        """
        Enhanced watermark extraction with error correction
        
        Args:
            image: Watermarked image
            watermark_length: Expected watermark length
            redundancy: Redundancy factor used in embedding
            voting: Use majority voting for error correction
            
        Returns:
            Extracted watermark text or None if extraction fails
        """
        try:
            if len(image.shape) == 3:
                # Extract from multiple channels and use voting
                extracted_texts = []
                for channel in [0, 1, 2]:
                    text = self._extract_from_channel(
                        image[:, :, channel], watermark_length, redundancy, voting
                    )
                    if text:
                        extracted_texts.append(text)
                
                if extracted_texts:
                    # Return most common extraction
                    from collections import Counter
                    counter = Counter(extracted_texts)
                    return counter.most_common(1)[0][0]
            else:
                return self._extract_from_channel(image, watermark_length, redundancy, voting)
        except Exception as e:
            print(f"Error in enhanced extraction: {e}")
        
        return None
    
    def _extract_from_channel(self, channel: np.ndarray, watermark_length: int, 
                            redundancy: int, voting: bool) -> Optional[str]:
        """
        Extract watermark from single channel
        
        Args:
            channel: Single channel image
            watermark_length: Expected length
            redundancy: Redundancy factor
            voting: Use majority voting
            
        Returns:
            Extracted text or None
        """
        # Pad image
        h, w = channel.shape
        pad_h = (self.block_size - h % self.block_size) % self.block_size
        pad_w = (self.block_size - w % self.block_size) % self.block_size
        
        padded = np.pad(channel, ((0, pad_h), (0, pad_w)), mode='edge') if pad_h > 0 or pad_w > 0 else channel
        
        # Extract redundant bits
        blocks_h = padded.shape[0] // self.block_size
        blocks_w = padded.shape[1] // self.block_size
        
        extracted_bits = []
        bits_needed = watermark_length * 8 * redundancy
        
        bit_index = 0
        for i in range(blocks_h):
            for j in range(blocks_w):
                if bit_index < bits_needed:
                    y_start = i * self.block_size
                    y_end = y_start + self.block_size
                    x_start = j * self.block_size
                    x_end = x_start + self.block_size
                    
                    block = padded[y_start:y_end, x_start:x_end].astype(np.float32)
                    bit = self._extract_bit_robust(block, bit_index % len(self.embedding_positions))
                    extracted_bits.append(bit)
                    
                    bit_index += 1
                else:
                    break
            if bit_index >= bits_needed:
                break
        
        # Apply error correction using redundancy
        if voting and redundancy > 1:
            corrected_bits = []
            for i in range(0, len(extracted_bits), redundancy):
                bit_group = extracted_bits[i:i + redundancy]
                # Majority voting
                ones = sum(1 for b in bit_group if b == '1')
                corrected_bits.append('1' if ones > len(bit_group) / 2 else '0')
            binary_watermark = ''.join(corrected_bits)
        else:
            binary_watermark = ''.join(extracted_bits[:watermark_length * 8])
        
        try:
            return self._binary_to_text(binary_watermark)
        except:
            return None
    
    def test_robustness(self, image: np.ndarray, watermark_text: str, 
                       strength: float = 0.1) -> dict:
        """
        Test watermark robustness against common attacks
        
        Args:
            image: Test image
            watermark_text: Text to test
            strength: Embedding strength
            
        Returns:
            Dict with robustness test results
        """
        results = {}
        
        try:
            # Embed watermark
            watermarked = self.embed_watermark_enhanced(image, watermark_text, strength)
            
            # Test 1: No attack
            extracted = self.extract_watermark_enhanced(watermarked, len(watermark_text))
            results['no_attack'] = extracted == watermark_text
            
            # Test 2: JPEG compression
            encoded = cv2.imencode('.jpg', watermarked, [cv2.IMWRITE_JPEG_QUALITY, self.quality_factor])[1]
            compressed = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
            extracted = self.extract_watermark_enhanced(compressed, len(watermark_text))
            results['jpeg_compression'] = extracted == watermark_text
            
            # Test 3: Gaussian noise
            noise = np.random.normal(0, 5, watermarked.shape)
            noisy = np.clip(watermarked + noise, 0, 255).astype(np.uint8)
            extracted = self.extract_watermark_enhanced(noisy, len(watermark_text))
            results['gaussian_noise'] = extracted == watermark_text
            
            # Test 4: Scaling
            small = cv2.resize(watermarked, None, fx=0.5, fy=0.5)
            restored = cv2.resize(small, (watermarked.shape[1], watermarked.shape[0]))
            extracted = self.extract_watermark_enhanced(restored, len(watermark_text))
            results['scaling'] = extracted == watermark_text
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
