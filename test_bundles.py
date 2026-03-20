"""
test_bundles.py - Simple test to verify sender/receiver work correctly
"""
import time
from imagebundle_shm import ImageBundleListReceiver


def test_receiver():
    """Test that we can receive bundles from the running sender"""
    print("Testing ImageBundle receiver...")
    print("-" * 60)
    
    try:
        receiver = ImageBundleListReceiver("bundle_shm")
        print(f"[OK] Connected to shared memory")
        
        # Read a few frames
        for i in range(5):
            bundles = receiver.get()
            print(f"\nFrame {i + 1}:")
            print(f"  Received {len(bundles)} bundles")
            
            for j, bundle in enumerate(bundles):
                print(f"  Bundle {j + 1}:")
                print(f"    Filename: {bundle.filename}")
                print(f"    Source shape: {bundle.source_image.shape}")
                print(f"    Processed images: {list(bundle.processed_images.keys())}")
                for proc_name, proc_img in bundle.processed_images.items():
                    print(f"      - {proc_name}: {proc_img.shape}")
            
            time.sleep(0.5)
        
        receiver.cleanup()
        print("\n[OK] Test completed successfully!")
        
    except FileNotFoundError:
        print("[ERROR] Shared memory not found!")
        print("Make sure the sender is running: pipenv run python sender_bundles.py")
        return False
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = test_receiver()
    exit(0 if success else 1)
