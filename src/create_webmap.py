"""Create webmap of GVI results"""

import os
from pathlib import Path

import geopandas as gpd
from jinja2 import Environment, FileSystemLoader
import matplotlib
from shapely.geometry import box
import numpy as np
import typer

try:
    from typing import Annotated
except ImportError:
    # for Python 3.9
    from typing_extensions import Annotated


app = typer.Typer()


def h3_to_webmap():
    return


@app.command()
def main(
    input_file: Annotated[
        Path,
        typer.Argument(help="Path to file containing h3 polygons."),
    ],
    output_dir: Annotated[
        Path,
        typer.Argument(help="Folder to save output HTML file to."),
    ],
    filename: Annotated[
        str, typer.Argument(help="(Optional) Filename for HTML output file.")
    ] = "gvi_webmap.html",
    zoom_level: Annotated[
        int,
        typer.Argument(
            help="""(Optional) Starting zoom level for webmap. 
			Takes integer between 0 (small scale) and 15 (large scale).
			"""
        ),
    ] = 10,
):
    gdf = gpd.read_file(input_file)
    # if crs is not 4326, convert to 4326
    if gdf.crs == "EPSG:4326":
        pass
    else:
        gdf = gdf.to_crs("EPSG:4326")

    # get central coordinates of all features
    centre = (
        str(gdf.dissolve().centroid.x.values[0])
        + ", "
        + str(gdf.to_crs("4326").dissolve().centroid.y.values[0])
    )
    centre_str = "[" + centre + "]"

    # Calculate datasdet bounds (with a buffer of 0.5 degrees) to limit webmap bounds
    gdf_bounds = gdf.total_bounds
    bbox = box(*gdf_bounds).buffer(0.5, cap_style="square", join_style="mitre")
    bounds = bbox.bounds
    bounds_str = (
        "["
        + str(bounds[0])
        + ","
        + str(bounds[1])
        + "], ["
        + str(bounds[2])
        + ","
        + str(bounds[3])
        + "]"
    )

    # Load API key for map tiles from environment variable
    maptiler_api_key = os.getenv("MAPTILER_API_KEY")

    # Set up colours based on dataset values
    # Create a plot with a legend
    ax = gdf.plot(
        column="gvi_score", scheme="natural_breaks", k=5, cmap="YlGnBu_r", legend=True
    )

    # Convert the legend labels to numeric break points
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    breaks = [float(t.split(',')[0].strip()) for t in labels]
    breaks_norm = list((breaks-np.min(breaks)) / (np.max(breaks)-np.min(breaks)))

    # Lookup the colourmap values for each breakpoint
    cmap = matplotlib.colormaps["viridis"]
    gdf['gvi_norm'] = (gdf.gvi_score-np.min(gdf.gvi_score)) / (np.max(gdf.gvi_score)-np.min(gdf.gvi_score))
    gdf['html_color'] = gdf['gvi_norm'].apply(lambda x: matplotlib.colors.rgb2hex(cmap(x)))

    # Load the MapLibre HMTL template
    environment = Environment(loader=FileSystemLoader("src/templates"))
    template = environment.get_template("maplibre_template.html")

    # Generate the HTML file from the template, filling dynamic values
    with open(
        os.path.join(output_dir, filename), mode="w", encoding="utf-8"
    ) as message:
        message.write(
            template.render(
                title="GVI score hex map",
                geojson=gdf.to_json(),
                centre_coords=centre_str,
                zoom=zoom_level,
                bounds=bounds_str,
                maptiler_api_key=maptiler_api_key,
            )
        )


if __name__ == "__main__":
    app()
