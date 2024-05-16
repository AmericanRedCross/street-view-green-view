"""Create webmap of GVI results"""

import typer
import os
from pathlib import Path
import geopandas as gpd
from shapely.geometry import box
import json
from jinja2 import Environment, FileSystemLoader

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
	input_hex

	output_html

	maptiler_apikey

	zoom_level
	): 
