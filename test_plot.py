"""
Quick test for matplotlib visualization
Run sender and visualizer together for testing
"""
from arrow_shm import SharedMemoryImageSender
import numpy as np
import time
from multiprocessing import Process
import sys


def simple_sender():
    """Send animated pattern"""
    print("[Sender] Starting...")
    
    shape = (480, 640, 3)
    sender = SharedMemoryImageSender("arrow_shm", shape)
    
    try:
        frame = 0
        print("[Sender] Ready. Sending frames...")
        while True:
            # Create animated pattern
            t = frame * 0.1
            x = np.linspace(0, 4 * np.pi, shape[1])
            y = np.linspace(0, 4 * np.pi, shape[0])
            xx, yy = np.meshgrid(x, y)
            
            r = np.sin(xx + t) * 127 + 128
            g = np.cos(yy + t) * 127 + 128
            b = np.sin(xx + yy + t) * 127 + 128
            
            image = np.stack([r, g, b], axis=-1).astype(np.uint8)
            sender.send(image)
            
            frame += 1
            time.sleep(1/30)  # 30 FPS
            
    except KeyboardInterrupt:
        print("\n[Sender] Stopping...")
    finally:
        sender.cleanup()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sender":
        simple_sender()
    else:
        print("Starting sender in background...")
        sender_proc = Process(target=simple_sender)
        sender_proc.start()
        
        time.sleep(1)  # Wait for sender to start
        
        print("\n" + "="*60)
        print("Now run in another terminal:")
        print("  pipenv run python visualizer_continuous.py --plot")
        print("="*60 + "\n")
        
        try:
            sender_proc.join()
        except KeyboardInterrupt:
            print("\nStopping...")
            sender_proc.terminate()
            sender_proc.join()
