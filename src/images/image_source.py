from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path


class ImageSource(ABC):
    """
    Image Source Interface
    """

    def __init__(self, images_path: Path, max_distance: float) -> None:
        """
        All Args Constructor
        Args:
            images_path: Where the images should be located
            max_distance: Maximum distance between point and image location, in meters
        """
        self.images_path = images_path
        self.images_path.mkdir(parents=True, exist_ok=True)
        self.max_distance = max_distance

    @abstractmethod
    def get_image_from_coordinates(self, latitude: float, longitude: float) -> dict:
        """
        Gets an image for a set of coordinates
        Args:
            latitude: Latitude of the point to get an image for
            longitude: Longitude of the point to get an image for

        Returns: A dict containing the Image ID, Path, Latitude, Longitude,
            Residual Distance From Point, and Error if any

        """
        raise NotImplementedError


class ImageSourceSelector(str, Enum):
    local = "LOCAL"
    mapillary = "MAPILLARY"
