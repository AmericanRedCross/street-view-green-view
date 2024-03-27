"""Rewrite of createPoints.py from the mittrees/Treepedia_Public project.
See: https://github.com/mittrees/Treepedia_Public/blob/master/Treepedia/createPoints.py
"""

from pathlib import Path

try:
    from typing import Annotated
except ImportError:
    # For Python <3.9
    from typing_extensions import Annotated

import geopandas as gpd
import numpy as np
import shapely
import typer

DEFAULT_MINI_DIST = 20.0  # meters
HIGHWAY_VALUES = {
    None,
    " ",
    "bridleway",
    "footway",
    "motorway",
    "motorway_link",
    "pedestrian",
    "primary",
    "primary_link",
    "secondary",
    "secondary_link",
    "service",
    "steps",
    "tertiary",
    "tertiary_link",
    "trunk",
    "trunk_link",
}

app = typer.Typer()


def remove_highways(gdf: gpd.GeoDataFrame):
    """Returns a copy of a GeoDataFrame of OpenStreetMap road features with highways
    removed.

    Args:
        gdf (geopandas.GeoDataFrame): OpenStreetMap features.

    Returns:
        geopandas.GeoDataFrame: Copy of input GeoDataFrame with highway features
            removed.
    """
    if "highway" not in gdf.columns:
        raise ValueError(
            "'highway' column not found in input GeoDataFrame. "
            "Input data must be of OpenStreetMap roads."
        )
    out_gdf = gdf[~gdf["highway"].isin(HIGHWAY_VALUES)].copy()
    return out_gdf


def interpolate_along_line(
    line: shapely.LineString, mini_dist: float
) -> shapely.MultiPoint:
    """Given a LineString, returns a MultiPoint feature with interpolated points with
    distaince `mini_dist` between each point, excluding the endpoint.

    Args:
        line (shapely.LineString): input line
        mini_dist (float): distance in meters between interpolated points

    Returns:
        shapely.MultiPoint: new MultiPoint feature containing interpolated points
    """
    new_coords = [
        line.interpolate(dist)
        for dist in np.linspace(
            0.0, line.length, num=int(line.length / mini_dist), endpoint=False
        )
    ]
    return shapely.MultiPoint(new_coords)


def create_points(gdf: gpd.GeoDataFrame, mini_dist: float = DEFAULT_MINI_DIST):
    """Given a GeoDataFrame of OpenStreetMap data with LineString features, returns an
    exploded GeodataFrame of Point features interpolated along the lines with distance
    `mini_dist` in meters.

    Args:
        gdf (geopandas.GeoDataFrame): input GeoDataFrame of LineString features
        mini_dist (float): distance in meters between interpolated points

    Returns:
        geopandas.GeoDataFrame: new linestrings with interpolated points
    """
    if (gdf.geometry.isna()).any():
        raise ValueError(
            "Input GeoDataFrame contains null geometries. "
            "Rerun with --drop-null to exclude these features."
        )
    if not (gdf.geom_type == "LineString").all():
        raise ValueError("Input GeoDataFrame must contain only LineString features.")
    # Drop metadata other than 'osm_id'
    gdf = gdf[["osm_id", "highway", "geometry"]]
    # EPSG:3857 is pseudo WGS84 with unit in meters
    gdf = gdf.to_crs("EPSG:3857")
    # Interpolate along lines and explode
    gdf["geometry"] = gdf["geometry"].apply(interpolate_along_line, args=(mini_dist,))
    gdf = gdf.explode(ignore_index=True, index_parts=False)
    # Convert output to WGS84
    gdf.to_crs("EPSG:4326", inplace=True)
    return gdf


@app.command()
def main(
    in_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Path to input OpenStreetMap roads data file. Must be a geospatial "
                "vector format readable by geopandas."
            )
        ),
    ],
    out_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Path to write interpolated points data. The file extension should "
                "correspond to a geospatial vector format writable by geopandas."
            )
        ),
    ],
    mini_dist: Annotated[
        float, typer.Option(help="Distance in meters between interpolated points.")
    ] = DEFAULT_MINI_DIST,
    drop_null: Annotated[
        bool,
        typer.Option(
            "--drop-null",
            help="Set whether features with null geometries should be removed",
        ),
    ] = False,
):
    gdf = gpd.read_file(in_file)
    gdf = remove_highways(gdf)
    if drop_null:
        gdf = gdf[~gdf.geometry.isna()]
    else:
        pass
    gdf = create_points(gdf, mini_dist=mini_dist)
    gdf.to_file(out_file)


if __name__ == "__main__":
    app()
