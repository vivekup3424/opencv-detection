"""Application startup and dependency injection bootstrap."""

from typing import Dict, Any
import logging
import sys
from pathlib import Path

from src.core.config.settings import ApplicationSettings, get_settings
from src.core.constants.enums import LogLevel
from src.core.errors.exceptions import ApplicationStartupError


class ApplicationBootstrap:
    """Handles application initialization and dependency injection setup."""
    
    def __init__(self):
        self.settings: ApplicationSettings = get_settings()
        self.dependencies: Dict[str, Any] = {}
        self._logger = None
    
    def initialize(self) -> None:
        """Initialize the application with all required dependencies."""
        try:
            self._setup_logging()
            self._validate_environment()
            self._register_dependencies()
            self._logger.info("Application bootstrap completed successfully")
        except Exception as e:
            raise ApplicationStartupError(f"Failed to initialize application: {e}") from e
    
    def _setup_logging(self) -> None:
        """Configure application logging."""
        log_level = getattr(logging, self.settings.log_level.upper())
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(self.settings.log_file) if self.settings.log_file else logging.NullHandler()
            ]
        )
        
        self._logger = logging.getLogger(__name__)
        self._logger.info(f"Logging configured with level: {self.settings.log_level}")
    
    def _validate_environment(self) -> None:
        """Validate that the environment is properly configured."""
        # Create necessary directories
        if self.settings.log_file:
            log_dir = Path(self.settings.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate camera settings
        if self.settings.camera.default_width <= 0 or self.settings.camera.default_height <= 0:
            raise ApplicationStartupError("Invalid camera dimensions in configuration")
        
        if self.settings.camera.default_fps <= 0:
            raise ApplicationStartupError("Invalid camera FPS in configuration")
        
        self._logger.info("Environment validation passed")
    
    def _register_dependencies(self) -> None:
        """Register all application dependencies."""
        # This will be expanded when we create infrastructure layer
        self.dependencies.update({
            'settings': self.settings,
            'logger': self._logger,
        })
        
        self._logger.info(f"Registered {len(self.dependencies)} dependencies")
    
    def get_dependency(self, name: str) -> Any:
        """Retrieve a registered dependency by name."""
        if name not in self.dependencies:
            raise ApplicationStartupError(f"Dependency '{name}' not found")
        return self.dependencies[name]
    
    def shutdown(self) -> None:
        """Clean shutdown of application resources."""
        if self._logger:
            self._logger.info("Application shutdown initiated")
        
        # Cleanup will be expanded when we have more resources to manage
        self.dependencies.clear()


# Global bootstrap instance
_bootstrap_instance = None


def get_bootstrap() -> ApplicationBootstrap:
    """Get the global bootstrap instance."""
    global _bootstrap_instance
    if _bootstrap_instance is None:
        _bootstrap_instance = ApplicationBootstrap()
    return _bootstrap_instance


def initialize_application() -> ApplicationBootstrap:
    """Initialize and return the application bootstrap."""
    bootstrap = get_bootstrap()
    bootstrap.initialize()
    return bootstrap
