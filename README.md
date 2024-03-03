# street-view-green-view

## Project description

### Goal

We want to automate mapping of tree canopy cover from street level imagery (SLI) to create an informative layer for exploring which areas of a city might be at greater risk during future heat waves and for engaging people in discussions about green and nature-based solutions for climate adaptation. 

### Project inspiration

This project was inspired by the [Treepedia project](https://github.com/mittrees/Treepedia_Public) from [MIT Senseable City Lab](https://senseable.mit.edu/). Treepedia aimed to raise a proactive awareness of urban vegetation improvement, using computer vision techniques applied to Google Street View images. Treepedia measured and mapped the amount of vegetation cover along a city's streets by computing the Green View Index (GVI) on Google Street View (GSV) panoramas. The method considered the obstruction of tree canopies and classified the images accordingly.

We plan to use crowd-sourced, open available imagery uploaded to [Mapillary](https://www.mapillary.com/) instead of GSV panoramas. This will give us greater control over the recency of the images and the geographic coverage of the images, as well as lowering costs. 

Our first workflow will mirror Treepedia's GVI; however, we will explore additional analysis methods including machine learning options that have been developed since 2017 when Treepedia was released.

### Why street level imagery (SLI)?

Satellite imagery is a well-known source of data, but launching a satellite is a costly endeavor and there are limits to what we can interpret from it. SLI provides an accessible way to gather images from a different perspective with exciting implications for humanitarians. 
- Effective hardware for SLI is no longer limited to vehicle-top rigs costing tens of thousands of dollars like those used by Google for their Street View service. There are a variety of options for high quality digital action cameras at a reasonable price that are durable, rugged, can capture at a frequent interval, and can automatically tag images with GPS coordinates. 
- There are more powerful computing resources, better data storage and transfer options, and innovations in algorithms and machine learning tools are making it easier and more accessible to quickly collect data, process large amounts of data, and automate extraction of insights. 
- There is a growing ecosystem of open tools and open data for SLI that organizations can use, build on, and contribute to.

### Contributing

This project is a collaboration with [Civic Tech DC](https://civictechdc.org/).

If you are interested in joining the project, please check out [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Usage

### 0. Setup

> [!NOTE]
> This project has a `Makefile` with some convenience commands that came be invoked like `make <command name>`, e.g.. `make requirements`. You can either use them or do things yourself manually.

1. Create a Python virtual environment.
     - You can use the shortcut command `make create_environment`.
     - The log will tell you how to activate the environment. Do so with: `source .venv/bin/activate`
2. Install requirements.
    ```bash
    pip install -r requirements.txt
    ```
    - You can use the shortcut command `make requirements` to do the same thing.
3. Put your raw OpenStreetMaps road vector data in `data/raw`.
    - Your raw data should be geospatial vector features of type `LineString`. The features must include standard OpenStreetMap keys `osm_id` and `highway`.
    - For example, download [`Three_Rivers_Michigan_USA_line.zip`](https://drive.google.com/file/d/1fpI4I5KP2WyVD5PeytW_hoXZswOt0dwA/view?usp=drive_link) to `data/raw/Three_Rivers_Michigan_USA_line.zip`. Note that this Google Drive link is only accessible to approved project members.

### 1. Sample points from roads data

The first step is to sample points along the roads in your provided data. You can use the [`create_points.py`](./src/create_points.py) script to sample these points and write them out to a new file. This script filters out certain types of highways, and then samples points along each remaining road. By default, the sampling distance is 20 meters.

#### Example

For example, if you're using the `Three_Rivers_Michigan_USA_line.zip` data mentioned in the "Setup" section above:

```bash
python -m src.create_points data/raw/Three_Rivers_Michigan_USA_line.zip data/interim/Three_Rivers_Michigan_USA_points.gpkg
```

This will write out a zipped shapefile containing the sampled points to `data/interim/Three_Rivers_Michigan_USA_points.gpkg`. The input and output formats can be any vector-based spatial data format [supported by geopandas](https://geopandas.org/en/stable/docs/user_guide/io.html), such as shapefiles, GeoJSON, and GeoPackage. The output format is automatically inferred from the file extension.

#### Advanced usage

For additional documentation on how to use `create_points.py`, you can run:

```bash
python -m src.create_points --help
```

Both the input files and output files support any file formats that geopandas supports, so long as it can correctly infer the format from the file extension. See the [geopandas documentation](https://geopandas.org/en/stable/docs/user_guide/io.html) for more details.

## Project Organization

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    └── src                <- Source code for use in this project.
        └── __init__.py    <- Makes src a Python module

--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
