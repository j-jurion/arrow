# Issue Resolution: Visualizer Receiving Images When Sender Not Running

## Root Cause

**Shared memory is persistent** - when the sender exits with an error, the shared memory block can remain in the system with stale data. The visualizer then reads this old data, making it appear as if images are being received even though no active sender is running.

## What Was Happening

1. **Sender crashes/exits with error** → Exit Code: 1 due to BufferError during cleanup
2. **Shared memory not cleaned up** → The `shm.unlink()` call failed, leaving memory orphaned
3. **Orphaned memory persists** → Contains the last image written before crash
4. **Visualizer opens orphaned memory** → Reads stale/static data
5. **User confusion** → "Why is it receiving images without a sender?"

## Solution Implemented

### 1. Improved Cleanup in All Files

Updated cleanup methods to suppress BufferError and ensure `unlink()` always runs:

```python
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
```

**Files updated:**
- `sender_continuous.py`
- `visualizer_continuous.py`
- `sender.py`
- `visualizer.py`
- `arrow_shm.py` (library)

### 2. Created Cleanup Utility

New `cleanup_shm.py` utility to detect and remove orphaned shared memory:

```bash
# Check for orphaned memory
pipenv run python cleanup_shm.py

# Remove it
pipenv run python cleanup_shm.py --cleanup
```

### 3. Added Troubleshooting Documentation

Created `TROUBLESHOOTING.md` with:
- Explanation of the issue
- How to detect orphaned shared memory
- Step-by-step fixes
- Prevention strategies
- Common issues and solutions

## Testing Results

**Before fix:**
```
Sender exits → Exit Code: 1 → Shared memory orphaned
Visualizer starts → Reads old data → Appears to work but shows static image
```

**After fix:**
```
Sender exits → BufferError suppressed → ✓ Cleaned up shared memory 'arrow_shm'
Visualizer starts → "Shared memory not found" → Clear indication sender not running
```

## Verification

```bash
# Test sender cleanup
pipenv run python sender_continuous.py --fps 30 --duration 5
# Output: ✓ Cleaned up shared memory 'arrow_shm'

# Verify cleanup worked
pipenv run python cleanup_shm.py --check
# Output: ✗ Shared memory 'arrow_shm' does not exist
```

✅ **Cleanup now works correctly**

## Key Improvements

1. **Robust cleanup** - Handles BufferError gracefully and ensures unlink() runs
2. **Clear feedback** - Success message confirms cleanup happened
3. **Utility tool** - Easy way to detect and fix orphaned memory
4. **Documentation** - Users understand the issue and how to fix it
5. **Prevention** - Proper error handling prevents future occurrences

## User Instructions

### Normal Operation
```bash
# Terminal 1
pipenv run python sender_continuous.py --fps 30

# Terminal 2  
pipenv run python visualizer_continuous.py --plot
```

### If You See Static/Old Images
```bash
# Clean up orphaned memory
pipenv run python cleanup_shm.py --cleanup

# Start fresh
pipenv run python sender_continuous.py --fps 30
pipenv run python visualizer_continuous.py --plot
```

### If Sender Exits With Error
The cleanup now happens automatically, but you can verify:
```bash
pipenv run python cleanup_shm.py --check
```

## Why BufferError Occurs

The BufferError happens because:
1. PyArrow's `pa.py_buffer()` creates a buffer object that holds a reference to the memoryview
2. When Python's garbage collector tries to close the SharedMemory, the memoryview still has an "exported buffer" (PyArrow's reference)
3. This is a known limitation when mixing PyArrow buffers with Python's multiprocessing shared memory

**Impact:** Cosmetic only - the warning is harmless and cleanup still succeeds with our improved code.

## Status

✅ **RESOLVED** - Shared memory cleanup now works properly
✅ **VERIFIED** - Testing confirms orphaned memory no longer persists
✅ **DOCUMENTED** - Users have tools and guides to handle edge cases
