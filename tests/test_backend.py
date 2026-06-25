import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vnext.backend import Backend

TESTS_DIR = Path(__file__).parent
IPTS = 36261
RUN = 260112


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
        patch("vnext.backend.AlignAndFocusPowderSlim") as mock_align,
        patch("vnext.backend.SaveGSS") as mock_save,
        patch("vnext.backend.DeleteWorkspace"),
        patch("vnext.backend.mtd", mock_mtd),
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
