import bisect
import datetime
import math
import os
from collections.abc import Mapping
from pathlib import Path

from mantid.kernel import Logger

from vnext import Config, FilePath
from vnext.dao import CalibrationFiles, FocusPositions, TofBins
from vnext.dao.calibration_files import load_calibration_files as _load_calibration_files
from vnext.dao.focus_positions import load_focus_positions as _load_focus_positions
from vnext.dao.tof_bins import TOF_MAX_DEFAULT, TOF_MIN_DEFAULT
from vnext.dao.tof_bins import load_tof_bins as _load_tof_bins

_log = Logger("vnext.calibration")

CALIB_FILES: dict[datetime.datetime, CalibrationFiles] = _load_calibration_files()
FOCUS_POS_LIST: dict[datetime.datetime, FocusPositions | str] = _load_focus_positions()
TOF_BIN_LIST: dict[datetime.datetime, TofBins] = _load_tof_bins()


def _get_focuspositions_from_char_file(filepath: FilePath) -> FocusPositions:
    """Load focus positions from a VULCAN characterisation file via PDLoadCharacterizations."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Characterization file does not exist: {filepath}")

    from mantid.simpleapi import PDLoadCharacterizations, mtd

    wkspname = mtd.unique_name(5, prefix="pdchar")
    (_, _, l1, specnum, l2, polar, azimuthal) = PDLoadCharacterizations(
        Filename=str(filepath), OutputWorkspace=wkspname
    )
    if wkspname in mtd:
        mtd.remove(wkspname)

    return FocusPositions(l1=l1, specnum=specnum, l2=l2, polar=polar, azimuthal=azimuthal)


def _bisect_era(index: Mapping[datetime.datetime, object], date: datetime.datetime) -> datetime.datetime:
    """Return the era key whose valid_from is the latest date on or before *date*."""
    valid_dates = sorted(index.keys())
    idx = bisect.bisect_right(valid_dates, date) - 1
    if idx < 0 or idx >= len(valid_dates):
        raise ValueError(f"Acquisition date {date} is out of range for {list(index.keys())}")
    return valid_dates[idx]


def _calibration_home(config) -> Path:
    """Resolve the calibration home directory from a ``neutrons_standard`` config object."""
    return Path(config["instrument.calibration.home"]).expanduser()


def get_calibration_info(date_aquired: datetime.datetime, config=None) -> tuple[Path, FocusPositions]:
    """
    Get the correct calibration files for reduction based on the date of acquisition of the data. This will use the
    date of the NeXus file to determine which calibration files to use for reduction.

    Parameters:
    - date_aquired: Date data was measured to find correct calibration information
    - config: Alternate configuration providing ``instrument.calibration.home``. Defaults to the
      shared ``neutrons_standard`` ``Config`` singleton. Mainly used in testing.

    Usage example
    .. code-block::

       import vnext
       from pathlib import Path
       from datetime.datetime import fromtimestamp
       filepath = Path("/SNS/VULCAN/IPTS-37627/nexus/VULCAN_269462.nxs.h5")
       timestamp = fromtimestamp(filepath.stat().st_ctime) # creation time
       cal_file, focus_pos = vnext.calibration.get_calibration_info(timestamp)

    The calibration file will be returned as a Path object, and the focus positions will be returned as a
    FocusPositions object. The focus positions may be None if there are no focus positions for the given date. The
    calibration file may be None if there are no calibration files for the given date. The focus positions and
    calibration file is not checked for existence.
    """
    if config is None:
        config = Config
    calib_path = _calibration_home(config)

    cal_era = _bisect_era(CALIB_FILES, date_aquired)
    _log.debug(f"Using calibration era {cal_era} for acquisition date {date_aquired}")
    cal_file = calib_path / CALIB_FILES[cal_era].cal_file

    focus_era = _bisect_era(FOCUS_POS_LIST, date_aquired)
    focus_pos = FOCUS_POS_LIST[focus_era]
    if not isinstance(focus_pos, FocusPositions):
        raise TypeError(
            f"Focus positions for era {focus_era} are a char_file reference and must be "
            "resolved to inline values in focus_positions.yaml before use"
        )

    return cal_file, focus_pos


def get_tof_bins(date_aquired: datetime.datetime) -> TofBins:
    """
    Get the correct TOF binning parameters for reduction based on the date of acquisition of the data.

    Parameters:
    - date_aquired: Date data was measured to find correct calibration information

    The binning will be returned as a TofBins object
    """
    try:
        tof_era = _bisect_era(TOF_BIN_LIST, date_aquired)
        _log.debug(f"Using TOF binning era {tof_era} for acquisition date {date_aquired}")
        tof_bins = TOF_BIN_LIST[tof_era]
    except ValueError:
        focus = get_calibration_info(date_aquired)[1]
        tof_bins = compute_tof_bins(focus)
    return tof_bins


def compute_tof_bins(
    focus_pos: FocusPositions,
    *,
    delta_theta: float = 0.001,
) -> TofBins:
    """Compute per-bank TOF binning parameters from instrument geometry and run settings.

    XMin on VULCAN defaults to 5000 μs, and XMax to 70000 μs.

    To align different log binning conventions (Mantid bin-edges vs VDRIVE bin-centers),
    the XMin value is adjusted backward by half of a (linear) bin step.

    XDelta per bank is the logarithmic fractional bin step Δd/d, set to the dominant
    angular resolution term so that every diffraction peak occupies the same number of
    bins regardless of its d-spacing (peak width scales as Δd ∝ d):

        Δd/d ≈ Δθ · |cot(θ_bank)|    where θ_bank = 2θ_bank / 2

    Args:
        focus_pos: per-bank detector geometry.
        center_wavelength: chopper centre wavelength (Å).
        frequency: chopper pulse repetition frequency (Hz).
        delta_theta: effective angular uncertainty of each focused bank (radians);
            default 0.001 rad reproduces the known VULCAN values of 0.001 at 90°
            and ~0.0003 at back-scattering angles.
    """
    xmin = []
    xdelta = []
    for polar in focus_pos.polar:
        # flight_path = focus_pos.l1 + l2
        # xmin.append(lambda_min * flight_path * tof_factor)
        theta = math.radians(polar / 2.0)
        xdelta.append(delta_theta * abs(math.cos(theta) / math.sin(theta)))
        # xmin shifted backward by half a linear bin step to align with VDRIVE bin-centers
        xmin.append(TOF_MIN_DEFAULT * (1.0 - 0.5 * xdelta[-1]))

    # xmax will be constant for all banks
    xmax = [TOF_MAX_DEFAULT] * len(focus_pos.l2)

    return TofBins(xmin=xmin, xdelta=xdelta, xmax=xmax)
