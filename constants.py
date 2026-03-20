"""
Central configuration and constants for ImageBundle system.
"""

# Shared Memory Configuration
DEFAULT_SHM_NAME = "bundle_shm"
DEFAULT_SHM_SIZE = 100_000_000  # 100 MB

# Sender Configuration
DEFAULT_SENDER_FPS = 2
DEFAULT_TEST_BUNDLE_COUNT = 3
DEFAULT_TEST_IMAGE_SIZE = (150, 150)

# Visualizer Configuration
DEFAULT_VISUALIZER_FPS = 10
DEFAULT_MAX_BUNDLES_PER_PAGE = 15
DEFAULT_WAIT_TIMEOUT = 30.0  # seconds

# Supported Image Formats
SUPPORTED_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')

# Status Messages
STATUS_OK = "[OK]"
STATUS_ERROR = "[ERROR]"
STATUS_WARNING = "[WARNING]"
