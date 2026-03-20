"""
Utility to check and clean up orphaned shared memory blocks
"""
from multiprocessing import shared_memory
import sys
from constants import DEFAULT_SHM_NAME, STATUS_OK, STATUS_ERROR


def check_shared_memory(name: str = DEFAULT_SHM_NAME) -> bool:
    """
    Check if shared memory exists.
    
    Args:
        name: Shared memory block name
        
    Returns:
        True if exists, False otherwise
    """
    try:
        shm = shared_memory.SharedMemory(name=name)
        print(f"{STATUS_OK} Shared memory '{name}' exists")
        print(f"  - Size: {shm.size:,} bytes")
        shm.close()
        return True
    except FileNotFoundError:
        print(f"{STATUS_ERROR} Shared memory '{name}' does not exist")
        return False


def cleanup_shared_memory(name: str = DEFAULT_SHM_NAME) -> bool:
    """
    Clean up shared memory if it exists.
    
    Args:
        name: Shared memory block name
        
    Returns:
        True if cleaned up successfully, False otherwise
    """
    try:
        shm = shared_memory.SharedMemory(name=name)
        size = shm.size
        shm.close()
        shm.unlink()
        print(f"{STATUS_OK} Cleaned up shared memory '{name}' ({size:,} bytes)")
        return True
    except FileNotFoundError:
        print(f"{STATUS_ERROR} Shared memory '{name}' does not exist - nothing to clean")
        return False
    except Exception as e:
        print(f"{STATUS_ERROR} Error cleaning up: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check/cleanup shared memory")
    parser.add_argument("--name", default=DEFAULT_SHM_NAME, 
                        help=f"Shared memory name (default: {DEFAULT_SHM_NAME})")
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
            print(f"  pipenv run python cleanup_shm.py --name {args.name} --cleanup")
        else:
            print("\nAll clear! No orphaned shared memory found.")
