import logging
from os import getenv
from pathlib import Path
from typing import Annotated, Optional

import geopandas as gpd
from geopy.distance import ELLIPSOIDS, distance
import numpy as np
from pandas import Series
import requests
from requests.exceptions import HTTPError
from stamina import retry
from tenacity import RetryError
from tqdm.contrib.concurrent import thread_map
from typer import Argument, Option, Typer

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
        self.downloaded_images = set()

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

        closest = 0
        closest_distance = np.inf

        for i, image in enumerate(
            filter(lambda img: img["id"] not in self.downloaded_images, images)
        ):
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
        self.downloaded_images.add(results["image_id"])

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


@app.command()
def main(
    points_file: Annotated[
        Path,
        Argument(help="Path to Input Points File"),
    ],
    images_path: Annotated[
        Path,
        Argument(help="Folder to Write Image Data"),
    ] = Path(Path(__file__).parent.parent, "data/raw/mapillary"),
    verbose: Annotated[bool, Option] = False,
):
    if verbose:
        log.setLevel(logging.DEBUG)

    mapillary = Mapillary(getenv("MAPILLARY_CLIENT_TOKEN"), images_path)
    gdf = gpd.read_file(points_file)
    gdf["image_id"] = Series()
    gdf["image_lat"] = Series()
    gdf["image_lon"] = Series()
    gdf["residual"] = Series()
    gdf["image_path"] = Series()
    gdf["error"] = Series()

    def download_image_for_gdf_row(row: int):
        latitude = gdf.at[row, "geometry"].y
        longitude = gdf.at[row, "geometry"].x
        try:
            results = mapillary.get_image_from_coordinates(latitude, longitude)
            gdf.at[row, "image_lat"] = results["image_lat"]
            gdf.at[row, "image_lon"] = results["image_lon"]
            gdf.at[row, "residual"] = results["residual"]
            gdf.at[row, "image_id"] = results["image_id"]
            gdf.at[row, "image_path"] = str(results["image_path"])
            gdf.at[row, "error"] = results["error"]
        except HTTPError or RetryError as e:
            log.error(e)
            gdf.at[row, "error"] = e.__class__.__name__

    thread_map(
        download_image_for_gdf_row,
        range(len(gdf)),
        desc=f"Downloading {len(gdf)} Images",
        unit="images",
    )
    log.info(gdf.head())

    gdf.to_file(
        Path(points_file.parent, f"{points_file.stem}_images.gpkg"), driver="GPKG"
    )


if __name__ == "__main__":
    app()
