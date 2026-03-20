"""
Sender: Creates SharedMemory and writes numpy array using PyArrow
"""
import numpy as np
import pyarrow as pa
from multiprocessing import shared_memory
import time
import struct


def create_and_send_image(shm_name: str = "arrow_shm", image_shape=(1080, 1920, 3)):
    """
    Create a SharedMemory block, write image data using PyArrow.
    
    Args:
        shm_name: Name of the shared memory block
        image_shape: Shape of the numpy array (height, width, channels)
    """
    # Create a sample image (random data for demonstration)
    image = np.random.randint(0, 255, image_shape, dtype=np.uint8)
    
    # Calculate total size needed
    # We'll store: dtype (1 byte), ndim (1 byte), shape (ndim * 8 bytes), data
    dtype_code = image.dtype.num  # numpy dtype code
    ndim = len(image.shape)
    header_size = 2 + (ndim * 8)  # dtype + ndim + shape
    data_size = image.nbytes
    total_size = header_size + data_size
    
    print(f"Creating shared memory '{shm_name}' of size {total_size} bytes")
    print(f"Image shape: {image.shape}, dtype: {image.dtype}")
    
    # Create SharedMemory block
    shm = shared_memory.SharedMemory(create=True, size=total_size, name=shm_name)
    
    try:
        # Create Arrow buffer from shared memory
        arrow_buffer = pa.py_buffer(shm.buf)
        
        # Get a writable memoryview from the buffer
        buf_view = memoryview(shm.buf)
        
        # Write metadata header
        offset = 0
        buf_view[offset] = dtype_code
        offset += 1
        buf_view[offset] = ndim
        offset += 1
        
        # Write shape
        for dim in image.shape:
            struct.pack_into('Q', buf_view, offset, dim)
            offset += 8
        
        # Write image data using numpy's efficient copy
        image_view = buf_view[offset:offset + data_size]
        image_view[:] = image.tobytes()
        
        print(f"✓ Image written to shared memory")
        print(f"  - Header size: {header_size} bytes")
        print(f"  - Data size: {data_size} bytes")
        print(f"  - Arrow buffer size: {len(arrow_buffer)} bytes")
        print(f"\nShared memory '{shm_name}' is ready for reading")
        print("Press Ctrl+C to cleanup and exit...")
        
        # Keep the process alive so visualizer can read
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nCleaning up...")
    finally:
        try:
            shm.close()
        except (BufferError, Exception):
            pass
        try:
            shm.unlink()
        except Exception:
            pass
        print("Shared memory cleaned up")


if __name__ == "__main__":
    create_and_send_image()
