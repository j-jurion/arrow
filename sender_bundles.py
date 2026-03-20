"""
Sender for ImageBundle lists - Creates and sends multiple ImageBundles to shared memory
"""
import numpy as np
from typing import Optional, List
from PIL import Image
import os
from loguru import logger

from imagebundle_shm import ImageBundleListSender
from base import ImageBundle
from constants import (
    DEFAULT_SHM_NAME,
    DEFAULT_TEST_BUNDLE_COUNT,
    DEFAULT_TEST_IMAGE_SIZE,
    SUPPORTED_IMAGE_EXTENSIONS
)


def generate_test_bundle(filename: str, size: tuple[int, int] = DEFAULT_TEST_IMAGE_SIZE) -> ImageBundle:
    """
    Generate a test ImageBundle with source and processed images.
    
    Args:
        filename: Name for the bundle
        size: Size of images (height, width)
        
    Returns:
        ImageBundle with random test data
    """
    # Create source image (random RGB)
    source = np.random.randint(0, 255, (*size, 3), dtype=np.uint8)
    
    # Create some processed versions
    processed = {
        "grayscale": source.mean(axis=2).astype(np.uint8),
        "red_channel": source[:, :, 0],
        "inverted": 255 - source,
        "edges": np.random.randint(0, 255, size, dtype=np.uint8),  # Simulated edges
    }
    
    return ImageBundle(
        source_image=source,
        processed_images=processed,
        filename=filename
    )


def generate_test_bundles_from_folder(folder: str) -> List[ImageBundle]:
    """
    Generate ImageBundles from all images in a folder.
    
    Args:
        folder: Path to folder containing images
    Returns:
        List of ImageBundles
    """
    bundles = []
    for filename in os.listdir(folder):
        if filename.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
            img_path = os.path.join(folder, filename)
            try:
                img = Image.open(img_path).convert('RGB')
                img_np = np.array(img)
                
                # Create processed versions (for demo, just use variations)
                processed = {
                    "grayscale": img_np.mean(axis=2).astype(np.uint8),
                    "inverted": 255 - img_np,
                    "red_channel": img_np[:, :, 0],
                }
                
                bundle = ImageBundle(
                    source_image=img_np,
                    processed_images=processed,
                    filename=filename
                )
                bundles.append(bundle)
            except Exception as e:
                logger.warning(f"Failed to process {filename}: {e}")
    
    return bundles


def run_sender(folder: Optional[str] = None, shm_name: str = DEFAULT_SHM_NAME) -> None:
    """
    Run sender that sends ImageBundle list to shared memory.
    
    Args:
        folder: Folder path containing images (if None, generates test bundles)
        shm_name: Name of shared memory block (must be created by visualizer first)
    """
    try:
        sender = ImageBundleListSender(shm_name)
    except FileNotFoundError:
        logger.error(f"Shared memory '{shm_name}' not found!")
        logger.info("The visualizer must be started first to create shared memory.")
        logger.info("  1. Start visualizer: pipenv run python visualizer_bundles.py")
        logger.info("  2. Then start sender: pipenv run python sender_bundles.py")
        return
    
    try:
        # Generate bundles
        if folder:
            bundles = generate_test_bundles_from_folder(folder=folder)
        else:
            # Fallback to test bundles
            bundles = [
                generate_test_bundle(f"image_{i + 1}.jpg")
                for i in range(DEFAULT_TEST_BUNDLE_COUNT)
            ]
        
        num_bundles = len(bundles)
        logger.info(f"\nLoaded {num_bundles} ImageBundles from {folder if folder else 'generated test data'}")
        logger.info("Sending to shared memory...")
        
        # Send to shared memory
        sender.send(bundles)
        logger.success(f"Sent {num_bundles} bundles")
        
    except KeyboardInterrupt:
        logger.info("\n\nStopping...")
    finally:
        sender.cleanup()
        logger.success("Sender cleanup complete")


if __name__ == "__main__":
    import typer
    
    def main(
        folder: Optional[str] = typer.Option(None, help="Folder containing images (if not specified, generates test bundles)"),
        name: str = typer.Option(DEFAULT_SHM_NAME, help="Shared memory name")
    ):
        """Send ImageBundle list via shared memory."""
        run_sender(folder, name)
    
    typer.run(main)
