"""
Demo: Quick example showing shared memory with PyArrow
Run this to see a complete sender/receiver demo in one script
"""
import numpy as np
import pyarrow as pa
from multiprocessing import shared_memory, Process
import time
import struct


def sender_process(shm_name: str, num_frames: int = 10):
    """Sender process - creates and writes to shared memory"""
    
    # Configuration
    image_shape = (100, 100, 3)
    dtype = np.uint8
    
    # Calculate sizes
    header_size = 2 + (len(image_shape) * 8)
    data_size = int(np.prod(image_shape))
    total_size = header_size + data_size
    
    # Create shared memory
    shm = shared_memory.SharedMemory(create=True, size=total_size, name=shm_name)
    
    try:
        # Wrap with PyArrow
        arrow_buffer = pa.py_buffer(shm.buf)
        buf_view = memoryview(shm.buf)
        
        # Write header
        offset = 0
        buf_view[offset] = np.dtype(dtype).num
        offset += 1
        buf_view[offset] = len(image_shape)
        offset += 1
        for dim in image_shape:
            struct.pack_into('Q', buf_view, offset, dim)
            offset += 8
        
        print(f"[Sender] Created shared memory '{shm_name}'")
        print(f"[Sender] Arrow buffer size: {len(arrow_buffer)} bytes\n")
        
        # Send frames
        for i in range(num_frames):
            # Generate frame (pattern changes each frame)
            image = np.full(image_shape, (i * 25) % 255, dtype=dtype)
            
            # Write to shared memory
            image_view = buf_view[offset:offset + data_size]
            image_view[:] = image.tobytes()
            
            print(f"[Sender] Sent frame {i+1}/{num_frames} - value: {image[0,0,0]}")
            time.sleep(0.3)
        
        print(f"[Sender] Done sending {num_frames} frames")
        time.sleep(2)  # Keep alive for receiver
        
    finally:
        shm.close()
        shm.unlink()
        print(f"[Sender] Cleaned up")


def receiver_process(shm_name: str, num_frames: int = 10):
    """Receiver process - opens and reads from shared memory with ZERO-COPY"""
    
    time.sleep(0.5)  # Wait for sender to create shared memory
    
    try:
        # Open existing shared memory
        shm = shared_memory.SharedMemory(name=shm_name)
        
        # Wrap with PyArrow (ZERO-COPY)
        arrow_buffer = pa.py_buffer(shm.buf)
        buf_view = memoryview(shm.buf)
        
        # Read header
        offset = 0
        dtype_code = buf_view[offset]
        offset += 1
        ndim = buf_view[offset]
        offset += 1
        
        shape = []
        for _ in range(ndim):
            dim = struct.unpack_from('Q', buf_view, offset)[0]
            shape.append(dim)
            offset += 8
        
        shape = tuple(shape)
        # Map dtype code back to numpy dtype
        dtype = np.dtype(np.sctypeDict.get(dtype_code, np.uint8))
        # More reliable: just construct from type code
        for np_type in [np.uint8, np.uint16, np.uint32, np.uint64, 
                        np.int8, np.int16, np.int32, np.int64,
                        np.float32, np.float64]:
            if np.dtype(np_type).num == dtype_code:
                dtype = np.dtype(np_type)
                break
        
        # Create numpy array view (ZERO-COPY)
        image = np.ndarray(shape, dtype=dtype, buffer=buf_view[offset:])
        
        print(f"[Receiver] Opened shared memory '{shm_name}'")
        print(f"[Receiver] Arrow buffer size: {len(arrow_buffer)} bytes")
        print(f"[Receiver] Image shape: {shape}, dtype: {dtype}")
        print(f"[Receiver] Memory address: {hex(image.ctypes.data)}\n")
        
        # Read frames
        last_value = None
        for i in range(num_frames * 2):  # Read more times to see updates
            current_value = image[0, 0, 0]
            
            if current_value != last_value:
                print(f"[Receiver] Frame updated! New value: {current_value}")
                last_value = current_value
            
            time.sleep(0.2)
        
        print(f"[Receiver] Done reading")
        
    finally:
        shm.close()
        print(f"[Receiver] Disconnected")


if __name__ == "__main__":
    print("=" * 60)
    print("PyArrow Shared Memory Demo")
    print("=" * 60)
    print()
    
    shm_name = "demo_arrow_shm"
    num_frames = 10
    
    # Create sender and receiver processes
    sender = Process(target=sender_process, args=(shm_name, num_frames))
    receiver = Process(target=receiver_process, args=(shm_name, num_frames))
    
    # Start both processes
    sender.start()
    receiver.start()
    
    # Wait for both to complete
    sender.join()
    receiver.join()
    
    print()
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)
    print()
    print("✓ Sender created SharedMemory")
    print("✓ Sender wrapped with PyArrow buffer")
    print("✓ Sender wrote numpy arrays")
    print("✓ Receiver opened SharedMemory by name")
    print("✓ Receiver read with ZERO-COPY")
    print()
