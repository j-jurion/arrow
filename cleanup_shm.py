"""
Utility to check and clean up orphaned shared memory blocks
"""
from multiprocessing import shared_memory
import sys


def check_shared_memory(name: str = "arrow_shm"):
    """Check if shared memory exists"""
    try:
        shm = shared_memory.SharedMemory(name=name)
        print(f"✓ Shared memory '{name}' exists")
        print(f"  - Size: {shm.size:,} bytes")
        shm.close()
        return True
    except FileNotFoundError:
        print(f"✗ Shared memory '{name}' does not exist")
        return False


def cleanup_shared_memory(name: str = "arrow_shm"):
    """Clean up shared memory if it exists"""
    try:
        shm = shared_memory.SharedMemory(name=name)
        size = shm.size
        shm.close()
        shm.unlink()
        print(f"✓ Cleaned up shared memory '{name}' ({size:,} bytes)")
        return True
    except FileNotFoundError:
        print(f"✗ Shared memory '{name}' does not exist - nothing to clean")
        return False
    except Exception as e:
        print(f"✗ Error cleaning up: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check/cleanup shared memory")
    parser.add_argument("--name", default="arrow_shm", 
                        help="Shared memory name")
    parser.add_argument("--cleanup", action="store_true",
                        help="Clean up the shared memory")
    parser.add_argument("--check", action="store_true",
                        help="Only check if shared memory exists")
    
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_shared_memory(args.name)
    elif args.check:
        exists = check_shared_memory(args.name)
        sys.exit(0 if exists else 1)
    else:
        # Default: check and offer to cleanup
        print(f"Checking shared memory '{args.name}'...\n")
        if check_shared_memory(args.name):
            print("\nThis might be orphaned from a previous run.")
            print("Run with --cleanup to remove it:")
            print(f"  pipenv run python cleanup_shm.py --cleanup")
        else:
            print("\nAll clear! No orphaned shared memory found.")
