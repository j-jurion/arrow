# ImageBundle Visualization System

Share and visualize image processing results using shared memory with PyArrow.

## Overview

Send lists of `ImageBundle` objects (source image + processed versions) through shared memory and display them in a column-based matplotlib layout.

## Key Features

✓ **ImageBundle Support** - Share source images with multiple processed versions  
✓ **Column Layout** - Each bundle displayed as a column with process labels  
✓ **Pagination** - Automatic pagination for many images with keyboard navigation  
✓ **Shared Memory** - Efficient inter-process communication via PyArrow  
✓ **Dynamic Updates** - Automatically adapts to changing bundle counts  
✓ **Folder Loading** - Load images directly from disk folders  

## Quick Start

### 1. Start the Sender

Send test bundles:
```bash
pipenv run python sender_bundles.py
```

Load images from a folder:
```bash
pipenv run python sender_bundles.py --folder /path/to/images
```

### 2. Start the Visualizer

```bash
pipenv run python visualizer_bundles.py --wait
```

**Keyboard Controls:**
- **← →** - Navigate between pages
- **ESC** - Close window

## Project Structure

```
├── base.py                  # ImageBundle class definition
├── imagebundle_shm.py       # Shared memory serialization
├── sender_bundles.py        # Send ImageBundles to shared memory
├── visualizer_bundles.py    # Visualize ImageBundles in matplotlib
├── cleanup_shm.py           # Cleanup utility for shared memory
└── IMAGEBUNDLE.md          # Detailed documentation
```

## ImageBundle Structure

```python
class ImageBundle(NamedTuple):
    source_image: np.ndarray              # Original image
    processed_images: dict[str, np.ndarray]  # Processed versions
    filename: str                         # Image filename
```

## Usage Examples

## Usage Examples

### Load Images from Folder

```bash
# Terminal 1 - Send bundles from folder
pipenv run python sender_bundles.py --folder /path/to/images

# Terminal 2 - Visualize
pipenv run python visualizer_bundles.py --wait
```

### Generate Test Bundles

```bash
# Terminal 1 - Send 3 test bundles
pipenv run python sender_bundles.py

# Terminal 2 - Visualize with pagination (10 bundles per page)
pipenv run python visualizer_bundles.py --max-per-page 10
```

### Continuous Mode

```bash
# Continuously update at 5 FPS
pipenv run python sender_bundles.py --folder /path/to/images --continuous --fps 5
```

## Command Options

### Sender Options

```bash
--folder PATH    # Folder containing images (generates test data if not specified)
--name NAME      # Shared memory name (default: bundle_shm)
--continuous     # Continuously update (default: send once)
--fps N          # Update rate in FPS for continuous mode (default: 2)
```

### Visualizer Options

```bash
--name NAME       # Shared memory name (default: bundle_shm)
--fps N           # Refresh rate (default: 10)
--max-per-page N  # Max bundles per page (default: 15)
--wait            # Wait for sender to start
```

## Visualization Layout

```
         Col 1       Col 2       Col 3
       img1.jpg    img2.jpg    img3.jpg

Source  [image]     [image]     [image]

gray    [gray]      [gray]      [gray]

edges   [edges]     N/A         [edges]
```

- **Filenames** at top of each column
- **Process names** on the left of each row
- **Pagination** when many images (use ← → arrows)

## Cleanup

Remove shared memory blocks:
```bash
pipenv run python cleanup_shm.py
```

## Documentation

See [IMAGEBUNDLE.md](IMAGEBUNDLE.md) for detailed documentation and API reference.

## Requirements

- Python 3.12+
- numpy
- matplotlib
- Pillow
- pyarrow

Install with:
```bash
pipenv install
```
