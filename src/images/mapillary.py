from pathlib import Path
from typing import Optional

from geopy.distance import ELLIPSOIDS, distance
import numpy as np
import requests
from requests import HTTPError
from stamina import retry
from tenacity import RetryError

from src.images.image_source import ImageSource
from src.utils import log


class Mapillary(ImageSource):
    url = "https://graph.mapillary.com/images"

    def __init__(
        self,
        access_token: str,
        basepath: Path = Path(Path(__file__).parent.parent, "data/raw/mapillary"),
    ) -> None:
        super().__init__(basepath)
        self.access_token = access_token
        self.assigned_images = set()

    @retry(on=HTTPError, attempts=3)
    def get_image_from_coordinates(self, latitude: int, longitude: int) -> dict:
        log.debug("Get Image From Coordinates: %s, %s", latitude, longitude)
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
        log.debug("Successfully Retrieved Image Data: %s", images)
        if len(images) == 0:
            log.debug(
                "No Images in Bounding Box: %s", self._bounds(latitude, longitude)
            )
            return results

        filtered_images = set(
            filter(lambda img: img["id"] not in self.assigned_images, images)
        )
        if len(filtered_images) == 0:
            log.debug("No Unassigned Images Available")
            return results

        closest = 0
        closest_distance = np.inf
        for i, image in enumerate(filtered_images):
            image_coordinates = (
                image["geometry"]["coordinates"][1],
                image["geometry"]["coordinates"][0],
            )
            residual = distance(
                (latitude, longitude), image_coordinates, ellipsoid=ELLIPSOIDS["WGS-84"]
            )
            if residual < closest_distance:
                closest = i
                closest_distance = residual

        image = images[closest]
        log.debug("Closest Image: %s", image["id"])
        results["image_id"] = image["id"]
        results["image_lat"] = image["geometry"]["coordinates"][1]
        results["image_lon"] = image["geometry"]["coordinates"][0]
        results["residual"] = closest_distance.m
        image_url = image["thumb_original_url"]
        try:
            results["image_path"] = self._download_image(image_url, results["image_id"])
        except HTTPError or RetryError as e:
            results["error"] = e.__class__.__name__
        self.assigned_images.add(results["image_id"])

        return results

    def _bounds(self, latitude, longitude) -> str:
        left = longitude - 10 / 111_111
        bottom = latitude - 10 / 111_111
        right = longitude + 10 / 111_111
        top = latitude + 10 / 111_111
        return f"{left},{bottom},{right},{top}"

    @retry(on=HTTPError, attempts=3)
    def _download_image(self, image_url, image_id) -> Optional[Path]:
        log.debug("Downloading Image: %s", image_id)
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        image_content = response.content
        log.debug("Successfully Retrieved Image: %s", image_id)
        image_path = Path(self.basepath, f"{image_id}.jpeg")
        log.debug("Writing Image To: %s", image_path)

        if not image_path.is_file():
            with open(image_path, "wb") as img:
                img.write(image_content)
            log.debug("Successfully Wrote Image: %s", image_path)

        return image_path
