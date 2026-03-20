# PyArrow Shared Memory Example

Zero-copy image sharing between processes using Python's native `multiprocessing.shared_memory` and PyArrow.

## Architecture

- **Sender**: Creates a `SharedMemory` block and writes numpy array data
- **Visualizer**: Opens the same `SharedMemory` by name and reads with zero-copy

## Key Features

✓ **Zero-copy** - Visualizer directly accesses shared memory without data duplication  
✓ **PyArrow integration** - Uses `pa.py_buffer(shm.buf)` to wrap shared memory  
✓ **Native Python** - Uses `multiprocessing.shared_memory` (Python 3.8+)  
✓ **Cross-process** - Works between independent Python processes  
✓ **High performance** - Suitable for real-time image streaming (30+ FPS)  
✓ **Visual display** - Real-time matplotlib visualization with live statistics

## Quick Start

### Test Installation

Verify everything works:
```bash
pipenv run python test_shm.py
```

### See It In Action (Matplotlib Visualization)

**Option 1: Start sender first (classic approach)**
```bash
# Terminal 1
pipenv run python sender_continuous.py --fps 30

# Terminal 2
pipenv run python visualizer_continuous.py --plot
```

**Option 2: Start visualizer first (it waits for sender)**
```bash
# Terminal 1
pipenv run python visualizer_continuous.py --plot --wait

# Terminal 2 (start anytime within 30 seconds)
pipenv run python sender_continuous.py --fps 30
```

The `--wait` flag makes the visualizer wait for the sender - **start in any order!**

### Simple Example (Static Image)

**Terminal 1 - Start sender:**
```bash
pipenv run python sender.py
```

**Terminal 2 - Start visualizer:**
```bash
pipenv run python visualizer.py
```

### Advanced Example (Continuous Updates)

**Terminal 1 - Start continuous sender:**
```bash
pipenv run python sender_continuous.py --fps 30
```

**Terminal 2 - Start continuous visualizer:**
```bash
pipenv run python visualizer_continuous.py
```

This demonstrates real-time image streaming with zero-copy access!

## Command Options

### Sender (Static)
```bash
# Keeps shared memory alive until Ctrl+C
pipenv run python sender.py
```

### Sender (Continuous)
```bash
# Stream at 30 FPS
pipenv run python sender_continuous.py --fps 30

# Stream for 60 seconds
pipenv run python sender_continuous.py --fps 30 --duration 60
```

### Visualizer (Static)
```bash
# Read continuously
pipenv run python visualizer.py

# Read once and exit
pipenv run python visualizer.py --once

# Custom shared memory name
pipenv run python visualizer.py --name my_shm
```

### Visualizer (Continuous)
```bash
# Terminal output with statistics
pipenv run python visualizer_continuous.py

# Matplotlib window visualization
pipenv run python visualizer_continuous.py --plot

# WAIT for sender (start visualizer first!)
pipenv run python visualizer_continuous.py --plot --wait

# Adjust plot refresh rate
pipenv run python visualizer_continuous.py --plot --fps 60

# Read once and exit
pipenv run python visualizer_continuous.py --once

# Minimal output
pipenv run python visualizer_continuous.py --no-stats
```

## How It Works

### Sender Side

```python
# 1. Create SharedMemory block
shm = shared_memory.SharedMemory(create=True, size=total_size, name="arrow_shm")

# 2. Wrap with PyArrow buffer
arrow_buffer = pa.py_buffer(shm.buf)

# 3. Write numpy array to shared memory
memoryview(shm.buf)[offset:] = image.tobytes()
```

### Visualizer Side

```python
# 1. Open existing SharedMemory by name
shm = shared_memory.SharedMemory(name="arrow_shm")

# 2. Wrap with PyArrow buffer (zero-copy)
arrow_buffer = pa.py_buffer(shm.buf)

# 3. Create numpy array view (zero-copy)
image = np.ndarray(shape, dtype=dtype, buffer=shm.buf[offset:])
```

## Memory Layout

The shared memory contains:
```
[dtype_code: 1 byte]
[ndim: 1 byte]
[dim_0: 8 bytes]
[dim_1: 8 bytes]
...
[image_data: width * height * channels bytes]
```

## Benefits

1. **No serialization overhead** - Direct memory access
2. **No data copying** - Visualizer reads directly from sender's memory
3. **High performance** - Suitable for high-frequency image streaming
4. **Simple API** - Uses Python's standard library

## 🎨 Visual Display

The visualizer now supports real-time visualization using matplotlib!

```bash
# Terminal 1 - Start sender
pipenv run python sender_continuous.py --fps 30

# Terminal 2 - Show in matplotlib window
pipenv run python visualizer_continuous.py --plot
```

This opens a matplotlib window showing:
- Real-time image updates (zero-copy from shared memory)
- Live statistics overlay (FPS, mean, std, range)
- 30 FPS default refresh rate (adjustable with `--fps`)

## Troubleshooting

### Visualizer shows old/static data

If the visualizer shows images but they don't update, the sender might not be running. You may be reading **orphaned shared memory** from a previous run.

**Fix:**
```bash
# Clean up orphaned shared memory
pipenv run python cleanup_shm.py --cleanup

# Start fresh
pipenv run python sender_continuous.py --fps 30
pipenv run python visualizer_continuous.py --plot
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

## 🛠️ Utilities

### cleanup_shm.py - Shared Memory Cleanup Utility

Check and clean up orphaned shared memory blocks:

```bash
# Check if shared memory exists
pipenv run python cleanup_shm.py

# Clean it up
pipenv run python cleanup_shm.py --cleanup

# Check specific name
pipenv run python cleanup_shm.py --name my_shm --cleanup
```

**When to use:**
- After a sender crashes or exits with error
- When visualizer shows static/old data
- Before starting a fresh test session

## 🚀 Performance

Real-world performance with 640×480 RGB images (~900KB):
- **Sender**: 30+ FPS sustained
- **Visualizer**: Zero-copy access (instant)
- **Latency**: Sub-millisecond (memory access only)
- **CPU Usage**: Minimal (no serialization/deserialization)

## Use Cases

Perfect for:
- 🎥 Real-time video streaming between processes
- 🤖 Computer vision pipelines (camera → processing → display)
- 🎮 Game development (rendering → post-processing)
- 📊 Live data visualization
- 🔬 Scientific computing with large arrays

## Requirements

- Python 3.8+ (for `multiprocessing.shared_memory`)
- numpy
- pyarrow

Install dependencies:
```bash
pipenv install
```

## Code Structure

- `test_shm.py` - Quick test to verify setup
- `sender.py` - Simple sender (static image)
- `visualizer.py` - Simple visualizer (reads static image)
- `sender_continuous.py` - Advanced sender (animated frames)
- `visualizer_continuous.py` - Advanced visualizer (real-time stats)
