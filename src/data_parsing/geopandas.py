import logging
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


class GeoPandasParser:
    def __init__(self, gpkg_path: Path):
        self.gdf = gpd.read_file(gpkg_path)
        log.debug(self.gdf)

    def get_coordinates(self) -> list[Point]:
        log.info("Get Coordinates")
        points = self.gdf["geometry"]
        log.debug(points)

        return list(points)
