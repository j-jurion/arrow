"""
Utility to check and clean up orphaned shared memory blocks
"""
from multiprocessing import shared_memory
from loguru import logger

from constants import DEFAULT_SHM_NAME


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
        logger.success(f"Shared memory '{name}' exists")
        logger.info(f"  - Size: {shm.size:,} bytes")
        shm.close()
        return True
    except FileNotFoundError:
        logger.error(f"Shared memory '{name}' does not exist")
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
        logger.success(f"Cleaned up shared memory '{name}' ({size:,} bytes)")
        return True
    except FileNotFoundError:
        logger.error(f"Shared memory '{name}' does not exist - nothing to clean")
        return False
    except Exception as e:
        logger.error(f"Error cleaning up: {e}")
        return False


if __name__ == "__main__":
    import typer
    
    def main(
        name: str = typer.Option(DEFAULT_SHM_NAME, help="Shared memory name"),
        cleanup: bool = typer.Option(False, "--cleanup", help="Clean up the shared memory"),
        check: bool = typer.Option(False, "--check", help="Only check if shared memory exists")
    ):
        """Check/cleanup shared memory."""
        if cleanup:
            cleanup_shared_memory(name)
        elif check:
            exists = check_shared_memory(name)
            raise typer.Exit(code=0 if exists else 1)
        else:
            # Default: check and offer to cleanup
            logger.info(f"Checking shared memory '{name}'...\n")
            if check_shared_memory(name):
                logger.info("\nThis might be orphaned from a previous run.")
                logger.info("Run with --cleanup to remove it:")
                logger.info(f"  pipenv run python cleanup_shm.py --name {name} --cleanup")
            else:
                logger.info("\nAll clear! No orphaned shared memory found.")
    
    typer.run(main)
