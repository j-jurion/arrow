"""
imagebundle_shm.py - Shared memory serialization for lists of ImageBundle objects

Supports sending/receiving lists of ImageBundle objects using shared memory with PyArrow.
"""
import numpy as np
import pyarrow as pa
from multiprocessing import shared_memory
import struct
import pickle
from typing import List
from base import ImageBundle


class ImageBundleListSender:
    """
    Manages shared memory for sending lists of ImageBundle objects.
    """
    
    def __init__(self, name: str, max_size: int = 100_000_000):
        """
        Create or reuse shared memory block for ImageBundle list data.
        
        Args:
            name: Unique name for the shared memory block
            max_size: Maximum size in bytes for the shared memory (default: 100MB)
        """
        self.name = name
        self.max_size = max_size
        self.closed = False
        
        # Try to create new shared memory
        try:
            self.shm = shared_memory.SharedMemory(
                create=True,
                size=max_size,
                name=name
            )
        except FileExistsError:
            # Shared memory already exists, reuse it
            self.shm = shared_memory.SharedMemory(name=name)
            # Note: We can't verify the size of existing shared memory,
            # so we just reuse whatever size it has
        
        self.arrow_buffer = pa.py_buffer(self.shm.buf)
        self.buf_view = memoryview(self.shm.buf)
        
        print(f"[OK] Created shared memory '{name}'")
        print(f"  - Max size: {max_size:,} bytes")
    
    def send(self, bundles: List[ImageBundle]):
        """
        Write list of ImageBundle objects to shared memory.
        
        The format is:
        - 8 bytes: data length (Q)
        - N bytes: pickled data
        
        Args:
            bundles: List of ImageBundle objects to send
            
        Raises:
            ValueError: If serialized data exceeds max_size
            RuntimeError: If shared memory is closed
        """
        if self.closed:
            raise RuntimeError("SharedMemory is closed")
        
        # Serialize the bundle list using pickle
        data = pickle.dumps(bundles)
        data_len = len(data)
        
        if data_len + 8 > self.max_size:
            raise ValueError(
                f"Serialized data size ({data_len} bytes) exceeds "
                f"max_size ({self.max_size} bytes)"
            )
        
        # Write data length
        struct.pack_into('Q', self.buf_view, 0, data_len)
        
        # Write data
        self.buf_view[8:8 + data_len] = data
    
    def cleanup(self):
        """Clean up shared memory resources"""
        if not self.closed:
            # Delete references to allow proper cleanup
            del self.buf_view
            del self.arrow_buffer
            
            try:
                self.shm.close()
            except (BufferError, Exception):
                pass
            
            try:
                self.shm.unlink()
            except Exception:
                pass
            
            self.closed = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


class ImageBundleListReceiver:
    """
    Manages shared memory for receiving lists of ImageBundle objects.
    """
    
    def __init__(self, name: str):
        """
        Open existing shared memory.
        
        Args:
            name: Name of the shared memory block to open
            
        Raises:
            FileNotFoundError: If shared memory doesn't exist
        """
        self.name = name
        self.closed = False
        
        try:
            self.shm = shared_memory.SharedMemory(name=name)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Shared memory '{name}' not found. "
                "Make sure the sender is running first."
            )
        
        self.arrow_buffer = pa.py_buffer(self.shm.buf)
        self.buf_view = memoryview(self.shm.buf)
        
        print(f"[OK] Opened shared memory '{name}'")
    
    def get(self) -> List[ImageBundle]:
        """
        Get current list of ImageBundle objects from shared memory.
        
        Returns:
            List of ImageBundle objects
            
        Raises:
            RuntimeError: If shared memory is closed
        """
        if self.closed:
            raise RuntimeError("SharedMemory is closed")
        
        # Read data length
        data_len = struct.unpack_from('Q', self.buf_view, 0)[0]
        
        # Read and deserialize data
        data = bytes(self.buf_view[8:8 + data_len])
        bundles = pickle.loads(data)
        
        return bundles
    
    def cleanup(self):
        """Clean up shared memory resources"""
        if not self.closed:
            # Delete references to allow proper cleanup
            del self.buf_view
            del self.arrow_buffer
            
            try:
                self.shm.close()
            except (BufferError, Exception):
                pass
            
            self.closed = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


if __name__ == "__main__":
    # Test example
    print("Testing ImageBundleListSender/Receiver\n")
    
    # Create test bundles
    test_bundles = [
        ImageBundle(
            source_image=np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8),
            processed_images={
                "grayscale": np.random.randint(0, 255, (100, 100), dtype=np.uint8),
                "blurred": np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8),
            },
            filename="test1.jpg"
        ),
        ImageBundle(
            source_image=np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8),
            processed_images={
                "edges": np.random.randint(0, 255, (100, 100), dtype=np.uint8),
            },
            filename="test2.jpg"
        ),
    ]
    
    # Send
    with ImageBundleListSender("test_bundle_shm") as sender:
        sender.send(test_bundles)
        print(f"\n[OK] Sent {len(test_bundles)} bundles")
        
        # Receive
        with ImageBundleListReceiver("test_bundle_shm") as receiver:
            received = receiver.get()
            print(f"[OK] Received {len(received)} bundles")
            
            for i, bundle in enumerate(received):
                print(f"\nBundle {i + 1}:")
                print(f"  {bundle}")
    
    print("\n[OK] Test completed successfully")
