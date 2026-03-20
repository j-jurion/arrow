"""
Visualizer for ImageBundle lists - Displays bundles in a column-based matplotlib layout

Layout:
- Each column represents one ImageBundle
- Top row: source images with filenames
- Subsequent rows: processed images with process names on the left
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import time
import sys
from imagebundle_shm import ImageBundleListReceiver
from base import ImageBundle
from typing import List


class BundleVisualizer:
    """
    Matplotlib visualizer for ImageBundle lists with column-based layout.
    """
    
    def __init__(self, shm_name: str = "bundle_shm", fps: int = 10, max_width: int = 3000):
        """
        Initialize the visualizer.
        
        Args:
            shm_name: Name of shared memory block
            fps: Target refresh rate
            max_width: Maximum width in pixels before pagination (default: 3000)
        """
        self.shm_name = shm_name
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.max_width = max_width
        
        # Connect to shared memory
        print(f"Connecting to shared memory '{shm_name}'...")
        self.receiver = ImageBundleListReceiver(shm_name)
        
        # Get initial bundles to determine layout
        self.bundles = self.receiver.get()
        print(f"[OK] Connected - {len(self.bundles)} bundles found")
        
        # Analyze bundle structure
        self.num_bundles = len(self.bundles)
        self.process_names = self._get_all_process_names()
        self.num_processes = len(self.process_names)
        
        print(f"  - Bundles: {self.num_bundles}")
        print(f"  - Processes: {self.process_names}")
        
        # Calculate pagination
        self._calculate_pagination()
        
        # Current page
        self.current_page = 0
        
        # Create figure and axes
        self._setup_figure()
        
        # Stats
        self.frame_count = 0
        self.start_time = time.time()
    
    def _get_all_process_names(self) -> List[str]:
        """Get union of all processed image names across bundles."""
        all_names = set()
        for bundle in self.bundles:
            all_names.update(bundle.processed_images.keys())
        return sorted(list(all_names))
    
    def _calculate_pagination(self):
        """Calculate how many bundles per page based on max_width."""
        # Estimate width per bundle (assuming ~200 pixels per image)
        estimated_width_per_bundle = 200
        
        # Calculate bundles per page
        self.bundles_per_page = max(1, int(self.max_width / estimated_width_per_bundle))
        
        # Calculate total pages
        self.total_pages = (self.num_bundles + self.bundles_per_page - 1) // self.bundles_per_page
        
        if self.total_pages > 1:
            print(f"  - Pagination: {self.bundles_per_page} bundles/page, {self.total_pages} pages total")
    
    def _get_current_page_bundles(self) -> List[ImageBundle]:
        """Get bundles for the current page."""
        start_idx = self.current_page * self.bundles_per_page
        end_idx = min(start_idx + self.bundles_per_page, self.num_bundles)
        return self.bundles[start_idx:end_idx]
    
    def _on_key_press(self, event):
        """Handle keyboard events."""
        if event.key == 'escape':
            # Close the window
            plt.close(self.fig)
        elif event.key == 'right':
            # Next page
            if self.current_page < self.total_pages - 1:
                self.current_page += 1
                self._rebuild_figure()
        elif event.key == 'left':
            # Previous page
            if self.current_page > 0:
                self.current_page -= 1
                self._rebuild_figure()
    
    def _rebuild_figure(self):
        """Rebuild the entire figure for a new page."""
        # Clear the figure
        self.fig.clear()
        
        # Rebuild with new page
        self._setup_figure_content()
        
        # Redraw
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()
    
    def _setup_figure(self):
        """Create matplotlib figure with grid layout."""
        # Calculate grid size: 1 source row + N processed rows
        num_rows = 1 + self.num_processes
        num_cols_page = min(self.bundles_per_page, self.num_bundles - self.current_page * self.bundles_per_page)
        
        # Create figure
        fig_width = max(8, num_cols_page * 3)
        fig_height = max(6, num_rows * 2.5)
        self.fig = plt.figure(figsize=(fig_width, fig_height))
        
        # Connect keyboard events
        self.fig.canvas.mpl_connect('key_press_event', self._on_key_press)
        
        # Setup figure content
        self._setup_figure_content()
        
        plt.ion()
        plt.show()
    
    def _setup_figure_content(self):
        """Setup the content of the figure for the current page."""
        # Get bundles for current page
        page_bundles = self._get_current_page_bundles()
        num_cols_page = len(page_bundles)
        num_rows = 1 + self.num_processes
        
        # Create grid with space for row labels
        # We'll use a GridSpec with extra column on left for labels
        gs = GridSpec(num_rows, num_cols_page + 1, 
                     figure=self.fig,
                     width_ratios=[0.5] + [1] * num_cols_page,  # Narrow label column
                     hspace=0, wspace=0,
                     left=0.02, right=0.98, top=0.98, bottom=0.02)
        
        # Store axes and image objects
        self.axes = {}
        self.img_objects = {}
        self.text_objects = {}
        
        # Row 0: Source images
        for col_idx, bundle in enumerate(page_bundles):
            ax = self.fig.add_subplot(gs[0, col_idx + 1])
            ax.axis('off')
            ax.margins(0)
            
            # Display source image
            img = ax.imshow(bundle.source_image)
            
            # Add filename as title
            ax.set_title(bundle.filename, fontsize=10, fontweight='bold', pad=2)
            
            self.axes[('source', col_idx)] = ax
            self.img_objects[('source', col_idx)] = img
        
        # Add "Source" label on the left
        label_ax = self.fig.add_subplot(gs[0, 0])
        label_ax.axis('off')
        label_ax.text(0.5, 0.5, 'Source', 
                     ha='center', va='center', 
                     fontsize=11, fontweight='bold',
                     transform=label_ax.transAxes)
        
        # Rows 1+: Processed images
        for row_idx, process_name in enumerate(self.process_names, start=1):
            # Add row label on the left
            label_ax = self.fig.add_subplot(gs[row_idx, 0])
            label_ax.axis('off')
            label_ax.text(0.5, 0.5, process_name, 
                         ha='center', va='center', 
                         fontsize=9,
                         transform=label_ax.transAxes,
                         wrap=True)
            
            # Add processed images for each bundle
            for col_idx, bundle in enumerate(page_bundles):
                ax = self.fig.add_subplot(gs[row_idx, col_idx + 1])
                ax.axis('off')
                ax.margins(0)
                
                # Check if this bundle has this processed image
                if process_name in bundle.processed_images:
                    proc_img = bundle.processed_images[process_name]
                    
                    # Handle grayscale vs color
                    if proc_img.ndim == 2:
                        img = ax.imshow(proc_img, cmap='gray')
                    else:
                        img = ax.imshow(proc_img)
                else:
                    # Empty placeholder
                    placeholder = np.ones((50, 50, 3), dtype=np.uint8) * 240
                    img = ax.imshow(placeholder)
                    ax.text(0.5, 0.5, 'N/A', 
                           ha='center', va='center',
                           transform=ax.transAxes,
                           fontsize=8, color='gray')
                
                self.axes[(process_name, col_idx)] = ax
                self.img_objects[(process_name, col_idx)] = img
        
        # Add page indicator and help text if multiple pages
        if self.total_pages > 1:
            help_text = (f"Page {self.current_page + 1}/{self.total_pages} | "
                        f"<- -> to navigate | ESC to close")
            self.fig.text(0.5, 0.005, help_text, ha='center', va='bottom',
                         fontsize=9, style='italic')
    
    def update_frame(self):
        """Update all images with new data from shared memory."""
        try:
            # Get new bundles
            old_num_bundles = self.num_bundles
            old_process_names = self.process_names
            
            self.bundles = self.receiver.get()
            self.num_bundles = len(self.bundles)
            self.process_names = self._get_all_process_names()
            
            # Check if structure changed (number of bundles or process names)
            structure_changed = (
                self.num_bundles != old_num_bundles or
                set(self.process_names) != set(old_process_names)
            )
            
            if structure_changed:
                # Recalculate pagination
                old_total_pages = self.total_pages
                self._calculate_pagination()
                
                # Adjust current page if now out of range
                if self.current_page >= self.total_pages:
                    self.current_page = max(0, self.total_pages - 1)
                
                # Rebuild figure if pagination or structure changed
                self._rebuild_figure()
                return
            
            # Get current page bundles
            page_bundles = self._get_current_page_bundles()
            
            # Update source images
            for col_idx, bundle in enumerate(page_bundles):
                if ('source', col_idx) in self.img_objects:
                    img_obj = self.img_objects[('source', col_idx)]
                    img_obj.set_data(bundle.source_image)
                    
                    # Update filename if changed
                    ax = self.axes[('source', col_idx)]
                    ax.set_title(bundle.filename, fontsize=10, fontweight='bold', pad=2)
            
            # Update processed images
            for process_name in self.process_names:
                for col_idx, bundle in enumerate(page_bundles):
                    if (process_name, col_idx) in self.img_objects:
                        if process_name in bundle.processed_images:
                            proc_img = bundle.processed_images[process_name]
                            img_obj = self.img_objects[(process_name, col_idx)]
                            img_obj.set_data(proc_img)
            
            # Update stats
            self.frame_count += 1
            
        except Exception as e:
            print(f"\nError updating frame: {e}")
    
    def run(self):
        """Run the visualization loop."""
        try:
            print(f"\nVisualizing at {self.fps} FPS")
            if self.total_pages > 1:
                print(f"Pages: {self.total_pages} (use arrow keys <- -> to navigate)")
            print("Press ESC to close window, or Ctrl+C to exit\n")
            
            while plt.fignum_exists(self.fig.number):
                frame_start = time.time()
                
                self.update_frame()
                
                # Refresh display
                self.fig.canvas.draw_idle()
                self.fig.canvas.flush_events()
                
                # Stats
                elapsed = time.time() - self.start_time
                actual_fps = self.frame_count / elapsed if elapsed > 0 else 0
                
                status = f"Frame {self.frame_count:5d} | Bundles: {len(self.bundles)}"
                if self.total_pages > 1:
                    status += f" | Page {self.current_page + 1}/{self.total_pages}"
                status += f" | FPS: {actual_fps:6.2f}"
                print(status, end='\r')
                
                # Maintain target FPS
                frame_time = time.time() - frame_start
                sleep_time = max(0, self.frame_interval - frame_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            print("\nWindow closed by user")
            
        except KeyboardInterrupt:
            print("\n\nStopping visualization...")
        finally:
            plt.close(self.fig)
            self.receiver.cleanup()
            
            elapsed = time.time() - self.start_time
            actual_fps = self.frame_count / elapsed if elapsed > 0 else 0
            print(f"\nDisplayed {self.frame_count} frames in {elapsed:.2f}s")
            print(f"Average FPS: {actual_fps:.2f}")
            print("[OK] Visualizer cleanup complete")


def wait_for_shm(shm_name: str, timeout: float = 30.0) -> bool:
    """
    Wait for shared memory to be created.
    
    Args:
        shm_name: Name of shared memory to wait for
        timeout: Maximum seconds to wait
        
    Returns:
        True if found, False if timeout
    """
    print(f"Waiting for shared memory '{shm_name}'...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            receiver = ImageBundleListReceiver(shm_name)
            receiver.cleanup()
            print(f"[OK] Found after {time.time() - start_time:.1f}s")
            return True
        except FileNotFoundError:
            time.sleep(0.5)
    
    print(f"[ERROR] Timeout after {timeout}s")
    return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Visualize ImageBundle lists in column-based layout"
    )
    parser.add_argument("--name", type=str, default="bundle_shm",
                        help="Shared memory name (default: bundle_shm)")
    parser.add_argument("--fps", type=int, default=10,
                        help="Target FPS for visualization (default: 10)")
    parser.add_argument("--max-width", type=int, default=3000,
                        help="Max width in pixels before pagination (default: 3000)")
    parser.add_argument("--wait", action="store_true",
                        help="Wait for sender to create shared memory")
    
    args = parser.parse_args()
    
    # Wait for sender if requested
    if args.wait:
        if not wait_for_shm(args.name):
            print("Make sure the sender is running.")
            sys.exit(1)
    
    # Create and run visualizer
    try:
        visualizer = BundleVisualizer(args.name, args.fps, args.max_width)
        visualizer.run()
    except FileNotFoundError:
        print("\n[ERROR] Shared memory '{args.name}' not found!")
        print("  Options:")
        print("    1. Start the sender first: python sender_bundles.py")
        print("    2. Use --wait flag to wait for sender")
        sys.exit(1)
