import datetime
from pathlib import Path

import pytest
from numpy import testing as nptest

from vnext import Configuration
from vnext.calibration import FocusPositions, _get_focuspositions_from_char_file, get_calibration_info

CALIB_DIR = Path(__file__).parent / "data"


def test_focuspos():
    # intentionally pass all parameters with the wrong type for the values
    fp = FocusPositions(l1=1.0, l2=[1, 2], polar=[3, 4], azimuthal=[5, 6])
    assert fp
    assert fp.l1 == 1.0
    assert fp.l2 == [1.0, 2.0]
    assert fp.polar == [3.0, 4.0]
    assert fp.azimuthal == [5.0, 6.0]
    assert fp.specnum == [1, 2]

    # intentionally pass all parameters with the wrong type for the values
    fp = FocusPositions(l1=1.0, l2=[1, 2], polar=[3, 4], azimuthal=[5, 6], specnum=[7.0, 8.0])
    assert fp
    assert fp.l1 == 1.0
    assert fp.l2 == [1.0, 2.0]
    assert fp.polar == [3.0, 4.0]
    assert fp.azimuthal == [5.0, 6.0]
    assert fp.specnum == [7, 8]


def test_focuspos_not_parallel():
    with pytest.raises(ValueError):
        _ = FocusPositions(l1=1.0, l2=[1], polar=[3, 4], azimuthal=[5, 6])

    with pytest.raises(ValueError):
        _ = FocusPositions(l1=1.0, l2=[1, 2], polar=[3], azimuthal=[5, 6])

    with pytest.raises(ValueError):
        _ = FocusPositions(l1=1.0, l2=[1, 2], polar=[3, 4], azimuthal=[5, 6], specnum=[7, 8, 9])


def test_get_focuspos_from_char_file():
    fp = _get_focuspositions_from_char_file(CALIB_DIR / "VULCAN_Characterization_3Banks_v2.txt")
    nptest.assert_allclose(fp.l1, 43.755)
    nptest.assert_allclose(fp.l2, (2.296492906, 2.296492906, 1.999243))
    nptest.assert_allclose(fp.polar, (89.9260985, 89.9260985, 149.8646347))
    nptest.assert_allclose(fp.azimuthal, (0, 0, 0))
    assert fp.specnum == [1, 2, 3]


def test_get_focuspos_from_char_file_no_exist():
    with pytest.raises(FileNotFoundError):
        _ = _get_focuspositions_from_char_file(CALIB_DIR / "does_not_exist.txt")


def test_get_calibration_info_bad_date():
    with pytest.raises(ValueError):
        get_calibration_info(datetime.datetime(1999, 12, 31))
    with pytest.raises(ValueError):
        get_calibration_info(datetime.datetime(2100, 1, 2))


def test_get_calibration_info_3bank():
    config = Configuration(**{"Paths.calibration": str(CALIB_DIR)})
    path, focus_pos = get_calibration_info(datetime.datetime(2020, 1, 1), config=config)
    assert path.name == "VULCAN_calibrate_2019_06_27.h5"
    assert focus_pos.l1 == 43.755


def test_get_calibration_info_6bank():
    config = Configuration(**{"Paths.calibration": str(CALIB_DIR)})
    path, focus_pos = get_calibration_info(datetime.datetime(2026, 2, 14), config=config)
    assert path.name == "B123456DIFCs-12Cross-3456789Cal.h5"
    assert focus_pos.l1 == 43.755
