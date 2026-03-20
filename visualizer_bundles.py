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
from typing import List
from loguru import logger

from imagebundle_shm import ImageBundleListReceiver, create_shared_memory
from base import ImageBundle
from constants import (
    DEFAULT_SHM_NAME,
    DEFAULT_VISUALIZER_FPS,
    DEFAULT_MAX_BUNDLES_PER_PAGE,
)


class BundleVisualizer:
    """
    Matplotlib visualizer for ImageBundle lists with column-based layout.
    """
    
    def __init__(self, shm_name: str = DEFAULT_SHM_NAME, fps: int = DEFAULT_VISUALIZER_FPS, 
                 max_bundles_per_page: int = DEFAULT_MAX_BUNDLES_PER_PAGE, max_size: int = 100_000_000):
        """
        Initialize the visualizer and create shared memory.
        
        Args:
            shm_name: Name of shared memory block
            fps: Target refresh rate
            max_bundles_per_page: Maximum bundles per page before pagination (default: 15)
            max_size: Maximum size of shared memory in bytes (default: 100MB)
        """
        self.shm_name = shm_name
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.max_bundles_per_page = max_bundles_per_page
        
        # Create shared memory (visualizer owns it)
        logger.info(f"Creating shared memory '{shm_name}'...")
        self.shared_memory = create_shared_memory(shm_name, max_size)
        
        # Connect to shared memory as receiver
        logger.info(f"Connecting receiver to shared memory '{shm_name}'...")
        self.receiver = ImageBundleListReceiver(shm_name)
        
        # Get initial bundles to determine layout
        self.bundles = self.receiver.get()
        logger.success(f"Connected - {len(self.bundles)} bundles found")
        
        # Analyze bundle structure
        self.num_bundles = len(self.bundles)
        self.process_names = self._get_all_process_names()
        self.num_processes = len(self.process_names)
        
        logger.info(f"  - Bundles: {self.num_bundles}")
        logger.info(f"  - Processes: {self.process_names}")
        
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
        """Calculate pagination based on max bundles per page."""
        # Handle empty bundles case
        if self.num_bundles == 0:
            self.bundles_per_page = 0
            self.total_pages = 0
            logger.warning("No bundles found - waiting for sender to provide data")
            return
        
        # Use configured bundles per page
        self.bundles_per_page = min(self.max_bundles_per_page, self.num_bundles)
        
        # Calculate total pages
        self.total_pages = (self.num_bundles + self.bundles_per_page - 1) // self.bundles_per_page
        
        if self.total_pages > 1:
            logger.info(f"  - Pagination: {self.bundles_per_page} bundles/page, {self.total_pages} pages total")
    
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
        
        # Create figure with compact dimensions
        # Width: scale with number of columns
        col_width = 2.0  # inches per column
        fig_width = max(8, num_cols_page * col_width)
        
        # Height: Just enough for the content without extra space
        # Use a small fixed height per row to keep it compact
        row_height = 1.5  # Small height per row
        fig_height = num_rows * row_height
        
        # Add small space for help text if multiple pages
        if self.total_pages > 1:
            fig_height += 0.3  # Small additional height for help text
        
        self.fig = plt.figure(figsize=(fig_width, fig_height))
        
        # Remove all padding around the figure
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0, wspace=0)
        
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
        
        # Create grid with space for row labels - minimal spacing
        gs = GridSpec(num_rows, num_cols_page + 1, 
                     figure=self.fig,
                     width_ratios=[0.5] + [1] * num_cols_page,  # Narrow label column
                     height_ratios=[1] * num_rows,  # All rows equal height
                     hspace=0, wspace=0,
                     left=0, right=1, top=1, bottom=0)
        
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
            # Position text in figure coordinates (outside the axes area)
            self.fig.text(0.5, 0.01, help_text, ha='center', va='bottom',
                         fontsize=8, style='italic', 
                         bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    def _update_frame(self):
        """Update all images with new data from shared memory."""
        try:
            # Get new bundles
            old_num_bundles = self.num_bundles
            old_process_names = self.process_names
            
            self.bundles = self.receiver.get()
            self.num_bundles = len(self.bundles)
            self.process_names = self._get_all_process_names()
            self.num_processes = len(self.process_names)
            
            # Check if structure changed (number of bundles or process names)
            structure_changed = (
                self.num_bundles != old_num_bundles or
                set(self.process_names) != set(old_process_names)
            )
            
            if structure_changed:
                # Recalculate pagination
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
                    try:
                        img_obj = self.img_objects[('source', col_idx)]
                        img_obj.set_data(bundle.source_image)
                        
                        # Update filename if changed
                        ax = self.axes[('source', col_idx)]
                        ax.set_title(bundle.filename, fontsize=10, fontweight='bold', pad=2)
                    except Exception as e:
                        logger.error(f"Error updating source image at col {col_idx}: {e}")
                        logger.error(f"  Image shape: {bundle.source_image.shape}")
            
            # Update processed images
            for process_name in self.process_names:
                for col_idx, bundle in enumerate(page_bundles):
                    if (process_name, col_idx) in self.img_objects:
                        if process_name in bundle.processed_images:
                            proc_img = bundle.processed_images[process_name]
                            try:
                                img_obj = self.img_objects[(process_name, col_idx)]
                                img_obj.set_data(proc_img)
                            except Exception as e:
                                logger.error(f"Error updating {process_name} at col {col_idx}: {e}")
                                logger.error(f"  Image shape: {proc_img.shape}")
            
            # Update stats
            self.frame_count += 1
            
        except Exception as e:
            logger.error(f"\nError updating frame: {e}")
    
    def run(self):
        """Run the visualization loop."""
        try:
            logger.info(f"\nVisualizing at {self.fps} FPS")
            if self.total_pages > 1:
                logger.info(f"Pages: {self.total_pages} (use arrow keys <- -> to navigate)")
            logger.info("Press ESC to close window, or Ctrl+C to exit\n")
            
            while plt.fignum_exists(self.fig.number):
                frame_start = time.time()
                
                self._update_frame()
                
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
                # Use raw print for status line with carriage return
                print(status, end='\r')
                
                # Maintain target FPS
                frame_time = time.time() - frame_start
                sleep_time = max(0, self.frame_interval - frame_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            logger.info("\nWindow closed by user")
            
        except KeyboardInterrupt:
            logger.info("\n\nStopping visualization...")
        finally:
            plt.close(self.fig)
            
            # Delete all references to bundles (they may hold PyArrow buffer references)
            if hasattr(self, 'bundles'):
                del self.bundles
            
            # Clean up receiver and delete the object
            if hasattr(self, 'receiver'):
                self.receiver.cleanup()
                del self.receiver
            
            # Clean up shared memory (visualizer owns it)
            import gc
            try:
                # Force garbage collection to release all references
                gc.collect()
                
                # Release the internal buffer if it exists
                if hasattr(self.shared_memory, '_buf') and self.shared_memory._buf is not None:  # type: ignore
                    try:
                        self.shared_memory._buf.release()  # type: ignore
                    except (BufferError, Exception):
                        pass
                
                self.shared_memory.close()
                self.shared_memory.unlink()
                logger.success("Shared memory cleaned up")
            except Exception as e:
                logger.warning(f"Error cleaning up shared memory: {e}")
            
            elapsed = time.time() - self.start_time
            actual_fps = self.frame_count / elapsed if elapsed > 0 else 0
            logger.info(f"\nDisplayed {self.frame_count} frames in {elapsed:.2f}s")
            logger.info(f"Average FPS: {actual_fps:.2f}")
            logger.success("Visualizer cleanup complete")



if __name__ == "__main__":
    import typer
    
    def main(
        name: str = typer.Option(DEFAULT_SHM_NAME, help="Shared memory name"),
        fps: int = typer.Option(DEFAULT_VISUALIZER_FPS, help="Target FPS for visualization"),
        max_per_page: int = typer.Option(DEFAULT_MAX_BUNDLES_PER_PAGE, "--max-per-page", help="Max bundles per page"),
    ):
        """Visualize ImageBundle lists in column-based layout."""
        # Create and run visualizer (creates shared memory)
        try:
            visualizer = BundleVisualizer(name, fps, max_per_page)
            visualizer.run()
        except FileExistsError:
            logger.error(f"\nShared memory '{name}' already exists!")
            logger.info("  Options:")
            logger.info("    1. Clean it up: pipenv run python cleanup_shm.py --cleanup")
            logger.info("    2. Use a different name: --name my_custom_name")
            raise typer.Exit(code=1)
    
    typer.run(main)
