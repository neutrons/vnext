import datetime
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vnext.backend import Backend

TESTS_DIR = Path(__file__).parent
IPTS = 36261
RUN = 260112
# A run whose NeXus fixture carries real proton-charge pulses
LOG_RUN = 218075


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def output_dir():
    """Yield the directory vnextbin will write .gda files to."""
    from vnext import Config

    d = Path(Config["instrument.reduction.bin"].format(IPTS=IPTS))
    d.mkdir(parents=True, exist_ok=True)
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def mantid_mocks():
    """Patch the three Mantid calls inside vnextbin and yield the mock pair."""
    mock_mtd = MagicMock()
    mock_mtd.__contains__ = lambda *_: False

    with (
        patch("vnext.reduction.AlignAndFocusPowderSlim") as mock_align,
        patch("vnext.gsas.SaveGSS") as mock_save,
        patch("vnext.reduction.DeleteWorkspace"),
        patch("vnext.reduction.mtd", mock_mtd),
    ):
        yield mock_align, mock_save


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_vnextbin_chopruns_raises():
    with pytest.raises(NotImplementedError) as excinfo:
        Backend().vnextbin(ipts=IPTS, runs=1, chopruns=1)
    assert excinfo.value.args[0] == "Binning of pre-chopped data is not yet implemented"


def test_vnextbin_no_runs_raises():
    with pytest.raises(ValueError) as excinfo:
        Backend().vnextbin(ipts=IPTS, runs=2, rune=4)  # runs 2-4 do not exist
    assert excinfo.value.args[0] == f"No valid runs found for IPTS {IPTS} in range 2-4"


@pytest.mark.usefixtures("mantid_mocks")
def test_vnextbin_missing_run_returns_dir(output_dir):
    """
    When a run in the range does not have a NeXus file,
    vnextbin silently skips it.
    An error is only raised if no valid files are found in the range.
    """
    result = Backend().vnextbin(ipts=IPTS, runs=RUN, rune=RUN + 4)  # RUN+1 through RUN+4 do not exist
    assert "output" in result
    # check against single-run name, which is the exact file path (not dir)
    assert Path(result["output"]) == output_dir / f"{RUN}.gda"


@pytest.mark.usefixtures("mantid_mocks")
def test_vnextbin_no_tof_raises():
    """
    If the run's NeXus file has no valid acquisition date, vnextbin raises an error.
    """
    steam_age = datetime.datetime(1800, 1, 1, 1)
    with patch("vnext.reduction.extract_nexus_metadata", return_value=(steam_age, 0.0, 0.0)):
        with pytest.raises(ValueError) as excinfo:
            Backend().vnextbin(ipts=IPTS, runs=RUN)
        assert f"Acquisition date {steam_age} is out of range" in excinfo.value.args[0]


# ---------------------------------------------------------------------------
# Success path — verify Mantid algorithms are called correctly
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("output_dir")
def test_vnextbin_calls_align_and_focus(mantid_mocks):
    mock_align, _ = mantid_mocks

    Backend().vnextbin(ipts=IPTS, runs=RUN)

    mock_align.assert_called_once()
    kwargs = mock_align.call_args.kwargs
    assert str(RUN) in kwargs["Filename"]
    assert kwargs["BinningUnits"] == "TOF"
    assert kwargs["OutputWorkspace"] == f"VULCAN_{RUN}"
    assert "CalFileName" in kwargs
    assert kwargs["L1"] == pytest.approx(43.755, rel=1e-3)


@pytest.mark.usefixtures("output_dir")
def test_vnextbin_calls_save_gss(mantid_mocks):
    _, mock_save = mantid_mocks

    Backend().vnextbin(ipts=IPTS, runs=RUN)

    mock_save.assert_called_once()
    kwargs = mock_save.call_args.kwargs
    assert kwargs["SplitFiles"] is False
    assert kwargs["Format"] == "SLOG"
    assert str(RUN) in kwargs["Filename"]


@pytest.mark.usefixtures("output_dir", "mantid_mocks")
def test_vnextbin_output_path():
    result = Backend().vnextbin(ipts=IPTS, runs=RUN)

    assert "output" in result
    output = Path(result["output"])
    assert output.suffix == ".gda"
    assert str(RUN) in output.name


@pytest.mark.usefixtures("output_dir")
def test_vnextbin_run_range(mantid_mocks):
    """A range covering only one real run should call AlignAndFocusPowderSlim
    once and return the single .gda path (not the directory)."""
    mock_align, _ = mantid_mocks
    # RUN exists; RUN+1 through RUN+4 do not
    result = Backend().vnextbin(ipts=IPTS, runs=RUN, rune=RUN + 4)

    assert mock_align.call_count == 1
    assert Path(result["output"]).suffix == ".gda"


