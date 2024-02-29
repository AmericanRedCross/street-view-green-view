import json
import logging
from multiprocessing import Pool
from pathlib import Path
from typing import Annotated, Optional

from requests import RequestException, Session
from requests.adapters import HTTPAdapter
from shapely import Point
from typer import Argument, Option, Typer

from src.data_parsing.geopandas import GeoPandasParser

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())
app = Typer()


class Mapillary:
    url = "https://graph.mapillary.com/images"

    def __init__(
        self,
        access_token,
        basepath=Path(Path(__file__).parent.parent, "data/raw/mapillary"),
    ):
        self.access_token = access_token
        self.basepath = basepath
        self.basepath.mkdir(parents=True, exist_ok=True)
        self.client = Session()
        self.client.mount("https://", HTTPAdapter(max_retries=3))

    def get_image_from_coordinates(self, point: Point) -> dict:
        longitude, latitude = point.x, point.y
        log.info("Get Image From Coordinates: %s, %s", latitude, longitude)
        try:
            response = self.client.get(
                self.url,
                params={
                    "access_token": self.access_token,
                    "fields": "id,thumb_original_url",
                    "is_pano": "true",
                    "bbox": self._bounds(latitude, longitude),
                },
            )
            response.raise_for_status()
        except RequestException as e:
            log.error(e)
            return {
                "latitude": latitude,
                "longitude": longitude,
                "image_id": None,
                "image_path": None,
            }

        images = response.json()["data"]
        log.debug("Successfully Retrieved Image Data: %s", images)
        if len(images) == 0:
            log.debug(
                "No Images in Bounding Box: %s", self._bounds(latitude, longitude)
            )
            return {
                "latitude": latitude,
                "longitude": longitude,
                "image_id": None,
                "image_path": None,
            }

        image_id = images[0]["id"]
        image_url = images[0]["thumb_original_url"]
        image_path = self._download_image(image_url, image_id)

        return {
            "latitude": latitude,
            "longitude": longitude,
            "image_id": image_id,
            "image_path": str(image_path),
        }

    def _bounds(self, latitude, longitude) -> str:
        left = longitude - 10 / 111_111
        bottom = latitude - 10 / 111_111
        right = longitude + 10 / 111_111
        top = latitude + 10 / 111_111
        return f"{left},{bottom},{right},{top}"

    def _download_image(self, image_url, image_id) -> Optional[Path]:
        log.info("Downloading Image: %s", image_id)
        try:
            response = self.client.get(image_url, stream=True)
            response.raise_for_status()
        except RequestException as e:
            log.error(e)
            return None
        image_content = response.content
        log.debug("Successfully Retrieved Image: %s", image_id)
        image_path = Path(self.basepath, f"{image_id}.jpeg")
        log.debug("Writing Image To: %s", image_path)

        if not image_path.is_file():
            with open(image_path, "wb") as img:
                img.write(image_content)
            log.debug("Successfully Wrote Image: %s", image_path)

        return image_path


@app.command()
def main(
    client_token: Annotated[
        str,
        Argument(help="Mapillary Client Token from Developer Portal"),
    ],
    points_file: Annotated[
        Path,
        Argument(help=("Path to Input Points File")),
    ],
    image_path: Annotated[
        Path,
        Argument(help="Folder to Write Image Data"),
    ] = Path(Path(__file__).parent.parent, "data/raw/mapillary"),
    verbose: Annotated[bool, Option] = False,
):
    if verbose:
        log.setLevel(logging.DEBUG)

    if points_file.suffix == ".gpkg":
        parser = GeoPandasParser(points_file)
    else:
        raise ValueError(f"Unsupported File Extension: {points_file.suffix}")

    mapillary = Mapillary(client_token, image_path)
    coordinates = parser.get_coordinates()

    with Pool() as pool:
        image_data = list(pool.map(mapillary.get_image_from_coordinates, coordinates))
    log.debug(image_data)

    with open(Path(image_path, "image_data.json"), "w") as f:
        json.dump(image_data, f)


if __name__ == "__main__":
    app()
