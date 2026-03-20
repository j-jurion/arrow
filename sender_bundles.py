"""
Sender for ImageBundle lists - Creates and sends multiple ImageBundles to shared memory
"""
import numpy as np
import time
from imagebundle_shm import ImageBundleListSender
from base import ImageBundle


from typing import Optional


def generate_test_bundle(filename: str, size: tuple = (200, 200)) -> ImageBundle:
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


def generate_test_bundles_from_folder(folder: str) -> list:
    """
    Generate ImageBundles from all images in a folder.
    
    Args:
        folder: Path to folder containing images
    Returns:
        List of ImageBundles
    """
    from PIL import Image
    import os
    
    bundles = []
    for filename in os.listdir(folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
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
                print(f"[WARNING] Failed to process {filename}: {e}")
    
    return bundles


def run_sender(folder: Optional[str] = None, shm_name: str = "bundle_shm", continuous: bool = False, fps: int = 2):
    """
    Run sender that sends ImageBundle list to shared memory.
    
    Args:
        folder: Folder path containing images (if None, generates test bundles)
        shm_name: Name of shared memory block
        continuous: If True, continuously update; if False, send once and exit
        fps: Update rate (frames per second) - only used if continuous=True
    """
    sender = ImageBundleListSender(shm_name)
    
    try:
        frame_count = 0
        start_time = time.time()
        frame_interval = 1.0 / fps if continuous else 0
        
        while True:
            frame_start = time.time()
            
            # Generate bundles
            if folder:
                bundles = generate_test_bundles_from_folder(folder=folder)
            else:
                # Fallback to test bundles
                bundles = [
                    generate_test_bundle(f"image_{i + 1}.jpg", size=(150, 150))
                    for i in range(3)
                ]
            
            num_bundles = len(bundles)
            
            # First frame - print startup message
            if frame_count == 0:
                if continuous:
                    print(f"\nLoaded {num_bundles} ImageBundles from {folder if folder else 'generated test data'}")
                    print(f"Sending continuously at {fps} FPS...")
                    print("Press Ctrl+C to stop\n")
                else:
                    print(f"\nLoaded {num_bundles} ImageBundles from {folder if folder else 'generated test data'}")
                    print("Sending to shared memory...")
            
            # Send to shared memory
            sender.send(bundles)
            
            frame_count += 1
            elapsed = time.time() - start_time
            
            if continuous:
                actual_fps = frame_count / elapsed if elapsed > 0 else 0
                print(f"Frame {frame_count:5d} | "
                      f"Bundles: {num_bundles} | "
                      f"Elapsed: {elapsed:6.1f}s | "
                      f"FPS: {actual_fps:6.2f}", end='\r')
            else:
                print(f"[OK] Sent {num_bundles} bundles")
                print("\nKeeping shared memory alive...")
                print("Press Ctrl+C to cleanup and exit\n")
            
            # If not continuous, send once and wait
            if not continuous:
                # Keep alive until interrupted
                while True:
                    time.sleep(1)
            
            # Sleep to maintain target FPS
            frame_time = time.time() - frame_start
            sleep_time = max(0, frame_interval - frame_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        sender.cleanup()
        print("[OK] Sender cleanup complete")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Send ImageBundle lists via shared memory")
    parser.add_argument("--folder", type=str, default=None,
                        help="Folder containing images (if not specified, generates test bundles)")
    parser.add_argument("--name", type=str, default="bundle_shm",
                        help="Shared memory name (default: bundle_shm)")
    parser.add_argument("--continuous", action="store_true",
                        help="Continuously update (default: send once and wait)")
    parser.add_argument("--fps", type=int, default=2, 
                        help="Update rate in FPS when continuous (default: 2)")
    
    args = parser.parse_args()
    run_sender(args.folder, args.name, args.continuous, args.fps)