# ---------------------------------------------------------------------------
# vnextbin_n / vnextbin_ns — vanadium-normalized binning
# ---------------------------------------------------------------------------


@pytest.fixture
def mantid_norm_mocks():
    """Patch the Mantid calls used by the vanadium-normalized binning path."""
    mock_mtd = MagicMock()
    mock_mtd.__contains__ = lambda *_: False  # nothing in mtd → skip DeleteWorkspace

    with (
        patch("vnext.reduction.AlignAndFocusPowderSlim") as mock_align,
        patch("vnext.gsas.SaveGSS"),
        patch("vnext.reduction.DeleteWorkspace"),
        patch("vnext.reduction.RebinToWorkspace") as mock_rebin,
        patch("vnext.reduction.Divide") as mock_divide,
        patch("vnext.reduction.SmoothData") as mock_smooth,
        patch("vnext.reduction.mtd", mock_mtd),
    ):
        yield {"align": mock_align, "rebin": mock_rebin, "divide": mock_divide, "smooth": mock_smooth}


def test_vnextbin_n_requires_runv():
    with pytest.raises(ValueError, match="runv"):
        Backend().vnextbin_n(ipts=IPTS, runs=RUN)


def test_vnextbin_ns_requires_runv():
    with pytest.raises(ValueError, match="runv"):
        Backend().vnextbin_ns(ipts=IPTS, runs=RUN)


def test_vnextbin_n_missing_vanadium_raises():
    # The missing-vanadium check fires before any Mantid call, so no mocks needed.
    with pytest.raises(FileNotFoundError):
        Backend().vnextbin_n(ipts=IPTS, runs=RUN, runv=999999)


@pytest.mark.usefixtures("output_dir")
def test_vnextbin_n_focuses_vanadium_and_divides(mantid_norm_mocks):
    """Sample and vanadium are both focused, then the sample is divided by it."""
    # Use the one real NeXus file as both sample and vanadium.
    result = Backend().vnextbin_n(ipts=IPTS, runs=RUN, runv=RUN)

    # AlignAndFocusPowderSlim runs once for the vanadium and once for the sample.
    assert mantid_norm_mocks["align"].call_count == 2
    mantid_norm_mocks["rebin"].assert_called_once()
    mantid_norm_mocks["divide"].assert_called_once()
    mantid_norm_mocks["smooth"].assert_not_called()  # _n does not smooth
    assert Path(result["output"]).suffix == ".gda"


@pytest.mark.usefixtures("output_dir")
def test_vnextbin_ns_smooths_vanadium(mantid_norm_mocks):
    Backend().vnextbin_ns(ipts=IPTS, runs=RUN, runv=RUN)

    mantid_norm_mocks["smooth"].assert_called_once()
    mantid_norm_mocks["divide"].assert_called_once()


# ---------------------------------------------------------------------------
# vnextsum — co-add GSAS files over a set of runs
# ---------------------------------------------------------------------------


@pytest.fixture
def binned_dirs():
    """Create the binned_data input dir and Summed_GDA output dir, then clean up."""
    from vnext import Config

    binned = Path(Config["instrument.reduction.bin"].format(IPTS=IPTS))
    summed = Path(Config["instrument.reduction.sum"].format(IPTS=IPTS))
    binned.mkdir(parents=True, exist_ok=True)
    yield binned, summed
    shutil.rmtree(binned, ignore_errors=True)
    shutil.rmtree(summed, ignore_errors=True)


def _bank0_y(gda_path):
    """Load a GSAS file and return the bank-1 intensities as a numpy array."""
    from mantid.simpleapi import (
        DeleteWorkspace,
        LoadGSS,
    )

    ws = LoadGSS(Filename=str(gda_path), OutputWorkspace="_assert_load")
    y = ws.readY(0).copy()
    DeleteWorkspace("_assert_load")
    return y


def test_vnextsum_runv_raises():
    with pytest.raises(NotImplementedError):
        Backend().vnextsum(ipts=IPTS, runs=100, runv=5000)


def test_vnextsum_no_files_returns_dir(binned_dirs):
    _, summed = binned_dirs
    result = Backend().vnextsum(ipts=IPTS, runs=999999)
    assert Path(result["output"]) == summed


def test_vnextsum_sums_range(binned_dirs, place_gda):
    binned, summed = binned_dirs
    f1 = place_gda(1, binned / "100.gda")
    f2 = place_gda(2, binned / "101.gda")

    result = Backend().vnextsum(ipts=IPTS, runs=100, rune=101)

    # Named after the first run, written under Summed_GDA.
    assert Path(result["output"]) == summed / "100.gda"
    import numpy as np

    np.testing.assert_allclose(_bank0_y(result["output"]), _bank0_y(f1) + _bank0_y(f2))


