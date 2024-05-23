from pathlib import Path
from typing import Optional

from geopy.distance import ELLIPSOIDS, distance
from loguru import logger as log
import requests
from requests import HTTPError
from stamina import retry
from tenacity import RetryError
from typing_extensions import override

from src.images.image_source import ImageSource


class Mapillary(ImageSource):
    """
    Mapillary Image Source
    """

    url = "https://graph.mapillary.com/images"

    def __init__(
        self, access_token: str, images_path: Path, max_distance: float
    ) -> None:
        """
        All Args Constructor
        Args:
            access_token: Mapillary Access Token
            images_path: Where the images should be located
            max_distance: Maximum distance between point and image location, in meters

        """
        super().__init__(images_path, max_distance)
        self.access_token = access_token
        self.assigned_images = set()

    @override
    @retry(on=HTTPError, attempts=3)
    def get_image_from_coordinates(self, latitude: float, longitude: float) -> dict:
        """
        Gets an image for a set of coordinates
        Args:
            latitude: Latitude of the point to get an image for
            longitude: Longitude of the point to get an image for

        Returns: A dict containing the Image ID, Path, Latitude, Longitude,
            Residual Distance From Point, and Error if any

        """
        log.debug("Get Image From Coordinates: {}, {}", latitude, longitude)
        results = {
            "image_lat": None,
            "image_lon": None,
            "residual": None,
            "image_id": None,
            "image_path": None,
            "error": None,
        }

        response = requests.get(
            self.url,
            params={
                "access_token": self.access_token,
                "fields": "id,thumb_original_url,geometry",
                "is_pano": "true",
                "bbox": self._bounds(latitude, longitude),
            },
        )
        response.raise_for_status()

        images = response.json()["data"]
        log.debug("Successfully Retrieved Image Data: {}", images)
        if len(images) == 0:
            log.debug(
                "No Images in Bounding Box: {}", self._bounds(latitude, longitude)
            )
            return results

        filtered_images = filter(
            lambda img: img["id"] not in self.assigned_images, images
        )

        closest = 0
        closest_distance = self.max_distance
        for i, image in enumerate(filtered_images):
            image_coordinates = (
                image["geometry"]["coordinates"][1],
                image["geometry"]["coordinates"][0],
            )
            residual = distance(
                (latitude, longitude), image_coordinates, ellipsoid=ELLIPSOIDS["WGS-84"]
            ).m

            if residual < closest_distance:
                closest = i
                closest_distance = residual

        if closest is None:
            log.debug("No Unassigned Images Available")
            return results

        image = images[closest]
        log.debug("Closest Image: {}", image["id"])
        results["image_id"] = image["id"]
        results["image_lat"] = image["geometry"]["coordinates"][1]
        results["image_lon"] = image["geometry"]["coordinates"][0]
        results["residual"] = closest_distance
        image_url = image["thumb_original_url"]
        try:
            results["image_path"] = self._download_image(
                image_url, results["image_id"]
            ).resolve()
        except HTTPError or RetryError as e:
            results["error"] = e.__class__.__name__
        self.assigned_images.add(results["image_id"])

        return results

    def _bounds(self, latitude: float, longitude: float) -> str:
        """
        Gets Bounding Box to Call Mapillary API to Search for Images
        Args:
            latitude: Latitude of the point to get an image for
            longitude: Longitude of the point to get an image for

        Returns: str representation of the bounding box

        """
        left = longitude - self.max_distance / 111_111
        bottom = latitude - self.max_distance / 111_111
        right = longitude + self.max_distance / 111_111
        top = latitude + self.max_distance / 111_111
        return f"{left},{bottom},{right},{top}"

    @retry(on=HTTPError, attempts=3)
    def _download_image(self, image_url: str, image_id: str) -> Optional[Path]:
        """
        Downloads an Image from a URL to images_path/image_id.jpeg
        Args:
            image_url: The URL of the image
            image_id: The Mapillary ID of the image

        Returns: Path of the downloaded image, or None

        """
        log.debug("Downloading Image: {}", image_id)
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        image_content = response.content
        log.debug("Successfully Retrieved Image: {}", image_id)
        image_path = Path(self.images_path, f"{image_id}.jpeg")
        log.debug("Writing Image To: {}", image_path)

        if not image_path.is_file():
            with open(image_path, "wb") as img:
                img.write(image_content)
            log.debug("Successfully Wrote Image: {}", image_path)

        return image_path
