import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vnext import Config
from vnext.fileservice import find_run_file, get_ipts

TESTS_DIR = Path(__file__).parent
IPTS = 36261
RUN = 260112


@pytest.fixture
def filefinder_mocks():
    mock_filefinder = MagicMock()
    mock_filefinder.findRuns.side_effect = lambda run_id: [Path(Config["instrument.data.home"]) / f"{run_id}.nxs.h5"]

    with patch("vnext.fileservice.FileFinder", mock_filefinder) as mock_filefinder:
        yield mock_filefinder


@pytest.fixture
def output_dir():
    """Yield the directory vnextbin will write .gda files to."""

    d = Path(Config["instrument.reduction.bin"].format(IPTS=IPTS))
    d.mkdir(parents=True, exist_ok=True)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_find_file_nonexistent_run():
    assert find_run_file(-1) is None


@pytest.mark.usefixtures("output_dir", "filefinder_mocks")
def test_find_file_exists():
    # This test assumes that the run file exists in the data directory.
    # Adjust the run number as needed to match an existing run.
    run_file = find_run_file(RUN)
    assert run_file is not None
    assert run_file.exists()
    assert run_file == Path(Config["instrument.data.file"].format(IPTS=IPTS, run=RUN))


@patch("vnext.fileservice.find_run_file")
def test_get_ipts(mock_find_run_file):
    # Mock the find_run_file to return a specific path
    mock_find_run_file.return_value = Path(f"/SNS/VULCAN/IPTS-{IPTS}/nexus/VULCAN_{RUN}.nxs.h5")
    ipts = get_ipts(RUN)
    assert ipts is not None
    assert ipts == IPTS
