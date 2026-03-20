"""
Advanced example: Visualizer continuously reads updated images from shared memory
"""
import numpy as np
import pyarrow as pa
from multiprocessing import shared_memory
import struct
import time
import sys
import matplotlib.pyplot as plt
import matplotlib.animation as animation


class SharedMemoryImageReceiver:
    """
    Manages shared memory for receiving numpy arrays (images) from another process.
    Uses PyArrow for efficient buffer wrapping with ZERO-COPY access.
    """
    
    def __init__(self, shm_name: str, wait: bool = False, wait_timeout: float = 30.0):
        """
        Open existing shared memory and read metadata.
        
        Args:
            shm_name: Name of shared memory block to open
            wait: If True, wait for shared memory to be created
            wait_timeout: Maximum seconds to wait for shared memory
        """
        self.shm_name = shm_name
        
        # Open existing shared memory (with optional wait)
        if wait:
            print(f"Waiting for shared memory '{shm_name}'...")
            start_time = time.time()
            while time.time() - start_time < wait_timeout:
                try:
                    self.shm = shared_memory.SharedMemory(name=shm_name)
                    print(f"✓ Connected after {time.time() - start_time:.1f}s")
                    break
                except FileNotFoundError:
                    time.sleep(0.5)
            else:
                print(f"✗ Timeout after {wait_timeout}s waiting for '{shm_name}'")
                print("  Make sure the sender is running.")
                sys.exit(1)
        else:
            try:
                self.shm = shared_memory.SharedMemory(name=shm_name)
            except FileNotFoundError:
                print(f"✗ Shared memory '{shm_name}' not found!")
                print("  Options:")
                print(f"    1. Start the sender first")
                print(f"    2. Use --wait flag to wait for sender to start")
                sys.exit(1)
        
        # Create PyArrow buffer (zero-copy wrapper)
        self.arrow_buffer = pa.py_buffer(self.shm.buf)
        self.buf_view = memoryview(self.shm.buf)
        
        # Read metadata header
        offset = 0
        dtype_code = self.buf_view[offset]
        offset += 1
        ndim = self.buf_view[offset]
        offset += 1
        
        shape = []
        for _ in range(ndim):
            dim = struct.unpack_from('Q', self.buf_view, offset)[0]
            shape.append(dim)
            offset += 8
        
        self.shape = tuple(shape)
        # Map dtype code back to numpy dtype
        self.dtype = np.uint8  # Default
        for np_type in [np.uint8, np.uint16, np.uint32, np.uint64, 
                        np.int8, np.int16, np.int32, np.int64,
                        np.float32, np.float64]:
            if np.dtype(np_type).num == dtype_code:
                self.dtype = np.dtype(np_type)
                break
        self.header_size = offset
        
        # Create numpy array view (ZERO-COPY - directly references shared memory)
        self.image = np.ndarray(
            self.shape, 
            dtype=self.dtype, 
            buffer=self.buf_view[offset:]
        )
        
        print(f"✓ Opened shared memory '{shm_name}'")
        print(f"  - Buffer size: {len(self.arrow_buffer):,} bytes")
        print(f"  - Image shape: {self.shape}")
        print(f"  - Data type: {self.dtype}")
        print(f"  - Memory address: {hex(self.image.ctypes.data)}")
        print(f"  - ZERO-COPY: Image data is directly accessed from shared memory")
    
    def get_image(self) -> np.ndarray:
        """
        Get current image from shared memory.
        
        Returns:
            Numpy array view (zero-copy) of the current image
        """
        # The image array is already a view of shared memory,
        # so this returns immediately with no copying
        return self.image
    
    def cleanup(self):
        """Clean up shared memory resources"""
        try:
            self.shm.close()
        except (BufferError, Exception):
            # BufferError can occur due to PyArrow buffer still holding reference
            # This is expected and can be safely ignored
            pass
        print(f"✓ Disconnected from shared memory '{self.shm_name}'")


def run_visualizer(shm_name: str = "arrow_shm", show_stats: bool = True, wait: bool = False):
    """
    Run visualizer that continuously reads images from shared memory.
    
    Args:
        shm_name: Name of shared memory block
        show_stats: Whether to display frame statistics
        wait: If True, wait for sender to create shared memory
    """
    receiver = SharedMemoryImageReceiver(shm_name, wait=wait)
    
    try:
        print(f"\nReading frames from shared memory...")
        print("Press Ctrl+C to stop\n")
        
        frame_count = 0
        start_time = time.time()
        last_frame = None
        
        while True:
            # Get image (ZERO-COPY - instant access)
            image = receiver.get_image()
            
            # Compute stats
            if show_stats:
                mean_val = image.mean()
                std_val = image.std()
                min_val = image.min()
                max_val = image.max()
                
                # Detect if frame changed (optional)
                changed = "NEW" if last_frame is None or not np.array_equal(image, last_frame) else "SAME"
                if changed == "NEW":
                    # Only copy when we need to compare
                    last_frame = image.copy()
                
                frame_count += 1
                elapsed = time.time() - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0
                
                print(f"Frame {frame_count:5d} | "
                      f"FPS: {fps:6.2f} | "
                      f"Mean: {mean_val:6.2f} | "
                      f"Std: {std_val:5.2f} | "
                      f"Range: [{min_val:3d}, {max_val:3d}] | "
                      f"{changed:4s}", end='\r')
            else:
                # Just count frames
                frame_count += 1
                elapsed = time.time() - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0
                print(f"Frame {frame_count:5d} | FPS: {fps:6.2f}", end='\r')
            
            # Small delay to avoid maxing out CPU
            time.sleep(0.001)
        
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0
        print(f"\n\nReceived {frame_count} frames in {elapsed:.2f}s")
        print(f"Average FPS: {fps:.2f}")
    finally:
        receiver.cleanup()


