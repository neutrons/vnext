import datetime
from pathlib import Path

import numpy as np
import pytest
from numpy import testing as nptest

from vnext import Configuration
from vnext.calibration import FocusPositions, _get_focuspositions_from_char_file, get_calibration_info

CALIB_DIR = Path(__file__).parent / "data"


def test_focuspos():
    # numbers to shorten the tests
    l1 = 1.0
    l2 = [1, 2]
    polar = [3, 4]
    azimuthal = [5, 6]

    # intentionally pass all parameters with the wrong type for the values
    fp = FocusPositions(l1=l1, l2=l2, polar=polar, azimuthal=azimuthal)
    assert fp
    assert fp.l1 == l1
    nptest.assert_equal(fp.l2, np.asarray(l2, dtype=float), strict=True)
    nptest.assert_equal(fp.polar, np.asarray(polar, dtype=float), strict=True)
    nptest.assert_equal(fp.azimuthal, np.asarray(azimuthal, dtype=float), strict=True)
    nptest.assert_equal(fp.specnum, np.asarray([1, 2], dtype=int), strict=True)

    # intentionally pass all parameters with the wrong type for the values
    specnum = [7.0, 8.0]
    fp = FocusPositions(l1=l1, l2=l2, polar=polar, azimuthal=azimuthal, specnum=specnum)
    assert fp
    nptest.assert_equal(fp.l2, np.asarray(l2, dtype=float), strict=True)
    nptest.assert_equal(fp.polar, np.asarray(polar, dtype=float), strict=True)
    nptest.assert_equal(fp.azimuthal, np.asarray(azimuthal, dtype=float), strict=True)
    nptest.assert_equal(fp.specnum, np.asarray(specnum, dtype=int), strict=True)


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


def test_get_calibration_latest():
    # get current instrument
    calib, fp = get_calibration_info(datetime.datetime(2100, 1, 2))
    assert calib.name == "B123456DIFCs-12Cross-3456789Cal.h5"
    nptest.assert_allclose(fp.l1, 43.755)
    nptest.assert_allclose(fp.l2, (2.296, 2.296, 2.07, 2.07, 2.07, 2.53, 2.07, 2.07, 2.53))
    nptest.assert_allclose(fp.polar, (90, 90, 120, 150, 157, 65.5, 150, 157, 65.5))
    nptest.assert_allclose(fp.azimuthal, (180, 0, 0, 0, 180, 180, 0, 0, 0))


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