def test_vnextsum_runlist(binned_dirs, place_gda):
    binned, summed = binned_dirs
    place_gda(1, binned / "200.gda")
    place_gda(3, binned / "201.gda")

    result = Backend().vnextsum(ipts=IPTS, runlist=[200, 201])
    assert Path(result["output"]) == summed / "200.gda"


def test_vnextsum_skips_missing_runs(binned_dirs, place_gda):
    """A run with no .gda is skipped; output is named for the first existing run."""
    binned, summed = binned_dirs
    f1 = place_gda(1, binned / "301.gda")  # 300 is missing

    result = Backend().vnextsum(ipts=IPTS, runs=300, rune=301)

    assert Path(result["output"]) == summed / "301.gda"
    import numpy as np

    np.testing.assert_allclose(_bank0_y(result["output"]), _bank0_y(f1))


# ---------------------------------------------------------------------------
# vnextlog — read sample-environment (DASlogs) data from a run's NeXus file
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_plotting():
    """Mock the plotting layer so backend tests exercise data, not rendering."""
    with (
        patch("vnext.plotting.plot_log") as log,
        patch("vnext.plotting.plot_pattern") as pattern,
        patch("vnext.plotting.plot_contour") as contour,
        patch("vnext.plotting.plot_pixel") as pixel,
    ):
        yield {"log": log, "pattern": pattern, "contour": contour, "pixel": pixel}


def test_vnextlog_lists_logs():
    # Listing mode returns before any plotting, so no plotting mock is needed.
    result = Backend().vnextlog(ipts=IPTS, runs=LOG_RUN)
    assert result["run"] == LOG_RUN
    assert "AI1" in result["logs"]
    assert result["logs"] == sorted(result["logs"])


@pytest.mark.usefixtures("mock_plotting")
def test_vnextlog_named_log_returns_workspace():
    from mantid.simpleapi import DeleteWorkspace, mtd

    result = Backend().vnextlog(ipts=IPTS, runs=LOG_RUN, name="AI1")
    assert result["name"] == "AI1"
    assert result["ipts"] == IPTS
    assert result["run"] == LOG_RUN
    # The named-log path loads the run's logs into a workspace and hands its name back.
    assert result["workspace"] in mtd
    DeleteWorkspace(result["workspace"])


def test_vnextlog_missing_run_raises():
    with pytest.raises(FileNotFoundError):
        Backend().vnextlog(ipts=IPTS, runs=999999)


def test_vnextlog_unknown_log_raises():
    with pytest.raises(KeyError):
        Backend().vnextlog(ipts=IPTS, runs=LOG_RUN, name="not_a_real_log")


def test_vnextlog_delegates_to_plotting_layer(mock_plotting):
    """A named log's workspace is handed to the plotting layer (rendering lives there)."""
    from mantid.simpleapi import DeleteWorkspace

    result = Backend().vnextlog(ipts=IPTS, runs=LOG_RUN, name="AI1")
    mock_plotting["log"].assert_called_once()
    # plot_log(workspace, name): the log name is the second positional argument.
    assert mock_plotting["log"].call_args.args[1] == "AI1"
    DeleteWorkspace(result["workspace"])


# ---------------------------------------------------------------------------
# plotting layer
# ---------------------------------------------------------------------------


def test_plot_log_draws_series():
    import matplotlib

    matplotlib.use("Agg")
    from mantid.simpleapi import AddTimeSeriesLog, CreateSampleWorkspace, DeleteWorkspace

    from vnext.plotting import plot_log

    ws = CreateSampleWorkspace(OutputWorkspace="test_plot_log_ws")
    AddTimeSeriesLog(ws, Name="AI1", Time="2010-01-01T00:00:00", Value=20.0)
    AddTimeSeriesLog(ws, Name="AI1", Time="2010-01-01T00:00:10", Value=21.0)

    ax = plot_log(ws, "AI1", show=False)
    assert len(ax.lines) == 1
    assert "AI1" in ax.get_ylabel()  # ylabel comes from the log itself
    assert "Time" in ax.get_xlabel()
    DeleteWorkspace("test_plot_log_ws")


# ---------------------------------------------------------------------------
# vnextview — load binned GSAS data for display
# ---------------------------------------------------------------------------


def test_vnextview_single_pattern(binned_dirs, mock_plotting, place_gda):
    binned, _ = binned_dirs
    place_gda(1, binned / "400.gda")

    result = Backend().vnextview(ipts=IPTS, runs=400)

    assert result["runs"] == 400
    assert len(result["banks"]) == 2
    bank = result["banks"][0]
    assert bank["bank"] == 1
    assert len(bank["x"]) == len(bank["y"])  # centres align with intensities
    mock_plotting["pattern"].assert_called_once()


