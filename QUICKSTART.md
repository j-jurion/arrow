# Quick Start Guide: Matplotlib Visualization

## Step-by-Step Instructions

### 1. Open Two Terminals

You'll need two terminal windows for this demo.

### 2. Terminal 1 - Start the Sender

```bash
cd c:\Users\joeri\git\private\arrow
pipenv run python sender_continuous.py --fps 30
```

You should see:
```
✓ Created shared memory 'arrow_shm'
  - Total size: 921,626 bytes
  - Image shape: (480, 640, 3)
  - Data type: uint8

Sending images at 30 FPS...
Press Ctrl+C to stop
```

**Keep this running!** The sender continuously updates the image with animated patterns.

### 3. Terminal 2 - Start the Visualizer

```bash
cd c:\Users\joeri\git\private\arrow
pipenv run python visualizer_continuous.py --plot
```

You should see:
```
✓ Opened shared memory 'arrow_shm'
  - Buffer size: 925,696 bytes
  - Image shape: (480, 640, 3)
  - Data type: uint8
  - Memory address: 0x...
  - ZERO-COPY: Image data is directly accessed from shared memory

✓ Matplotlib window opened
  - Image shape: (480, 640, 3)
  - Refresh rate: 30 FPS

Press Ctrl+C in terminal or close window to exit
```

**A matplotlib window will appear** showing the animated image with live statistics!

### 4. What You'll See

- **Animated patterns** - Colorful sinusoidal waves that change over time
- **Live statistics** - Real-time FPS counter and image statistics
- **Zero-copy performance** - The visualizer reads directly from sender's memory

### 5. Stop the Demo

- **Close the matplotlib window**, or press **Ctrl+C** in Terminal 2
- Press **Ctrl+C** in Terminal 1 to stop the sender

## Options

### Adjust Plot Refresh Rate
```bash
# Higher refresh rate (60 FPS)
pipenv run python visualizer_continuous.py --plot --fps 60

# Lower refresh rate (10 FPS for slower systems)
pipenv run python visualizer_continuous.py --plot --fps 10
```

### Change Sender Frame Rate
```bash
# Faster updates
pipenv run python sender_continuous.py --fps 60

# Send for limited time (30 seconds)
pipenv run python sender_continuous.py --fps 30 --duration 30
```

## Troubleshooting

### "Shared memory not found"
- Make sure you start the **sender first** (Terminal 1)
- Wait 1-2 seconds for sender to initialize before starting visualizer

### Matplotlib doesn't show window
- Check that matplotlib is installed: `pipenv install`
- Try running with different backend: Add `--fps 10` to slow down updates

### Performance Issues
- Lower the FPS: `--fps 10`
- Reduce image size in sender_continuous.py (edit line 24)

## What's Happening Behind the Scenes

1. **Sender** creates a shared memory block named "arrow_shm"
2. **Sender** writes numpy arrays using `pa.py_buffer(shm.buf)` wrapper
3. **Visualizer** opens the same shared memory by name
4. **Visualizer** creates a numpy array view pointing directly to shared memory (**zero-copy**)
5. **Matplotlib** displays the numpy array and refreshes at target FPS
6. **No data copying** happens - visualizer reads directly from sender's memory

This is the fastest possible way to share images between Python processes!
