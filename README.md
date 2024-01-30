# street-view-green-view

This project aims to create tools for mapping tree canopy. Inspired by the [Treepedia project](https://github.com/mittrees/Treepedia_Public) from [MIT Senseable City Lab](https://senseable.mit.edu/).

## Usage

### 0. Setup

> [!NOTE]
> This project has a `Makefile` with some convenience commands that came be invoked like `make <command name>`, e.g.. `make requirements`. You can either use them or do things yourself manually.

1. Create a Python virtual environment.
     - You can use the shortcut command `make create_environment`.
2. Install requirements.
    ```bash
    pip install -r requirements.txt
    ```
    - You can use the shortcut command `make requirements`.
3. Put your raw OpenStreetMaps road vector data in `data/raw`.
    - Your raw data should be geospatial vector features of type `LineString`. The features almost must include standard OpenStreetMap keys `osm_id` and `highway`.
    - For example, download [`Three_Rivers_Michigan_USA_line.zip`](https://drive.google.com/file/d/1fpI4I5KP2WyVD5PeytW_hoXZswOt0dwA/view?usp=drive_link) to `data/raw/Three_Rivers_Michigan_USA_line.zip`. Note that this Google Drive link is only accessible to approved project members.

### 1. Sample points from roads data

The first step is to sample points along the roads in your provided data. You can use the [`create_points.py`](./src/create_points.py) script to sample these points and write them out to a new file. This script filters out certain types of highways, and then samples points along each remaining road. By default, the sampling distance is 20 meters.

#### Example

For example, if you're using the `Three_Rivers_Michigan_USA_line.zip` data mentioned in the "Setup" section above:

```bash
python -m src.create_points data/raw/Three_Rivers_Michigan_USA_line.zip data/interim/Three_Rivers_Michigan_USA_points.shz
```

This will write out a zipped shapefile containing the sampled points to `data/interim/Three_Rivers_Michigan_USA_points.shz`.

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
