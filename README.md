# ImageBundle Visualization System

High-performance image processing result sharing using shared memory with PyArrow.

## Overview

The ImageBundle system allows you to send lists of `ImageBundle` objects (source image + processed versions) through shared memory and visualize them in a column-based matplotlib layout.

**Key Features:**
- ✓ Share source images with multiple processed versions
- ✓ Column-based layout with automatic pagination
- ✓ Efficient inter-process communication via PyArrow
- ✓ Dynamic updates adapting to changing bundle counts
- ✓ Load images directly from folders
- ✓ Zero-copy reading when possible

## Quick Start

### 1. Start the Sender

**Generate test bundles:**
```bash
pipenv run python sender_bundles.py
```

**Load images from a folder:**
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
├── base.py                  # ImageBundle data structure
├── constants.py             # Centralized configuration
├── imagebundle_shm.py       # Shared memory serialization
├── sender_bundles.py        # Send ImageBundles to shared memory
├── visualizer_bundles.py    # Matplotlib visualization
├── cleanup_shm.py           # Cleanup utility
└── README.md               # This file
```

## ImageBundle Structure

```python
class ImageBundle(NamedTuple):
    source_image: np.ndarray              # Original image
    processed_images: dict[str, np.ndarray]  # Processed versions
    filename: str                         # Image filename
```

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

## Programmatic Usage

### Creating and Sending Bundles

```python
from imagebundle_shm import ImageBundleListSender
from base import ImageBundle
import numpy as np

# Create sender
sender = ImageBundleListSender("my_shm")

# Create bundles
bundles = [
    ImageBundle(
        source_image=np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8),
        processed_images={
            "grayscale": np.random.randint(0, 255, (200, 200), dtype=np.uint8),
            "edges": np.random.randint(0, 255, (200, 200), dtype=np.uint8),
        },
        filename="image1.jpg"
    ),
    # ... more bundles
]

# Send to shared memory
sender.send(bundles)

# Cleanup
sender.cleanup()
```

### Receiving and Visualizing

```python
from visualizer_bundles import BundleVisualizer

# Create visualizer (connects to shared memory)
visualizer = BundleVisualizer("my_shm", fps=10, max_bundles_per_page=15)

# Run visualization loop
visualizer.run()
```

## Visualization Layout

The matplotlib window displays bundles in a grid:

```
                Col 1           Col 2           Col 3
              image1.jpg      image2.jpg      image3.jpg
                                                    
Source      [source img]    [source img]    [source img]
grayscale   [gray img]      [gray img]      [gray img]
edges       [edges img]     [edges img]     N/A
inverted    [inverted img]  N/A             [inverted img]
```

- **Filenames** appear as column headers
- **Process names** appear as row labels on the left
- **N/A** shown for missing processed images

## Command Options

### Sender (`sender_bundles.py`)

```bash
--folder PATH    # Folder with images (generates test data if not specified)
--name NAME      # Shared memory name (default: bundle_shm)
--continuous     # Continuously update (default: send once)
--fps N          # Update rate in FPS when continuous (default: 2)
```

**Supported formats:** `.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`

### Visualizer (`visualizer_bundles.py`)

```bash
--name NAME        # Shared memory name (default: bundle_shm)
--fps N            # Refresh rate (default: 10)
--max-per-page N   # Max bundles per page (default: 15)
--wait             # Wait for sender to start
```

### Cleanup (`cleanup_shm.py`)

```bash
--name NAME    # Shared memory name (default: bundle_shm)
--check        # Only check if exists
--cleanup      # Clean up shared memory
```

## Configuration

Default values are defined in [constants.py](constants.py):

```python
DEFAULT_SHM_NAME = "bundle_shm"
DEFAULT_SHM_SIZE = 100_000_000  # 100 MB
DEFAULT_SENDER_FPS = 2
DEFAULT_VISUALIZER_FPS = 10
DEFAULT_MAX_BUNDLES_PER_PAGE = 15
```

## Performance

- Uses `pickle` for serialization (supports arbitrary numpy arrays)
- Shared memory blocks default to 100MB max size
- Zero-copy reading when possible
- Efficient matplotlib updates using `set_data()`

## Troubleshooting

### Orphaned Shared Memory

If the sender crashes, clean up orphaned shared memory:

```bash
pipenv run python cleanup_shm.py --cleanup
```

### "Shared memory not found"

Make sure the sender is running before starting the visualizer, or use `--wait`:

```bash
pipenv run python visualizer_bundles.py --wait
```

### Out of Memory

If bundles are too large, reduce the number per update or increase `max_size`:

```python
sender = ImageBundleListSender("my_shm", max_size=200_000_000)  # 200 MB
```

## Stopping

- Press **Ctrl+C** in the terminal, or
- **Close** the matplotlib window

Both sender and visualizer will cleanup shared memory properly.
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
