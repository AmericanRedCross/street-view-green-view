from typer.testing import CliRunner

from src.assign_gvi_to_points import app, get_gvi_score, main as run_assign_gvi

runner = CliRunner(mix_stderr=False)


def test_help():
    """Test the CLI with --help flag."""
    result = runner.invoke(app, ["--help"])
    print(result.output)
    assert result.exit_code == 0
    assert (
        "Calculate Green View Index (GVI) scores for a dataset of street-level images."
        in result.output
    )


# ------------------------------------------------------
# Below: additional functional tests for GVI scoring
# ------------------------------------------------------
import re
from pathlib import Path

import pytest
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
import cv2


@pytest.fixture
def tmp_images_dir(tmp_path: Path):
    """Make a temp folder with a few tiny .jpeg images."""
    d = tmp_path / "images"
    d.mkdir()

    def make_img(path: Path, g: int, r: int = 0, b: int = 0):
        # OpenCV uses BGR channel order
        img = np.zeros((16, 16, 3), dtype=np.uint8)
        img[:, :] = (b, g, r)
        cv2.imwrite(str(path), img)

    make_img(d / "img1.jpeg", g=255, r=0, b=0)        # very green
    make_img(d / "img2.jpeg", g=120, r=120, b=120)    # gray-ish
    make_img(d / "img3.jpeg", g=10, r=200, b=200)     # low green

    return d


@pytest.fixture
def interim_points(tmp_path: Path):
    """Make a fake GeoPackage with point geometries that match our test image IDs."""
    df = pd.DataFrame({"image_id": ["img1", "img2", "img3"]})
    geom = [Point(-77.0365, 38.8977), Point(-77.02, 38.9), Point(-77.01, 38.91)]
    gdf = gpd.GeoDataFrame(df, geometry=geom, crs="EPSG:4326")

    path = tmp_path / "points.gpkg"
    gdf.to_file(path)
    return path


def test_get_gvi_score_formatting(tmp_images_dir: Path):
    """Ensure GVI scores are floats with 6 decimals and no scientific notation."""
    score = get_gvi_score(str(tmp_images_dir / "img1.jpeg"))
    assert isinstance(score, float)
    s = f"{score:.6f}"
    assert "e" not in s.lower()
    assert re.fullmatch(r"-?\d+\.\d{6}", s)


def test_main_joins_scores(tmp_images_dir: Path, interim_points: Path, tmp_path: Path):
    """Run main() and confirm output contains correct join and formatting."""
    out = tmp_path / "out.gpkg"
    run_assign_gvi(tmp_images_dir, interim_points, out)
    result = gpd.read_file(out)

    # Columns created by your code
    assert "gvi_score" in result.columns
    assert result.crs.to_epsg() == 4326
    assert len(result) == 3

    # All scores are numeric & 6-decimal rounded (string check)
    s = result["gvi_score"].astype(float).map(lambda x: f"{x:.6f}")
    assert not s.str.contains("e").any()
    assert s.str.match(r"-?\d+\.\d{6}$").all()


def test_main_raises_if_no_jpegs(tmp_path: Path, interim_points: Path):
    """Should raise if image folder lacks .jpeg files."""
    bad_dir = tmp_path / "empty_images"
    bad_dir.mkdir()
    with pytest.raises(Exception):
        run_assign_gvi(bad_dir, interim_points, tmp_path / "out.gpkg")


def test_main_raises_if_not_points(tmp_path: Path, tmp_images_dir: Path):
    """Should raise if interim data is not Point geometry."""
    poly = Polygon([(-77.04, 38.89), (-77.03, 38.89), (-77.03, 38.90), (-77.04, 38.90)])
    gdf = gpd.GeoDataFrame(pd.DataFrame({"image_id": ["img1"]}),
                           geometry=[poly], crs="EPSG:4326")
    bad_path = tmp_path / "not_points.gpkg"
    gdf.to_file(bad_path)

    with pytest.raises(Exception):
        run_assign_gvi(tmp_images_dir, bad_path, tmp_path / "out.gpkg")