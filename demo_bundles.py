"""
demo_bundles.py - Demo showing ImageBundle list visualization

This demonstrates sending and visualizing multiple ImageBundle objects.

Usage:
    1. In one terminal: python demo_bundles.py sender
    2. In another terminal: python demo_bundles.py visualizer
"""
import sys
import time
from pathlib import Path


def demo_sender():
    """Run the sender demo"""
    print("=" * 60)
    print("ImageBundle Sender Demo")
    print("=" * 60)
    print("\nThis will send 3 test ImageBundles to shared memory once.")
    print("Each bundle contains:")
    print("  - Source image (random RGB)")
    print("  - Processed images (grayscale, red channel, inverted, edges)")
    print("\nStart the visualizer in another terminal:")
    print("  python demo_bundles.py visualizer")
    print("\nThe sender will keep shared memory alive until you stop it.")
    print("Press Ctrl+C to cleanup and exit\n")
    
    time.sleep(2)
    
    from sender_bundles import run_sender
    run_sender(folder=None, shm_name="bundle_shm", continuous=False)


def demo_visualizer():
    """Run the visualizer demo"""
    print("=" * 60)
    print("ImageBundle Visualizer Demo")
    print("=" * 60)
    print("\nThis will visualize ImageBundles from shared memory.")
    print("\nLayout:")
    print("  - Each column = one ImageBundle")
    print("  - Top row = source images with filenames")
    print("  - Rows below = processed images with labels on left")
    print("\nMake sure sender is running first!")
    print("  python demo_bundles.py sender")
    print("\nPress Ctrl+C or close window to stop\n")
    
    time.sleep(2)
    
    from visualizer_bundles import BundleVisualizer
    try:
        visualizer = BundleVisualizer("bundle_shm", fps=10)
        visualizer.run()
    except FileNotFoundError:
        print("\n[ERROR] Error: Shared memory not found!")
        print("\nPlease start the sender first:")
        print("  python demo_bundles.py sender")
        sys.exit(1)


def show_help():
    """Show help message"""
    print("ImageBundle Demo")
    print("=" * 60)
    print("\nUsage:")
    print("  python demo_bundles.py sender      - Run sender")
    print("  python demo_bundles.py visualizer  - Run visualizer")
    print("\nQuick Start:")
    print("  1. Terminal 1: pipenv run python demo_bundles.py sender")
    print("  2. Terminal 2: pipenv run python demo_bundles.py visualizer")
    print("\nThe visualizer will show a matplotlib window with:")
    print("  - Columns for each ImageBundle")
    print("  - Source images on top with filenames")
    print("  - Processed images below with labels")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)
    
    mode = sys.argv[1].lower()
    
    if mode == "sender":
        demo_sender()
    elif mode == "visualizer":
        demo_visualizer()
    else:
        show_help()
