# ImageBundle Visualization

This system demonstrates high-performance sharing of image processing results using shared memory and PyArrow.

## Overview

The system can send lists of `ImageBundle` objects through shared memory and visualize them in a column-based matplotlib layout:

- **Each column** represents one `ImageBundle` 
- **Top row** shows source images with filenames
- **Subsequent rows** show processed images with process names on the left

## Structure

### Core Classes

- `ImageBundle` (in `base.py`):
  ```python
  class ImageBundle(NamedTuple):
      source_image: np.ndarray
      processed_images: dict[str, np.ndarray]
      filename: str = ""
  ```

### Modules

- **`imagebundle_shm.py`** - Serialization for ImageBundle lists
  - `ImageBundleListSender` - Sends list of bundles to shared memory
  - `ImageBundleListReceiver` - Receives bundles with zero-copy when possible

- **`sender_bundles.py`** - Sender that creates and sends test bundles
- **`visualizer_bundles.py`** - Column-based matplotlib visualizer
- **`demo_bundles.py`** - Demo script for quick testing

## Quick Start

### 1. Start the Sender (Terminal 1)
```bash
# Send test bundles (generated)
pipenv run python sender_bundles.py

# Or load images from a folder
pipenv run python sender_bundles.py --folder /path/to/images
```

This sends bundles **once** and keeps shared memory alive. Press Ctrl+C to stop.

Options:
- `--folder PATH` - Folder containing images (if not specified, generates 3 test bundles)
- `--name NAME` - Shared memory name (default: bundle_shm)
- `--continuous` - Continuously update instead of send once
- `--fps N` - Update rate when continuous (default: 2)

The number of bundles is determined by the number of images in the folder (supports .png, .jpg, .jpeg, .bmp, .gif).

### 2. Start the Visualizer (Terminal 2)
```bash
pipenv run python visualizer_bundles.py
```

Options:
- `--fps N` - Refresh rate (default: 10)
- `--name NAME` - Shared memory name (default: bundle_shm)
- `--max-width N` - Max width in pixels before pagination (default: 3000)
- `--wait` - Wait for sender to start

**Keyboard Controls:**
- **← →** (Arrow keys) - Navigate between pages when multiple pages exist
- **ESC** - Close the visualization window

Or use the demo script:
```bash
# Terminal 1
pipenv run python demo_bundles.py sender

# Terminal 2  
pipenv run python demo_bundles.py visualizer
```

## Example Usage

### Sending Images from a Folder

```bash
# Send all images from a folder
pipenv run python sender_bundles.py --folder /path/to/your/images

# Continuously update from folder at 5 FPS
pipenv run python sender_bundles.py --folder /path/to/images --continuous --fps 5
```

The sender will automatically load all supported image files (.png, .jpg, .jpeg, .bmp, .gif) from the folder and create ImageBundles with processed versions (grayscale, red channel, inverted).

### Creating and Sending Bundles Programmatically

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

# Create visualizer (connects to shared memory and creates matplotlib window)
visualizer = BundleVisualizer("my_shm", fps=10)

# Run visualization loop
visualizer.run()
```

## Visualization Layout

The matplotlib window shows:

```
                Col 1           Col 2           Col 3
              image1.jpg      image2.jpg      image3.jpg
Row Label   
                                                    
Source      [source img]    [source img]    [source img]

grayscale   [gray img]      [gray img]      [gray img]

edges       [edges img]     [edges img]     N/A

inverted    [inverted img]  N/A             [inverted img]
```

- **Filenames** appear as column headers
- **Process names** appear as row labels on the left
- **N/A** shown for missing processed images

## Performance

- Uses `pickle` for serialization (supports arbitrary numpy arrays)
- Shared memory blocks default to 100MB max size
- Zero-copy reading when possible
- Efficient matplotlib updates using `set_data()`

## Stopping

- Press **Ctrl+C** in the terminal, or
- **Close** the matplotlib window

Both sender and visualizer will cleanup shared memory properly.
