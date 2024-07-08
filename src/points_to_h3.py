"""Convert point features to h3 hex grid"""

import os
from pathlib import Path

import geopandas as gpd
import h3pandas
import typer

try:
    from typing import Annotated
except ImportError:
    # for Python 3.9
    from typing_extensions import Annotated

app = typer.Typer()


@app.command()
def main(
    input_file: Annotated[
        Path,
        typer.Argument(help="Path to file containing point layer with GVI scores."),
    ],
    output_file: Annotated[
        Path,
        typer.Argument(
            help="File to write output data to (can specify any GDAL-supported format)"
        ),
    ],
    cell_resolution: Annotated[
        int,
        typer.Argument(
            help="H3 cell resolution to aggregate to, between 0 (largest) and 15 (smallest)"
        ),
    ] = 10,
):
    """
    Aggregates points to h3 hex cells.

    Args:
            input_file: Path to file containing point layer with GVI scores.
            cell_resolution: H3 cell resolution to aggregate to, between 0 (largest) and 15 (smallest)
            aggregation_operations:
            output_file: File to write output data to (can specify any GDAL-supported format)

    Returns:
            File containing h3 polygons with aggregated GVI scores

    """
    # Check input file exists
    if os.path.exists(input_file):
        pass
    else:
        raise ValueError("Input file could not be found")

    # Check input file is a valid file for GeoPandas
    try:
        gpd.read_file(input_file)
    except Exception as e:
        raise e

    # Check data contains point features
    if "Point" in gpd.read_file(input_file).geometry.type.unique():
        pass
    else:
        raise Exception("Expected point data in interim data file but none found")

    # Check data contains numeric gvi_score field

    # Load input data
    gdf = gpd.read_file(input_file)

    # Exclude points with no GVI score
    gdf = gdf[~gdf.gvi_score.isna()]

    # Assign points to h3 cells at the selected resolution
    gdf_h3 = gdf.h3.geo_to_h3(cell_resolution).reset_index()

    # Aggregate the points to the assigned h3 cell
    gvi_mean = gdf_h3.groupby("h3_" + f"{cell_resolution:02}").agg({"gvi_score": "mean"})

    # Convert the h3 cells to polygons
    gvi_hex = gvi_mean.h3.h3_to_geo_boundary()

    # Export the h3 polygons to the specified output file
    gvi_hex.to_file(output_file)


if __name__ == "__main__":
    app()
