import logging
from os import getenv
from pathlib import Path
from typing import Annotated

import geopandas as gpd
from pandas import Series
from requests.exceptions import HTTPError
from tenacity import RetryError
from tqdm.contrib.concurrent import thread_map
from typer import Argument, Option, Typer

from src.images.local_images import LocalImages
from src.images.mapillary import Mapillary
from src.utils import log

app = Typer()


@app.command()
def main(
    points_file: Annotated[
        Path,
        Argument(help="Path to Input Points File"),
    ],
    image_source: Annotated[str, Argument(help="Where to Get Images From")],
    images_path: Annotated[
        Path,
        Argument(help="Folder to Write Image Data"),
    ] = Path(Path(__file__).parent.parent, "data/raw/mapillary"),
    verbose: Annotated[bool, Option] = False,
):
    if verbose:
        log.setLevel(logging.DEBUG)

    source = None
    if image_source.upper() == "LOCAL":
        source = LocalImages(images_path)
    elif image_source.upper() == "MAPILLARY":
        source = Mapillary(getenv("MAPILLARY_CLIENT_TOKEN"), images_path)
    else:
        raise ValueError(f"Unknown Image Source: {image_source}")

    gdf = gpd.read_file(points_file)
    gdf["image_id"] = Series()
    gdf["image_lat"] = Series()
    gdf["image_lon"] = Series()
    gdf["residual"] = Series()
    gdf["image_path"] = Series()
    gdf["error"] = Series()

    def get_image_for_gdf_row(row: int):
        latitude = gdf.at[row, "geometry"].y
        longitude = gdf.at[row, "geometry"].x

        try:
            results = source.get_image_from_coordinates(latitude, longitude)
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
        get_image_for_gdf_row,
        range(len(gdf)),
        desc=f"Getting {len(gdf)} Images",
        unit="images",
    )
    log.info(gdf.head())

    gdf.to_file(
        Path(points_file.parent, f"{points_file.stem}_images.gpkg"), driver="GPKG"
    )


if __name__ == "__main__":
    app()