def test_vnextview_sequential_contour(binned_dirs, mock_plotting, place_gda):
    binned, _ = binned_dirs
    place_gda(1, binned / "500.gda")
    place_gda(2, binned / "501.gda")
    place_gda(3, binned / "502.gda")

    result = Backend().vnextview(ipts=IPTS, runs=500, rune=502)

    assert result["runs_present"] == [500, 501, 502]
    bank = result["banks"][0]
    # intensity grid is (n_runs x n_xbins)
    assert bank["intensity"].shape[0] == 3
    assert bank["intensity"].shape[1] == len(bank["x"])
    mock_plotting["contour"].assert_called_once()


def test_vnextview_skips_missing_in_range(binned_dirs, mock_plotting, place_gda):
    binned, _ = binned_dirs
    place_gda(1, binned / "600.gda")  # 601 missing
    place_gda(2, binned / "602.gda")

    result = Backend().vnextview(ipts=IPTS, runs=600, rune=602)
    assert result["runs_present"] == [600, 602]
    mock_plotting["contour"].assert_called_once()


def test_vnextview_missing_run_raises():
    with pytest.raises(FileNotFoundError):
        Backend().vnextview(ipts=IPTS, runs=999999)


def test_vnextview_unsupported_option_raises():
    with pytest.raises(NotImplementedError):
        Backend().vnextview(ipts=IPTS, runs=400, runv=5000)


# ---------------------------------------------------------------------------
# vnextpixel — per-pixel detector contour for one run
# ---------------------------------------------------------------------------


def test_vnextpixel_returns_pixel_data_and_plots(mock_plotting):
    """The run's NeXus events are reduced to per-pixel data and plotted."""
    import numpy as np

    fake = {
        "counts": np.array([1.0, 2.0, 3.0]),
        "two_theta": np.array([89.0, 90.0, 91.0]),
        "azimuthal": np.array([0.0, 1.0, 2.0]),
    }
    with patch("vnext.detector.pixel_counts", return_value=fake) as mock_counts:
        result = Backend().vnextpixel(ipts=IPTS, runs=RUN)

    mock_counts.assert_called_once()
    assert result["ipts"] == IPTS
    assert result["run"] == RUN
    np.testing.assert_array_equal(result["counts"], fake["counts"])
    mock_plotting["pixel"].assert_called_once()


def test_vnextpixel_missing_run_raises():
    with pytest.raises(FileNotFoundError):
        Backend().vnextpixel(ipts=IPTS, runs=999999)


def test_vnextpixel_runv_raises():
    with pytest.raises(NotImplementedError):
        Backend().vnextpixel(ipts=IPTS, runs=RUN, runv=2000)


def test_plot_pixel_colours_counts():
    import matplotlib

    matplotlib.use("Agg")
    import numpy as np

    from vnext.plotting import plot_pixel

    pixel = {
        "ipts": IPTS,
        "run": RUN,
        "counts": np.array([1.0, 5.0, 9.0]),
        "two_theta": np.array([89.0, 90.0, 91.0]),
        "azimuthal": np.array([-1.0, 0.0, 1.0]),
    }
    ax = plot_pixel(pixel, show=False)
    assert len(ax.collections) == 1  # one scatter collection
    assert ax.get_ylabel() == "2theta (deg)"


def test_plot_pattern_draws_each_bank():
    import matplotlib

    matplotlib.use("Agg")
    from mantid.simpleapi import CreateWorkspace, DeleteWorkspace

    from vnext.plotting import plot_pattern

    # Two spectra = two banks.
    ws = CreateWorkspace(
        DataX=[1.0, 2.0, 3.0, 1.0, 2.0, 3.0],
        DataY=[10.0, 20.0, 15.0, 5.0, 8.0, 6.0],
        NSpec=2,
        UnitX="TOF",
        OutputWorkspace="test_plot_pattern_ws",
    )
    ws.setTitle("IPTS-1 run 400")

    ax = plot_pattern(ws, show=False)
    assert len(ax.lines) == 2
    assert ax.get_title() == "IPTS-1 run 400"
    DeleteWorkspace("test_plot_pattern_ws")


def test_plot_contour_one_axes_per_bank():
    import matplotlib

    matplotlib.use("Agg")
    import numpy as np
    from mantid.simpleapi import CreateWorkspace, DeleteWorkspace

    from vnext.plotting import plot_contour

    workspaces = []
    for bank in (1, 2):
        ws = CreateWorkspace(
            DataX=np.tile([1.0, 2.0, 3.0], 3),
            DataY=np.random.rand(9),
            NSpec=3,
            UnitX="TOF",
            VerticalAxisUnit="Label",
            VerticalAxisValues=["500", "501", "502"],
            OutputWorkspace=f"test_plot_contour_ws{bank}",
        )
        ws.setTitle(f"bank {bank}")
        workspaces.append(ws)

    axes = plot_contour(workspaces, show=False)
    assert len(axes) == 2
    for bank in (1, 2):
        DeleteWorkspace(f"test_plot_contour_ws{bank}")
