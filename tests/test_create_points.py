from pathlib import Path
import shutil

import geopandas as gpd
import numpy as np
import pytest
from shapely import LineString, MultiPoint, geometry
from typer.testing import CliRunner

from src.create_points import (
    DEFAULT_HIGHWAY_VALUES_TO_KEEP,
    DEFAULT_MINI_DIST,
    app,
    create_points,
    filter_by_highway_type,
    interpolate_along_line,
)

runner = CliRunner(mix_stderr=False)


def test_help():
    """Test the CLI with --help flag."""
    result = runner.invoke(app, ["--help"])
    print(result.output)
    assert result.exit_code == 0
    assert (
        "Create a dataset of interpolated points along OpenStreetMap roads."
        in result.output
    )


def test_filter_by_highway_type_error():
    bad_df = gpd.GeoDataFrame(columns=["not_highway"])
    with pytest.raises(Exception):
        filter_by_highway_type(bad_df, [])


def test_filter_by_highway_type():
    highway_vals = np.random.choice(DEFAULT_HIGHWAY_VALUES_TO_KEEP, size=10).tolist()
    drop_highway_vals = ["drop_value_1", "drop_value_2", "drop_value_3"]
    df = gpd.GeoDataFrame({"highway": highway_vals + drop_highway_vals})
    filtered_df = filter_by_highway_type(df)
    assert all(val in DEFAULT_HIGHWAY_VALUES_TO_KEEP for val in filtered_df["highway"])


def test_interpolate_along_line():
    test_line = LineString(np.random.rand(2, 2))
    test_dist = 0.2
    new_coords = interpolate_along_line(test_line, test_dist)
    assert isinstance(new_coords, MultiPoint)
    assert len(new_coords.geoms) == int(test_line.length / test_dist)


@pytest.mark.parametrize("invalid_value", [None, geometry.Point((1, 1))])
def test_create_points_error(invalid_value):
    test_df = gpd.read_file("tests/assets/test_gdf.shp").head()
    test_df.loc[0, "geometry"] = invalid_value
    with pytest.raises(ValueError):
        create_points(test_df, 20)


def test_create_points():
    test_df = gpd.read_file("tests/assets/test_gdf.shp").head()
    output_df = create_points(test_df, 20)
    assert set(output_df.columns) == set(["osm_id", "highway", "geometry"])
    assert (output_df.geom_type == "Point").all()
    assert output_df.crs == "EPSG:4326"


@pytest.mark.parametrize(
    "mini_dist,drop_null,highway_types",
    [
        (DEFAULT_MINI_DIST, False, DEFAULT_HIGHWAY_VALUES_TO_KEEP),
        (DEFAULT_MINI_DIST, True, DEFAULT_HIGHWAY_VALUES_TO_KEEP),
        (DEFAULT_MINI_DIST, False, DEFAULT_HIGHWAY_VALUES_TO_KEEP[:2]),
    ],
)
def test_main(mini_dist, drop_null, highway_types):
    Path("tests/tmp").mkdir(exist_ok=True)
    in_filepath = "tests/assets/test_gdf.shp"
    out_filepath = "tests/tmp/test_gdf_out.shp"

    args = [
        in_filepath,
        out_filepath,
        "--mini-dist",
        mini_dist,
        "--highway-type",
        highway_types,
    ]

    if drop_null:
        args.append("--drop-null")

    runner.invoke(app, args)
    output_gdf = gpd.read_file(out_filepath)

    assert output_gdf.crs == "EPSG:4326"
    assert all(val in highway_types for val in output_gdf["highway"])
    if drop_null:
        assert not output_gdf.geometry.isnull().values.any()
    shutil.rmtree("tests/tmp")
