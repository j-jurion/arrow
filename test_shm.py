"""
Quick test to verify shared memory setup works correctly
"""
import numpy as np
import pyarrow as pa
from multiprocessing import shared_memory
import sys


def test_shared_memory():
    """Test basic shared memory functionality"""
    print("Testing shared memory with PyArrow...\n")
    
    # Test parameters
    shm_name = "test_arrow_shm"
    test_array = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint8)
    
    print(f"1. Creating test array:")
    print(f"   Shape: {test_array.shape}")
    print(f"   Dtype: {test_array.dtype}")
    print(f"   Data:\n{test_array}\n")
    
    # Create shared memory
    try:
        shm = shared_memory.SharedMemory(create=True, size=test_array.nbytes, name=shm_name)
        print(f"2. Created shared memory '{shm_name}' ({test_array.nbytes} bytes)")
        
        # Wrap with PyArrow
        arrow_buffer = pa.py_buffer(shm.buf)
        print(f"3. Created PyArrow buffer ({len(arrow_buffer)} bytes)")
        
        # Write data
        memoryview(shm.buf)[:] = test_array.tobytes()
        print(f"4. Written data to shared memory\n")
        
        # Read back (zero-copy)
        result = np.ndarray(test_array.shape, dtype=test_array.dtype, buffer=shm.buf)
        print(f"5. Read back with zero-copy:")
        print(f"   Shape: {result.shape}")
        print(f"   Data:\n{result}\n")
        
        # Verify
        if np.array_equal(test_array, result):
            print("✓ SUCCESS: Data matches!")
            print(f"✓ Memory address: {hex(result.ctypes.data)}")
            print(f"✓ PyArrow integration working")
            return_code = 0
        else:
            print("✗ FAILED: Data mismatch!")
            return_code = 1
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return_code = 1
    finally:
        try:
            shm.close()
            shm.unlink()
            print("\nCleaned up shared memory")
        except:
            pass
    
    sys.exit(return_code)


if __name__ == "__main__":
    test_shared_memory()
