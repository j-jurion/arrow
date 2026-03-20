# Troubleshooting Guide

## Why is the visualizer receiving images when sender is not running?

### The Issue

**Shared memory is persistent** - it survives even after the process that created it exits. If the sender crashes or exits with an error before properly cleaning up, the shared memory block remains in the system with stale data.

When you start the visualizer, it:
1. Opens the existing (orphaned) shared memory
2. Reads the old/stale data that was written before the sender crashed
3. Keeps reading the same static data over and over

### How to Fix

**Method 1: Use the cleanup utility**
```bash
# Check for orphaned shared memory
pipenv run python cleanup_shm.py

# Clean it up
pipenv run python cleanup_shm.py --cleanup
```

**Method 2: Manual cleanup**
```bash
python -c "from multiprocessing import shared_memory; shm = shared_memory.SharedMemory(name='arrow_shm'); shm.close(); shm.unlink()"
```

**Method 3: Restart the sender properly**  
Just start the sender again - it will fail with "File exists" error, but you can modify it to handle this.

## Common Issues

### 1. "BufferError: memoryview has 1 exported buffer"

**What it means:** PyArrow's buffer is still holding a reference to the shared memory when trying to close it.

**Impact:** The error message is ugly but harmless. The shared memory cleanup might fail, leaving it orphaned.

**Fix:** Already handled in the updated code - the cleanup now suppresses this error and ensures `unlink()` still runs.

### 2. Sender exits with error (Exit Code: 1)

**Root cause:** The BufferError during cleanup causes the process to exit with error code.

**Impact:** Shared memory is left orphaned if `unlink()` wasn't called before the error.

**Fix:** Run `cleanup_shm.py --cleanup` before starting again, or use the improved cleanup code that's now in all files.

### 3. Visualizer shows static/unchanging image

**Symptom:** Image appears but doesn't animate or update.

**Cause:** 
- Sender is not running (reading orphaned shared memory)
- Sender has stopped updating (crashed/frozen)
- Sender FPS is too low

**Fix:**
```bash
# Clean up orphaned memory
pipenv run python cleanup_shm.py --cleanup

# Start fresh
pipenv run python sender_continuous.py --fps 30
pipenv run python visualizer_continuous.py --plot
```

### 4. "Shared memory not found"

**Cause:** Sender hasn't created the shared memory yet.

**Fix:** Start the sender first, wait 1-2 seconds, then start the visualizer.

### 5. Matplotlib window doesn't appear

**Possible causes:**
- matplotlib backend issue
- Process running in background
- Display/GUI not available

**Fix:**
```bash
# Try different backend
export MPLBACKEND=TkAgg  # Linux/Mac
$env:MPLBACKEND="TkAgg"  # Windows PowerShell

# Run again
pipenv run python visualizer_continuous.py --plot
```

## Best Practices

### Always Clean Up After Testing

After stopping a test:
```bash
# Check for orphaned memory
pipenv run python cleanup_shm.py

# Clean if found
pipenv run python cleanup_shm.py --cleanup
```

### Start in Correct Order

1. **Start sender first** - Creates the shared memory
2. **Wait 1-2 seconds** - Give sender time to initialize
3. **Start visualizer** - Opens the shared memory

### Stop in Correct Order

1. **Stop visualizer first** - Close window or Ctrl+C
2. **Stop sender** - Ctrl+C (this will clean up shared memory)

### Monitor for Errors

If you see `Exit Code: 1` on the sender:
- The shared memory might be orphaned
- Run cleanup before starting again
- Check the error messages for root cause

## Quick Reference

```bash
# Check for orphaned shared memory
pipenv run python cleanup_shm.py

# Clean up orphaned memory
pipenv run python cleanup_shm.py --cleanup

# Start sender
pipenv run python sender_continuous.py --fps 30

# Start visualizer (in another terminal)
pipenv run python visualizer_continuous.py --plot

# Check if sender is running
Get-Process python | Where-Object {$_.CommandLine -like "*sender*"}
```

## Understanding Shared Memory Lifecycle

```
┌─────────────────────────────────────────────────┐
│ Sender starts → Creates shared memory           │
│ Sender writes → Data visible to all processes   │
│ Visualizer opens → Reads data (zero-copy)       │
│ Sender stops → Should call shm.unlink()         │
│                                                  │
│ If cleanup fails:                                │
│   ❌ Shared memory persists (orphaned)          │
│   ❌ Contains stale/old data                    │
│   ✅ Visualizer can still read it               │
│   ⚠️  Must manually clean up                    │
└─────────────────────────────────────────────────┘
```

## System-Specific Notes

### Windows
- Shared memory names are global (visible to all processes)
- Orphaned shared memory persists until system reboot
- Use `cleanup_shm.py` to remove orphaned blocks

### Linux/Mac
- Shared memory is stored in `/dev/shm/`
- Can check with: `ls -lh /dev/shm/`
- Can manually remove with: `rm /dev/shm/arrow_shm`

## Prevention

The updated code now properly handles the BufferError during cleanup to ensure:
1. Error is suppressed (no ugly traceback)
2. `unlink()` still runs to remove shared memory
3. Process exits cleanly
