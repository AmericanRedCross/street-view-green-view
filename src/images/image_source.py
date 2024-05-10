from abc import ABC, abstractmethod
from pathlib import Path


class ImageSource(ABC):
    def __init__(self, basepath: Path) -> None:
        self.basepath = basepath
        self.basepath.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def get_image_from_coordinates(self, latitude: int, longitude: int) -> dict:
        raise NotImplementedError