def read_single_frame(shm_name: str = "arrow_shm"):
    """
    Read a single frame and display info.
    
    Args:
        shm_name: Name of shared memory block
    """
    receiver = SharedMemoryImageReceiver(shm_name)
    
    try:
        image = receiver.get_image()
        
        print(f"\nImage information:")
        print(f"  - Shape: {image.shape}")
        print(f"  - Dtype: {image.dtype}")
        print(f"  - Size: {image.nbytes:,} bytes")
        print(f"  - Mean: {image.mean():.2f}")
        print(f"  - Std: {image.std():.2f}")
        print(f"  - Min: {image.min()}")
        print(f"  - Max: {image.max()}")
        print(f"\nFirst pixel (RGB): {image[0, 0, :]}")
        print(f"Center pixel (RGB): {image[image.shape[0]//2, image.shape[1]//2, :]}")
        
    finally:
        receiver.cleanup()


def visualize_with_plot(shm_name: str = "arrow_shm", fps: int = 30, wait: bool = False):
    """
    Visualize images from shared memory using matplotlib with real-time updates.
    
    Args:
        shm_name: Name of shared memory block
        fps: Target refresh rate for the plot
        wait: If True, wait for sender to create shared memory
    """
    if wait:
        print(f"Waiting for shared memory '{shm_name}'...")
    else:
        print(f"Opening shared memory '{shm_name}' for visualization...")
    receiver = SharedMemoryImageReceiver(shm_name, wait=wait)
    
    # Setup matplotlib figure
    plt.ion()  # Enable interactive mode
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title(f"Shared Memory Image Viewer (Zero-Copy)\n{shm_name}", fontsize=14)
    ax.axis('off')
    
    # Get initial image
    image = receiver.get_image()
    
    # Handle grayscale vs color images
    if len(image.shape) == 2:
        # Grayscale
        im_display = ax.imshow(image, cmap='gray', vmin=0, vmax=255)
    elif image.shape[2] == 3:
        # RGB
        im_display = ax.imshow(image)
    else:
        # Other formats - show first 3 channels
        im_display = ax.imshow(image[:, :, :3])
    
    # Add stats text
    stats_text = ax.text(0.02, 0.98, '', transform=ax.transAxes,
                        verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                        fontfamily='monospace', fontsize=10)
    
    print(f"\n✓ Matplotlib window opened")
    print(f"  - Image shape: {image.shape}")
    print(f"  - Refresh rate: {fps} FPS")
    print("\nPress Ctrl+C in terminal or close window to exit\n")
    
    frame_count = 0
    start_time = time.time()
    frame_interval = 1.0 / fps
    
    try:
        while plt.fignum_exists(fig.number):
            frame_start = time.time()
            
            # Get image (ZERO-COPY - instant access)
            image = receiver.get_image()
            
            # Update image display
            im_display.set_data(image)
            
            # Update stats
            frame_count += 1
            elapsed = time.time() - start_time
            actual_fps = frame_count / elapsed if elapsed > 0 else 0
            
            stats = (f"Frame: {frame_count:5d}\n"
                    f"FPS: {actual_fps:6.2f}\n"
                    f"Mean: {image.mean():6.2f}\n"
                    f"Std: {image.std():5.2f}\n"
                    f"Range: [{image.min():3d}, {image.max():3d}]")
            stats_text.set_text(stats)
            
            # Refresh display
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
            
            # Maintain target FPS
            frame_time = time.time() - frame_start
            sleep_time = max(0, frame_interval - frame_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        print("\nWindow closed by user")
        
    except KeyboardInterrupt:
        print("\n\nStopping visualization...")
    finally:
        elapsed = time.time() - start_time
        actual_fps = frame_count / elapsed if elapsed > 0 else 0
        print(f"\nDisplayed {frame_count} frames in {elapsed:.2f}s")
        print(f"Average FPS: {actual_fps:.2f}")
        
        plt.close(fig)
        receiver.cleanup()



if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Receive images via shared memory with zero-copy"
    )
    parser.add_argument("--name", default="arrow_shm", 
                        help="Shared memory name")
    parser.add_argument("--once", action="store_true", 
                        help="Read once and exit")
    parser.add_argument("--no-stats", action="store_true", 
                        help="Disable statistics display")
    parser.add_argument("--plot", action="store_true",
                        help="Show image in matplotlib window")
    parser.add_argument("--fps", type=int, default=30,
                        help="Target FPS for plot updates (default: 30)")
    parser.add_argument("--wait", action="store_true",
                        help="Wait for sender to create shared memory (up to 30s)")
    
    args = parser.parse_args()
    
    if args.once:
        read_single_frame(args.name)
    elif args.plot:
        visualize_with_plot(args.name, args.fps, wait=args.wait)
    else:
        run_visualizer(args.name, show_stats=not args.no_stats, wait=args.wait)
