"""Unit tests for vnext.gsas — GSAS file reading / assembly utilities."""

import shutil
from pathlib import Path

import numpy as np
import pytest

from vnext import Config
from vnext.gsas import build_sequential_view, read_gsas_banks

IPTS = 36261


@pytest.fixture
def binned_dir():
    """Create a scratch binned_data directory for GSAS fixtures and clean up."""

    d = Path(Config["instrument.reduction.bin"].format(IPTS=IPTS))
    d.mkdir(parents=True, exist_ok=True)
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# read_gsas_banks
# ---------------------------------------------------------------------------


def test_read_gsas_banks_returns_two_banks(binned_dir, place_gda):
    gda = place_gda(1, binned_dir / "100.gda")
    banks = read_gsas_banks(gda)

    assert [b["bank"] for b in banks] == [1, 2]


def test_read_gsas_banks_x_centres_align_with_y(binned_dir, place_gda):
    """GSAS files store bin edges; the reader returns centres so x and y align."""
    gda = place_gda(1, binned_dir / "101.gda")
    banks = read_gsas_banks(gda)

    for bank in banks:
        assert len(bank["x"]) == len(bank["y"])
        assert isinstance(bank["x"], np.ndarray)
        assert isinstance(bank["y"], np.ndarray)


def test_read_gsas_banks_scale_reflected_in_intensity(binned_dir, place_gda):
    """The scale=2 fixture has exactly twice the scale=1 intensities."""
    one = read_gsas_banks(place_gda(1, binned_dir / "102.gda"))
    two = read_gsas_banks(place_gda(2, binned_dir / "103.gda"))

    np.testing.assert_allclose(two[0]["y"], 2.0 * one[0]["y"])


# ---------------------------------------------------------------------------
# build_sequential_view
# ---------------------------------------------------------------------------


def test_build_sequential_view_grid_shape(binned_dir, place_gda):
    place_gda(1, binned_dir / "200.gda")
    place_gda(2, binned_dir / "201.gda")
    place_gda(3, binned_dir / "202.gda")

    result = build_sequential_view(IPTS, 200, 202)

    assert result["ipts"] == IPTS
    assert result["runs_present"] == [200, 201, 202]
    assert [b["bank"] for b in result["banks"]] == [1, 2]
    bank = result["banks"][0]
    # intensity grid is (n_runs x n_xbins) and shares the bank x axis
    assert bank["intensity"].shape == (3, len(bank["x"]))


def test_build_sequential_view_rows_match_per_run_intensity(binned_dir, place_gda):
    """Each grid row is the corresponding run's bank-1 intensity."""
    place_gda(1, binned_dir / "300.gda")
    place_gda(2, binned_dir / "301.gda")

    result = build_sequential_view(IPTS, 300, 301)
    grid = result["banks"][0]["intensity"]
    # scale=2 row should be twice the scale=1 row
    np.testing.assert_allclose(grid[1], 2.0 * grid[0])


def test_build_sequential_view_skips_missing_runs(binned_dir, place_gda):
    place_gda(1, binned_dir / "400.gda")  # 401 missing
    place_gda(2, binned_dir / "402.gda")

    result = build_sequential_view(IPTS, 400, 402)

    assert result["runs_present"] == [400, 402]
    assert result["banks"][0]["intensity"].shape[0] == 2


@pytest.mark.usefixtures("binned_dir")
def test_build_sequential_view_no_files_raises():
    with pytest.raises(FileNotFoundError):
        build_sequential_view(IPTS, 900, 905)
