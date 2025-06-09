"""Dependency injection configuration and application composition root."""

from typing import Protocol, Dict, Any
import logging

from .core.config.settings import app_config
from .core.startup import ApplicationBootstrap, initialize_application
from .domain.repositories.camera_repository import ICameraRepository
from .infrastructure.repositories.camera_repository_impl import InMemoryICameraRepository
from .domain.usecases.camera_management import CameraManagementUseCase
from .domain.usecases.camera_status import CameraStatusUseCase
from .domain.usecases.broadcast_motion_event import BroadcastMotionEventUseCase
from .application.gateways.websocket_gateway import WebSocketGateway
from .application.controllers.camera_controller import CameraController


class ServiceContainer:
    """Simple dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._logger = logging.getLogger(__name__)
    
    def register(self, service_type: type, instance: Any) -> None:
        """Register a service instance."""
        self._services[service_type.__name__] = instance
        self._logger.debug(f"Registered service: {service_type.__name__}")
    
    def get(self, service_type: type) -> Any:
        """Get a service instance."""
        service_name = service_type.__name__
        if service_name not in self._services:
            raise ValueError(f"Service {service_name} not registered")
        return self._services[service_name]
    
    def has(self, service_type: type) -> bool:
        """Check if service is registered."""
        return service_type.__name__ in self._services


class ApplicationContainer:
    """Main application composition root - wires dependencies together."""
    
    def __init__(self):
        self.container = ServiceContainer()
        self.bootstrap: ApplicationBootstrap = None
        self._initialized = False
    
    def initialize(self, websocket_server=None) -> None:
        """Initialize all dependencies."""
        if self._initialized:
            return
        
        # Initialize core bootstrap
        self.bootstrap = initialize_application()
        
        # Register core services
        self.container.register(ApplicationBootstrap, self.bootstrap)
        
        # Register infrastructure services
        camera_repository = InMemoryICameraRepository(websocket_server)
        self.container.register(ICameraRepository, camera_repository)
        
        # Register use cases
        camera_mgmt_usecase = CameraManagementUseCase(camera_repository)
        camera_status_usecase = CameraStatusUseCase(camera_repository)
        broadcast_usecase = BroadcastMotionEventUseCase(camera_repository)
        
        self.container.register(CameraManagementUseCase, camera_mgmt_usecase)
        self.container.register(CameraStatusUseCase, camera_status_usecase)
        self.container.register(BroadcastMotionEventUseCase, broadcast_usecase)
        
        # Register application services
        websocket_gateway = WebSocketGateway(broadcast_usecase)
        self.container.register(WebSocketGateway, websocket_gateway)
        
        # Register camera controller class factory
        def camera_controller_factory(request, client_address, server):
            return CameraController(request, client_address, server, 
                                  camera_mgmt_usecase, camera_status_usecase)
        self.container.register('CameraControllerFactory', camera_controller_factory)
        
        self._initialized = True
        
        logger = self.bootstrap.get_dependency('logger')
        logger.info("Application container initialized successfully")
    
    def get_camera_repository(self) -> ICameraRepository:
        """Get camera repository instance."""
        return self.container.get(ICameraRepository)
    
    def get_camera_management_usecase(self) -> CameraManagementUseCase:
        """Get camera management use case."""
        return self.container.get(CameraManagementUseCase)
    
    def get_camera_status_usecase(self) -> CameraStatusUseCase:
        """Get camera status use case."""
        return self.container.get(CameraStatusUseCase)
    
    def get_broadcast_usecase(self) -> BroadcastMotionEventUseCase:
        """Get broadcast motion event use case."""
        return self.container.get(BroadcastMotionEventUseCase)
    
    def get_websocket_gateway(self) -> WebSocketGateway:
        """Get WebSocket gateway instance."""
        return self.container.get(WebSocketGateway)
    
    def get_camera_controller_class(self):
        """Get camera controller class factory."""
        return self.container.get('CameraControllerFactory')
    
    def shutdown(self) -> None:
        """Clean shutdown of all services."""
        if self.bootstrap:
            self.bootstrap.shutdown()


# Global container instance
_container: ApplicationContainer = None


def get_container() -> ApplicationContainer:
    """Get the global application container."""
    global _container
    if _container is None:
        _container = ApplicationContainer()
    return _container


def initialize_container(websocket_server=None) -> ApplicationContainer:
    """Initialize and return the application container."""
    container = get_container()
    container.initialize(websocket_server)
    return container
