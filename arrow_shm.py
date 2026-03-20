"""
arrow_shm.py - Reusable library for zero-copy image sharing using SharedMemory + PyArrow

Usage:
    # Sender side
    from arrow_shm import SharedMemoryImageSender
    sender = SharedMemoryImageSender("my_shm", (480, 640, 3))
    sender.send(image_array)
    sender.cleanup()
    
    # Receiver side  
    from arrow_shm import SharedMemoryImageReceiver
    receiver = SharedMemoryImageReceiver("my_shm")
    image = receiver.get()  # Zero-copy access
    receiver.cleanup()
"""
import numpy as np
import pyarrow as pa
from multiprocessing import shared_memory
import struct
from typing import Tuple, Optional
import sys


class SharedMemoryImageSender:
    """
    Manages shared memory for sending numpy arrays between processes.
    Uses PyArrow for efficient buffer wrapping.
    """
    
    def __init__(self, name: str, shape: Tuple[int, ...], dtype=np.uint8):
        """
        Create shared memory block for image data.
        
        Args:
            name: Unique name for the shared memory block
            shape: Shape of the numpy array (e.g., (height, width, channels))
            dtype: Data type of the array (default: np.uint8)
        """
        self.name = name
        self.shape = shape
        self.dtype = np.dtype(dtype)
        self.closed = False
        
        # Calculate sizes
        self.ndim = len(shape)
        self.header_size = 2 + (self.ndim * 8)
        self.data_size = int(np.prod(shape)) * self.dtype.itemsize
        self.total_size = self.header_size + self.data_size
        
        # Create shared memory
        self.shm = shared_memory.SharedMemory(
            create=True,
            size=self.total_size,
            name=name
        )
        
        # Create PyArrow buffer
        self.arrow_buffer = pa.py_buffer(self.shm.buf)
        self.buf_view = memoryview(self.shm.buf)
        
        # Write header
        self._write_header()
    
    def _write_header(self):
        """Write metadata header to shared memory"""
        offset = 0
        self.buf_view[offset] = self.dtype.num
        offset += 1
        self.buf_view[offset] = self.ndim
        offset += 1
        
        for dim in self.shape:
            struct.pack_into('Q', self.buf_view, offset, dim)
            offset += 8
    
    def send(self, image: np.ndarray):
        """
        Write image to shared memory.
        
        Args:
            image: Numpy array to write (must match shape and dtype)
            
        Raises:
            ValueError: If image shape or dtype doesn't match
            RuntimeError: If shared memory is closed
        """
        if self.closed:
            raise RuntimeError("SharedMemory is closed")
        
        if image.shape != self.shape:
            raise ValueError(f"Image shape {image.shape} doesn't match expected {self.shape}")
        
        if image.dtype != self.dtype:
            raise ValueError(f"Image dtype {image.dtype} doesn't match expected {self.dtype}")
        
        # Write data
        offset = self.header_size
        self.buf_view[offset:offset + self.data_size] = image.tobytes()
    
    def cleanup(self):
        """Clean up shared memory resources"""
        if not self.closed:
            try:
                self.shm.close()
            except (BufferError, Exception):
                # BufferError can occur due to PyArrow buffer still holding reference
                pass
            
            try:
                self.shm.unlink()
            except Exception:
                pass
            
            self.closed = True
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.cleanup()


class SharedMemoryImageReceiver:
    """
    Manages shared memory for receiving numpy arrays from another process.
    Provides ZERO-COPY access using PyArrow buffer wrapping.
    """
    
    def __init__(self, name: str):
        """
        Open existing shared memory and read metadata.
        
        Args:
            name: Name of the shared memory block to open
            
        Raises:
            FileNotFoundError: If shared memory doesn't exist
        """
        self.name = name
        self.closed = False
        
        # Open existing shared memory
        try:
            self.shm = shared_memory.SharedMemory(name=name)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Shared memory '{name}' not found. "
                "Make sure the sender is running first."
            )
        
        # Create PyArrow buffer (zero-copy)
        self.arrow_buffer = pa.py_buffer(self.shm.buf)
        self.buf_view = memoryview(self.shm.buf)
        
        # Read metadata
        offset = 0
        dtype_code = self.buf_view[offset]
        offset += 1
        ndim = self.buf_view[offset]
        offset += 1
        
        shape = []
        for _ in range(ndim):
            dim = struct.unpack_from('Q', self.buf_view, offset)[0]
            shape.append(dim)
            offset += 8
        
        self.shape = tuple(shape)
        self.header_size = offset
        
        # Map dtype code back to numpy dtype
        self.dtype = np.uint8  # Default
        for np_type in [np.uint8, np.uint16, np.uint32, np.uint64,
                        np.int8, np.int16, np.int32, np.int64,
                        np.float32, np.float64]:
            if np.dtype(np_type).num == dtype_code:
                self.dtype = np.dtype(np_type)
                break
        
        # Create numpy array view (ZERO-COPY)
        self._image = np.ndarray(
            self.shape,
            dtype=self.dtype,
            buffer=self.buf_view[self.header_size:]
        )
    
    def get(self) -> np.ndarray:
        """
        Get current image from shared memory.
        
        Returns:
            Numpy array view (zero-copy) of the current image
            
        Raises:
            RuntimeError: If shared memory is closed
        """
        if self.closed:
            raise RuntimeError("SharedMemory is closed")
        
        return self._image
    
    @property
    def image(self) -> np.ndarray:
        """Property accessor for image (zero-copy)"""
        return self.get()
    
    def cleanup(self):
        """Clean up shared memory resources"""
        if not self.closed:
            try:
                self.shm.close()
            except (BufferError, Exception):
                # BufferError can occur due to PyArrow buffer still holding reference
                pass
            self.closed = True
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.cleanup()


# Example usage
if __name__ == "__main__":
    print("Example usage of arrow_shm library\n")
    
    # Example 1: Basic usage
    print("Example 1: Basic sender/receiver")
    print("-" * 40)
    
    # Create and send
    with SharedMemoryImageSender("example_shm", (10, 10, 3)) as sender:
        test_image = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        sender.send(test_image)
        print("✓ Sent image to shared memory")
        
        # Receive (in same process for demo)
        with SharedMemoryImageReceiver("example_shm") as receiver:
            received_image = receiver.get()
            print(f"✓ Received image with shape {received_image.shape}")
            print(f"✓ Arrays equal: {np.array_equal(test_image, received_image)}")
            print(f"✓ Zero-copy: memory address = {hex(received_image.ctypes.data)}")
    
    print("\nLibrary ready to use!")
    print("\nImport in your code:")
    print("  from arrow_shm import SharedMemoryImageSender, SharedMemoryImageReceiver")
