"""
Advanced example: Sender continuously updates image in shared memory
"""
import numpy as np
import pyarrow as pa
from multiprocessing import shared_memory
import time
import struct


class SharedMemoryImageSender:
    """
    Manages shared memory for sending numpy arrays (images) between processes.
    Uses PyArrow for efficient buffer wrapping.
    """
    
    def __init__(self, shm_name: str, image_shape: tuple, dtype=np.uint8):
        """
        Initialize shared memory for image data.
        
        Args:
            shm_name: Name of shared memory block
            image_shape: Shape of numpy array (height, width, channels)
            dtype: Data type of the array
        """
        self.shm_name = shm_name
        self.image_shape = image_shape
        self.dtype = np.dtype(dtype)
        
        # Calculate sizes
        self.dtype_code = self.dtype.num
        self.ndim = len(image_shape)
        self.header_size = 2 + (self.ndim * 8)  # dtype + ndim + shape
        self.data_size = int(np.prod(image_shape)) * self.dtype.itemsize
        self.total_size = self.header_size + self.data_size
        
        # Create shared memory
        self.shm = shared_memory.SharedMemory(
            create=True, 
            size=self.total_size, 
            name=shm_name
        )
        
        # Create PyArrow buffer
        self.arrow_buffer = pa.py_buffer(self.shm.buf)
        self.buf_view = memoryview(self.shm.buf)
        
        # Write header (only once)
        self._write_header()
        
        print(f"✓ Created shared memory '{shm_name}'")
        print(f"  - Total size: {self.total_size:,} bytes")
        print(f"  - Image shape: {image_shape}")
        print(f"  - Data type: {self.dtype}")
        
    def _write_header(self):
        """Write metadata header to shared memory"""
        offset = 0
        self.buf_view[offset] = self.dtype_code
        offset += 1
        self.buf_view[offset] = self.ndim
        offset += 1
        
        for dim in self.image_shape:
            struct.pack_into('Q', self.buf_view, offset, dim)
            offset += 8
    
    def send_image(self, image: np.ndarray):
        """
        Write image to shared memory.
        
        Args:
            image: Numpy array to write (must match shape and dtype)
        """
        if image.shape != self.image_shape:
            raise ValueError(f"Image shape {image.shape} doesn't match {self.image_shape}")
        if image.dtype != self.dtype:
            raise ValueError(f"Image dtype {image.dtype} doesn't match {self.dtype}")
        
        # Write data directly to shared memory (zero-copy on sender side too)
        offset = self.header_size
        image_view = self.buf_view[offset:offset + self.data_size]
        image_view[:] = image.tobytes()
    
    def cleanup(self):
        """Clean up shared memory resources"""
        try:
            self.shm.close()
        except (BufferError, Exception):
            # BufferError can occur due to PyArrow buffer still holding reference
            # This is expected and can be safely ignored
            pass
        
        try:
            self.shm.unlink()
            print(f"✓ Cleaned up shared memory '{self.shm_name}'")
        except Exception as e:
            print(f"⚠ Warning during cleanup: {e}")


def generate_animated_image(width: int, height: int, frame: int) -> np.ndarray:
    """
    Generate an animated test pattern.
    
    Args:
        width: Image width
        height: Image height
        frame: Frame number for animation
        
    Returns:
        RGB image as numpy array
    """
    # Create a moving gradient pattern
    x = np.linspace(0, 4 * np.pi, width)
    y = np.linspace(0, 4 * np.pi, height)
    xx, yy = np.meshgrid(x, y)
    
    # Animated sinusoidal pattern
    t = frame * 0.1
    r = np.sin(xx + t) * 127 + 128
    g = np.cos(yy + t) * 127 + 128
    b = np.sin(xx + yy + t) * 127 + 128
    
    image = np.stack([r, g, b], axis=-1).astype(np.uint8)
    return image


def run_sender(fps: int = 30, duration: int = None):
    """
    Run sender that continuously updates image in shared memory.
    
    Args:
        fps: Target frames per second
        duration: Duration in seconds (None for infinite)
    """
    shm_name = "arrow_shm"
    image_shape = (480, 640, 3)  # VGA resolution, RGB
    
    sender = SharedMemoryImageSender(shm_name, image_shape)
    
    try:
        print(f"\nSending images at {fps} FPS...")
        print("Press Ctrl+C to stop\n")
        
        frame_count = 0
        start_time = time.time()
        frame_interval = 1.0 / fps
        
        while True:
            frame_start = time.time()
            
            # Generate new frame
            image = generate_animated_image(
                image_shape[1], 
                image_shape[0], 
                frame_count
            )
            
            # Send to shared memory
            sender.send_image(image)
            
            frame_count += 1
            elapsed = time.time() - start_time
            actual_fps = frame_count / elapsed if elapsed > 0 else 0
            
            # Stats
            print(f"Frame {frame_count:5d} | "
                  f"Elapsed: {elapsed:6.1f}s | "
                  f"FPS: {actual_fps:6.2f} | "
                  f"Target: {fps}", end='\r')
            
            # Check duration
            if duration and elapsed >= duration:
                break
            
            # Sleep to maintain target FPS
            frame_time = time.time() - frame_start
            sleep_time = max(0, frame_interval - frame_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        print(f"\n\nSent {frame_count} frames in {elapsed:.2f}s")
        print(f"Average FPS: {actual_fps:.2f}")
        
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        sender.cleanup()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Send images via shared memory")
    parser.add_argument("--fps", type=int, default=30, help="Target FPS")
    parser.add_argument("--duration", type=int, default=None, 
                        help="Duration in seconds (default: infinite)")
    
    args = parser.parse_args()
    run_sender(args.fps, args.duration)
