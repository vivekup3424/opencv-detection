# Use case: Stop All Cameras
from domain.repositories.camera_repository import ICameraRepository

class StopAllCamerasUseCase:
    def __init__(self, camera_repository: ICameraRepository):
        self.camera_repository = camera_repository

    def execute(self) -> None:
        self.camera_repository.stop_all_cameras()
