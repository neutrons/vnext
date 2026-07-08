"""Unit tests for vnext.gsas — GSAS file reading / assembly utilities."""

import shutil
from pathlib import Path

import numpy as np
import pytest
from mantid.simpleapi import mtd

from vnext import Config
from vnext.gsas import sequential_view_workspaces

IPTS = 36261


@pytest.fixture
def binned_dir():
    """Create a scratch binned_data directory for GSAS fixtures and clean up."""

    d = Path(Config["instrument.reduction.bin"].format(IPTS=IPTS))
    d.mkdir(parents=True, exist_ok=True)
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# sequential_view_workspaces
# ---------------------------------------------------------------------------


def test_sequential_view_one_workspace_per_bank(binned_dir, place_gda):
    place_gda(1, binned_dir / "200.gda")
    place_gda(2, binned_dir / "201.gda")
    place_gda(3, binned_dir / "202.gda")

    with sequential_view_workspaces(IPTS, 200, 202) as (runs_present, workspaces):
        assert runs_present == [200, 201, 202]
        assert [ws.getTitle() for ws in workspaces] == ["bank 1", "bank 2"]
        for ws in workspaces:
            # one spectrum per run, all sharing the file's x binning
            assert ws.getNumberHistograms() == 3


def test_sequential_view_run_axis_labels(binned_dir, place_gda):
    place_gda(1, binned_dir / "250.gda")
    place_gda(2, binned_dir / "251.gda")

    with sequential_view_workspaces(IPTS, 250, 251) as (_, workspaces):
        axis = workspaces[0].getAxis(1)
        assert [axis.label(i) for i in range(axis.length())] == ["250", "251"]


def test_sequential_view_rows_match_per_run_intensity(binned_dir, place_gda):
    """Each spectrum is the corresponding run's bank intensity."""
    place_gda(1, binned_dir / "300.gda")
    place_gda(2, binned_dir / "301.gda")

    with sequential_view_workspaces(IPTS, 300, 301) as (_, workspaces):
        bank1 = workspaces[0]
        # scale=2 run should be twice the scale=1 run
        np.testing.assert_allclose(bank1.readY(1), 2.0 * bank1.readY(0))


def test_sequential_view_skips_missing_runs(binned_dir, place_gda):
    place_gda(1, binned_dir / "400.gda")  # 401 missing
    place_gda(2, binned_dir / "402.gda")

    with sequential_view_workspaces(IPTS, 400, 402) as (runs_present, workspaces):
        assert runs_present == [400, 402]
        assert workspaces[0].getNumberHistograms() == 2


def test_sequential_view_cleans_up_workspaces(binned_dir, place_gda):
    place_gda(1, binned_dir / "500.gda")
    place_gda(2, binned_dir / "501.gda")

    with sequential_view_workspaces(IPTS, 500, 501) as (_, workspaces):
        names = [ws.name() for ws in workspaces]
        assert all(name in mtd for name in names)
    assert not any(name in mtd for name in names)
    # no leftover intermediate (run / spectrum) workspaces either
    assert not any(name.startswith("__vnextview_seq") for name in mtd.getObjectNames())


@pytest.mark.usefixtures("binned_dir")
def test_sequential_view_no_files_raises():
    with pytest.raises(FileNotFoundError):
        with sequential_view_workspaces(IPTS, 900, 905):
            pass
