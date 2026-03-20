"""
Visualizer: Opens SharedMemory and reads numpy array with zero-copy using PyArrow
"""
import numpy as np
import pyarrow as pa
from multiprocessing import shared_memory
import struct
import time
import sys


def read_image_from_shm(shm_name: str = "arrow_shm", wait: bool = False, wait_timeout: float = 30.0):
    """
    Open existing SharedMemory and read image data with zero-copy.
    
    Args:
        shm_name: Name of the shared memory block to open
        wait: If True, wait for shared memory to be created
        wait_timeout: Maximum seconds to wait
        
    Returns:
        numpy array containing the image data (zero-copy view)
    """
    if wait:
        print(f"Waiting for shared memory '{shm_name}'...")
        start_time = time.time()
        shm = None
        while time.time() - start_time < wait_timeout:
            try:
                shm = shared_memory.SharedMemory(name=shm_name)
                print(f"✓ Connected after {time.time() - start_time:.1f}s")
                break
            except FileNotFoundError:
                time.sleep(0.5)
        
        if shm is None:
            print(f"✗ Timeout after {wait_timeout}s waiting for '{shm_name}'")
            print("  Make sure the sender is running.")
            sys.exit(1)
    else:
        print(f"Opening shared memory '{shm_name}'...")
        try:
            # Open existing SharedMemory (created by sender)
            shm = shared_memory.SharedMemory(name=shm_name)
        except FileNotFoundError:
            print(f"✗ Shared memory '{shm_name}' not found!")
            print("  Options:")
            print(f"    1. Start the sender first")
            print(f"    2. Use --wait flag to wait for sender")
            sys.exit(1)
    
    try:
        # Create Arrow buffer from shared memory (zero-copy)
        arrow_buffer = pa.py_buffer(shm.buf)
        
        print(f"✓ Opened shared memory: {len(arrow_buffer)} bytes")
        
        # Read metadata header
        buf_view = memoryview(shm.buf)
        offset = 0
        
        dtype_code = buf_view[offset]
        offset += 1
        ndim = buf_view[offset]
        offset += 1
        
        # Read shape
        shape = []
        for _ in range(ndim):
            dim = struct.unpack_from('Q', buf_view, offset)[0]
            shape.append(dim)
            offset += 8
        
        shape = tuple(shape)
        # Map dtype code back to numpy dtype
        dtype = np.uint8  # Default
        for np_type in [np.uint8, np.uint16, np.uint32, np.uint64, 
                        np.int8, np.int16, np.int32, np.int64,
                        np.float32, np.float64]:
            if np.dtype(np_type).num == dtype_code:
                dtype = np.dtype(np_type)
                break
        
        print(f"  - Shape: {shape}")
        print(f"  - Dtype: {dtype}")
        
        # Create numpy array from shared memory (zero-copy view)
        # The array directly references the shared memory, no copy is made
        image = np.ndarray(shape, dtype=dtype, buffer=buf_view[offset:])
        
        print(f"✓ Image loaded with ZERO-COPY")
        print(f"  - Memory address: {hex(image.ctypes.data)}")
        print(f"  - Array size: {image.nbytes} bytes")
        print(f"  - Sample values: {image[0, 0, :]} (first pixel)")
        
        return image, shm
        
    except FileNotFoundError:
        print(f"✗ Shared memory '{shm_name}' not found!")
        print("  Make sure the sender is running first.")
        sys.exit(1)


def visualize_continuous(shm_name: str = "arrow_shm", interval: float = 0.1, wait: bool = False):
    """
    Continuously read and display stats from shared memory.
    
    Args:
        shm_name: Name of the shared memory block
        interval: Time between reads in seconds
        wait: If True, wait for sender to create shared memory
    """
    image, shm = read_image_from_shm(shm_name, wait=wait)
    
    try:
        print(f"\nReading continuously (every {interval}s)...")
        print("Press Ctrl+C to exit\n")
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            # Access the image data (zero-copy)
            # In a real application, you might display it, process it, etc.
            mean_val = image.mean()
            min_val = image.min()
            max_val = image.max()
            
            frame_count += 1
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0
            
            print(f"Frame {frame_count:4d} | "
                  f"Mean: {mean_val:6.2f} | "
                  f"Min: {min_val:3d} | "
                  f"Max: {max_val:3d} | "
                  f"FPS: {fps:6.2f}", end='\r')
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        try:
            shm.close()
        except (BufferError, Exception):
            pass
        print("Disconnected from shared memory")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Visualize shared memory image")
    parser.add_argument("--name", default="arrow_shm", help="Shared memory name")
    parser.add_argument("--interval", type=float, default=0.1, 
                        help="Read interval in seconds")
    parser.add_argument("--once", action="store_true", 
                        help="Read once and exit")
    parser.add_argument("--wait", action="store_true",
                        help="Wait for sender to create shared memory (up to 30s)")
    
    args = parser.parse_args()
    
    if args.once:
        image, shm = read_image_from_shm(args.name, wait=args.wait)
        try:
            shm.close()
        except (BufferError, Exception):
            pass
    else:
        visualize_continuous(args.name, args.interval, wait=args.wait)
