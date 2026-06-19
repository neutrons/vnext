import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
import pytest
from numpy import testing as nptest

from vnext import Config
from vnext.calibration import (
    FocusPositions,
    _bisect_era,
    _get_focuspositions_from_char_file,
    compute_tof_bins,
    extract_nexus_metadata,
    get_calibration_info,
)

TESTS_DIR = Path(__file__).parent
CALIB_DIR = TESTS_DIR / "data"
VULCAN_NEXUS = CALIB_DIR / "VULCAN_260112.nxs.h5"


def test_focuspos():
    # numbers to shorten the tests
    l1 = 1.0
    l2 = [1, 2]
    polar = [3, 4]
    azimuthal = [5, 6]

    # intentionally pass all parameters with the wrong type for the values
    fp = FocusPositions(l1=l1, l2=l2, polar=polar, azimuthal=azimuthal)  # ty: ignore[invalid-argument-type]
    assert fp
    assert fp.l1 == l1
    nptest.assert_equal(fp.l2, np.asarray(l2, dtype=float), strict=True)
    nptest.assert_equal(fp.polar, np.asarray(polar, dtype=float), strict=True)
    nptest.assert_equal(fp.azimuthal, np.asarray(azimuthal, dtype=float), strict=True)
    nptest.assert_equal(fp.specnum, np.asarray([1, 2], dtype=int), strict=True)

    # intentionally pass all parameters with the wrong type for the values
    specnum = [7.0, 8.0]
    fp = FocusPositions(l1=l1, l2=l2, polar=polar, azimuthal=azimuthal, specnum=specnum)  # ty: ignore[invalid-argument-type]
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


_ERA_SORTED = {
    datetime.datetime(2017, 7, 1): "a",
    datetime.datetime(2022, 5, 13): "b",
    datetime.datetime(2026, 1, 1): "c",
}

_ERA_UNSORTED = {
    datetime.datetime(2026, 1, 1): "c",
    datetime.datetime(2017, 7, 1): "a",
    datetime.datetime(2022, 5, 13): "b",
}


def test_bisect_era_out_of_bounds():
    with pytest.raises(ValueError):
        _bisect_era(_ERA_SORTED, datetime.datetime(2000, 1, 1))


def test_bisect_era_sorted_exact_key():
    assert _bisect_era(_ERA_SORTED, datetime.datetime(2022, 5, 13)) == datetime.datetime(2022, 5, 13)


def test_bisect_era_sorted_between_keys():
    assert _bisect_era(_ERA_SORTED, datetime.datetime(2024, 6, 15)) == datetime.datetime(2022, 5, 13)


def test_bisect_era_unsorted_exact_key():
    assert _bisect_era(_ERA_UNSORTED, datetime.datetime(2017, 7, 1)) == datetime.datetime(2017, 7, 1)


def test_bisect_era_unsorted_between_keys():
    assert _bisect_era(_ERA_UNSORTED, datetime.datetime(2019, 3, 1)) == datetime.datetime(2017, 7, 1)


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
    path, focus_pos = get_calibration_info(datetime.datetime(2020, 1, 1))
    assert path.name == "VULCAN_calibrate_2019_06_27.h5"
    assert focus_pos.l1 == 43.755


def test_get_calibration_info_6bank():
    path, focus_pos = get_calibration_info(datetime.datetime(2026, 2, 14))
    assert path.name == "B123456DIFCs-12Cross-3456789Cal.h5"
    assert focus_pos.l1 == 43.755


def test_extract_nexus_metadata():
    import h5py

    run_date_iso = "2020-01-01T12:00:00.000000"
    wl_keys = ["BL7:Chop:Skf34:CenterWavelength", "skf34.lambda"]
    spd_keys = ["BL7:Chop:Skf34:SpeedReq", "skf34.speed"]
    # test_file = Config["instrument.data.file"].format(IPTS=37627, run=123456)
    with NamedTemporaryFile(dir=Config["instrument.data.home"], suffix=".nxs.h5") as nxs:
        with h5py.File(Path(nxs.name), "w") as f:
            f[f"/entry/DASlogs/{wl_keys[0]}/value"] = [b"2.8"]
            f[f"/entry/DASlogs/{spd_keys[0]}/value"] = [b"20.0"]
            f["/entry/start_time"] = [b"2020-01-01T12:00:00.000000"]

        run_date, center_wavelength, frequency = extract_nexus_metadata(nxs.name)

    assert run_date == datetime.datetime.fromisoformat(run_date_iso)
    assert center_wavelength == pytest.approx(2.8)
    assert frequency == pytest.approx(20.0)


def test_compute_tof_bins_from_nexus():
    import h5py

    with h5py.File(VULCAN_NEXUS, "r") as f:
        logs = f["entry"]["DASlogs"]
        run_date = datetime.datetime.fromisoformat(f["entry"]["start_time"][0].decode()[:19])
        center_wavelength = float(logs["BL7:Chop:Skf34:CenterWavelength"]["value"][0])
        frequency = float(logs["BL7:Chop:Skf34:SpeedReq"]["value"][0])

    assert center_wavelength == pytest.approx(2.8)
    assert frequency == pytest.approx(20.0)

    _, focus_pos = get_calibration_info(run_date)
    tof = compute_tof_bins(focus_pos, center_wavelength, frequency)

    # one entry per focus group
    assert len(tof.xmin) == len(focus_pos.l2)
    assert len(tof.xdelta) == len(focus_pos.l2)

    # equatorial banks (~90°): xdelta ≈ Δθ · cot(45°) = 0.001
    nptest.assert_allclose(tof.xdelta[0], 0.001001, rtol=1e-3)
    nptest.assert_allclose(tof.xdelta[1], 0.001001, rtol=1e-3)

    # back-scattering bank (~150°): xdelta ≈ Δθ · cot(75°) ≈ 0.000269
    nptest.assert_allclose(tof.xdelta[2], 0.000269, rtol=1e-2)

    # xmin per bank — varies with L2
    nptest.assert_allclose(tof.xmin[0], 6282.17, rtol=1e-3)
    nptest.assert_allclose(tof.xmin[2], 6241.62, rtol=1e-3)

    # xmax covers the full frame and exceeds all per-bank xmin
    assert min(tof.xmax) > max(tof.xmin)
    nptest.assert_allclose(tof.xmax, 58906.44, rtol=1e-3)

    # binning mode is logarithmic
    assert tof.binning_mode == "Logarithmic"
