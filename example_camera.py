"""
Real-world example: Camera sender and display receiver using arrow_shm library

This demonstrates how you might use the library in a real application:
- Camera process: Captures images and sends via shared memory
- Display process: Receives and displays images with zero-copy
"""
from arrow_shm import SharedMemoryImageSender, SharedMemoryImageReceiver
import numpy as np
import time
from multiprocessing import Process


def camera_simulator(shm_name: str, fps: int = 30, duration: int = 10):
    """
    Simulates a camera capturing images and sending via shared memory.
    
    In a real application, replace this with:
        import cv2
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        sender.send(frame)
    """
    print(f"[Camera] Starting camera simulator at {fps} FPS")
    
    image_shape = (480, 640, 3)  # VGA resolution
    
    with SharedMemoryImageSender(shm_name, image_shape) as sender:
        print(f"[Camera] Shared memory ready")
        
        frame_count = 0
        start_time = time.time()
        frame_interval = 1.0 / fps
        
        end_time = time.time() + duration
        
        while time.time() < end_time:
            frame_start = time.time()
            
            # Simulate camera capture (replace with real camera)
            # Creating a time-varying pattern to show updates
            t = time.time() * 2
            image = np.full(image_shape, int((np.sin(t) + 1) * 127), dtype=np.uint8)
            
            # Send via shared memory (zero-copy on receiver side)
            sender.send(image)
            
            frame_count += 1
            
            # Maintain frame rate
            elapsed = time.time() - frame_start
            sleep_time = max(0, frame_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        elapsed_total = time.time() - start_time
        actual_fps = frame_count / elapsed_total
        
        print(f"\n[Camera] Sent {frame_count} frames in {elapsed_total:.2f}s")
        print(f"[Camera] Average FPS: {actual_fps:.2f}")


def display_receiver(shm_name: str, duration: int = 10):
    """
    Receives images from shared memory and "displays" them.
    
    In a real application, replace print statements with:
        import cv2
        cv2.imshow('Frame', image)
        cv2.waitKey(1)
    """
    time.sleep(0.5)  # Wait for sender to create shared memory
    
    print(f"[Display] Connecting to shared memory...")
    
    try:
        with SharedMemoryImageReceiver(shm_name) as receiver:
            print(f"[Display] Connected! Shape: {receiver.shape}, dtype: {receiver.dtype}")
            print(f"[Display] Memory address: {hex(receiver.image.ctypes.data)}")
            print(f"[Display] Zero-copy access enabled\n")
            
            frame_count = 0
            start_time = time.time()
            end_time = time.time() + duration
            
            while time.time() < end_time:
                # Get image (ZERO-COPY - instant access)
                image = receiver.get()
                
                # Process/display image (in real app, use cv2.imshow)
                # For demo, just compute stats
                mean_val = image.mean()
                
                frame_count += 1
                
                # Show stats every 30 frames
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    print(f"[Display] Frame {frame_count:4d} | FPS: {fps:6.2f} | Mean: {mean_val:6.2f}")
                
                time.sleep(0.001)  # Small delay to avoid CPU spinning
            
            elapsed_total = time.time() - start_time
            actual_fps = frame_count / elapsed_total
            
            print(f"\n[Display] Received {frame_count} frames in {elapsed_total:.2f}s")
            print(f"[Display] Average FPS: {actual_fps:.2f}")
            
    except FileNotFoundError as e:
        print(f"[Display] Error: {e}")


def main():
    """Run camera sender and display receiver"""
    print("=" * 70)
    print("Real-world Example: Camera → Shared Memory → Display")
    print("=" * 70)
    print()
    
    shm_name = "camera_shm"
    fps = 30
    duration = 10
    
    # Create processes
    camera_proc = Process(target=camera_simulator, args=(shm_name, fps, duration))
    display_proc = Process(target=display_receiver, args=(shm_name, duration))
    
    # Start both
    camera_proc.start()
    display_proc.start()
    
    # Wait for completion
    camera_proc.join()
    display_proc.join()
    
    print()
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("Key Points:")
    print("  ✓ Camera writes to shared memory using PyArrow")
    print("  ✓ Display reads with ZERO-COPY (no data duplication)")
    print("  ✓ Sub-millisecond latency (memory access only)")
    print("  ✓ Works across independent Python processes")
    print()
    print("In a real application:")
    print("  - Replace camera_simulator with cv2.VideoCapture()")
    print("  - Replace display stats with cv2.imshow()")
    print("  - Add error handling and reconnection logic")
    print()


if __name__ == "__main__":
    main()
