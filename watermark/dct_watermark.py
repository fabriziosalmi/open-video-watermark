import numpy as np
import cv2
from PIL import Image

class DCTWatermark:
    """
    DCT-based watermarking for robust frequency-domain embedding.
    This implementation embeds watermarks in the DCT coefficients of image blocks.
    """
    
    def __init__(self, block_size=8):
        self.block_size = block_size
    
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
