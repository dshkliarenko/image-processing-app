import cv2
import numpy as np

from app.database import calculate_image_hash


class TestImageHashing:
    """Test image hashing functionality"""

    def test_calculate_image_hash_consistency(self):
        """Test that same image always generates same hash"""
        # Create simple test image data
        img = np.zeros((50, 50, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', img)
        image_bytes = buffer.tobytes()

        hash1 = calculate_image_hash(image_bytes)
        hash2 = calculate_image_hash(image_bytes)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64-char hex string

    def test_different_images_different_hashes(self):
        """Test that different images generate different hashes"""
        # Create two different images
        img1 = np.zeros((50, 50, 3), dtype=np.uint8)
        img2 = np.ones((50, 50, 3), dtype=np.uint8) * 255

        _, buffer1 = cv2.imencode('.jpg', img1)
        _, buffer2 = cv2.imencode('.jpg', img2)

        bytes1 = buffer1.tobytes()
        bytes2 = buffer2.tobytes()

        hash1 = calculate_image_hash(bytes1)
        hash2 = calculate_image_hash(bytes2)

        # Different images should produce different hashes
        assert hash1 != hash2

class TestCoreFeatures:
    """Test edge cases and core functionality"""

    def test_empty_data_handling(self):
        """Test handling of empty data"""
        # Empty data should still produce a hash (it's valid SHA-256 input)
        hash_empty = calculate_image_hash(b"")
        assert len(hash_empty) == 64
        assert isinstance(hash_empty, str)