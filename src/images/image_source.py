from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path


class ImageSource(ABC):
    def __init__(self, images_path: Path) -> None:
        """
        All Args Constructor
        :param images_path: Where the Images Should Be Located
        """
        self.images_path = images_path
        self.images_path.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def get_image_from_coordinates(self, latitude: float, longitude: float) -> dict:
        """
        Gets an Image for a Set of Coordinates
        :param latitude: Latitude of the Point to Get an Image for
        :param longitude: Longitude of the Point to Get an Image for
        :return: A Dictionary Containing the Image ID, Path, Latitude, Longitude,
        Residual Distance From Point, and Error if any
        """
        raise NotImplementedError


class ImageSourceSelector(str, Enum):
    local = "LOCAL"
    mapillary = "MAPILLARY"
