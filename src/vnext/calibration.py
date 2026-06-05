import bisect
import datetime
import os
from dataclasses import dataclass
from pathlib import Path

from mantid.kernel import Logger

from vnext import Configuration
from vnext._typing import FilePath

_log = Logger("vnext.calibration")


@dataclass
class FocusPositions:
    l1: float
    specnum: list[int]
    l2: list[float]
    polar: list[float]
    azimuthal: list[float]

    def __init__(
        self,
        l1: float | int,
        l2: list[float] | list[int],
        polar: list[float] | list[int],
        azimuthal: list[float] | list[int],
        specnum: list[int] | list[float] | None = None,
    ):
        """This will coerce all types and make sure all arrays are the same length"""
        self.l1 = float(l1)
        if not (len(l2) == len(polar) == len(azimuthal)):
            raise ValueError(f"All arrays must be equal length: {len(l2)} == {len(polar)} == {len(azimuthal)}")
        self.l2 = [float(item) for item in l2]  # convert to floats
        self.polar = [float(item) for item in polar]  # convert to floats
        self.azimuthal = [float(item) for item in azimuthal]  # convert to floats

        if specnum is not None:  # implicit values for spectrum numbers
            if len(l2) != len(specnum):
                raise ValueError(f"All arrays must be equal length: {len(l2)} == {len(specnum)}")
            self.specnum = [int(item) for item in specnum]
        else:
            self.specnum = list(range(1, len(self.l2) + 1))


def _get_focuspositions_from_char_file(filepath: FilePath) -> FocusPositions:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Characterization file does not exist: {filepath}")

    from mantid.simpleapi import PDLoadCharacterizations, mtd  # ty: ignore[unresolved-import]

    # use mantid to parse the file
    wkspname = mtd.unique_name(5, prefix="pdchar")
    (_, _, l1, specnum, l2, polar, azimuthal) = PDLoadCharacterizations(
        Filename=str(filepath), OutputWorkspace=wkspname
    )
    if wkspname in mtd:
        mtd.remove(wkspname)  # it wasn't needed

    # convert to the correct object type
    return FocusPositions(l1=l1, specnum=specnum, l2=l2, polar=polar, azimuthal=azimuthal)


# files that have DIFC , grouping, and mask information for reduction keyed by the valid date
CALIB_FILE_LIST: dict[datetime.datetime, FilePath] = {
    datetime.datetime(2000, 1, 1): "vulcan_foc_all_2bank_11p.cal",
    datetime.datetime(2017, 7, 1): "VULCAN_calibrate_2019_06_27.h5",
    datetime.datetime(2022, 5, 13): "B123456DIFCs-12Cross-3456Cal_v4.h5",
    datetime.datetime(2026, 1, 1): "B123456DIFCs-12Cross-3456789Cal.h5",
}

# files that have the focus positions and bin edges for reduction keyed by the valid date
FOCUS_POS_LIST = {
    # really old ones are in a characterization file
    datetime.datetime(2000, 1, 1): "VULCAN_Characterization_2Banks_v2.txt",
    # newer ones are hard coded in the code since they are used for focusing and we don't want to have to
    # read a file to get them
    datetime.datetime(2017, 7, 1):
    # copied from VULCAN_Characterization_3Banks_v2.txt
    FocusPositions(
        l1=43.755,
        l2=[2.288371, 2.288371, 2.061211, 2.058998, 2.020524, 2.533234],
        polar=[89.966, 89.966, 120.053, 150.040, 157.127, 65.518],
        azimuthal=[0, 0, 0, 0, 0, 0],
    ),
    datetime.datetime(2022, 5, 13):  # copied from "VULCAN_Characterization_6Banks_v2.txt",
    FocusPositions(
        l1=43.755,
        l2=[2.296492906, 2.296492906, 1.999243],
        polar=[89.9260985, 89.9260985, 149.8646347],
        azimuthal=[0, 0, 0],
    ),
    datetime.datetime(2026, 1, 1): FocusPositions(
        l1=43.755,
        l2=[2.296, 2.296, 2.07, 2.07, 2.07, 2.53, 2.07, 2.07, 2.53],
        polar=[90, 90, 120, 150, 157, 65.5, 150, 157, 65.5],
        azimuthal=[180, 0, 0, 0, 180, 180, 0, 0, 0],
    ),
}

"""
PREVIOUS code also had bonus files for copying exact bin edges from vdrive
    # 2000-1-1 ~ 2017-6-30
    "/SNS/VULCAN/shared/CALIBRATION/2011_1_7/vdrive_log_bin.dat",
    # 2017-7-1 ~ 2022-11-4
    "/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/vdrive_3bank_bin.h5",
    # 2022-11-5 ~ current
    "/SNS/VULCAN/shared/Malcolm/vdrive_6bank_bin.h5",  # used for matching bin edges to vdrive output

It has ben decided that it was always a matter of defining histograms by bin boundary vs bin centers. Inputs are being
modified to account for this.
"""


def get_calibration_info(
    date_aquired: datetime.datetime, config: Configuration | None = None
) -> tuple[Path, FocusPositions]:
    """
    Get the correct calibration files for reduction based on the date of acquisition of the data. This will use the
    date of the NeXus file to determine which calibration files to use for reduction.

    Usage example

    Parameters:
    - date_aquired: Date data was measured to find correct calibration information
    - config: Alternate configuration. Used in testing

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
    # convert the dates into a list and use bisect to find the correct calibration files
    valid_dates = list(CALIB_FILE_LIST.keys())
    # locate the position of the date in the list
    char_index = bisect.bisect_right(valid_dates, date_aquired) - 1
    # error check that the result makes sense
    if char_index < 0 or char_index >= len(valid_dates):
        raise ValueError("File date is out of range for calibration files")
    date = valid_dates[char_index]
    _log.debug(f"Calibration information for date {date_aquired} is valid from {date}")

    # convert the calibration file into a Path
    calib_file = CALIB_FILE_LIST[date]
    if type(calib_file) is not Path:
        if config is None:  # lazy creation
            config = Configuration()
        calib_path = Path(config.get_calibration_path())
        calib_file = calib_path / calib_file
        # write the result back into the dict so we don't have to do it again
        CALIB_FILE_LIST[date] = calib_file
    #
    focus_pos = FOCUS_POS_LIST[date]
    if type(focus_pos) is not FocusPositions:
        # create the path to a file to read
        if config is None:  # lazy creation
            config = Configuration()
        calib_path = Path(config.get_calibration_path())
        focus_pos = calib_path / str(focus_pos)  # force type
        focus_pos = _get_focuspositions_from_char_file(focus_pos)  # changing type
        # write the result back into the dict so we don't have to do it again
        FOCUS_POS_LIST[date] = focus_pos

    # return the results
    return calib_file, focus_pos


"""
# TODO should ask the config object up top
calfile = Path("/home/pf9/build/mantid/vulcanperf/B123456DIFCs-12Cross-3456789Cal.h5")
# TODO should use positions from elsewhere
l1 = 43.755
l2 = [2.296,2.296,2.07,2.07,2.07,2.53,2.07,2.07,2.53]
polar=[90,90,120,150,157,65.5,150,157,65.5]
azimuthal=[180,0,0,0,180,180,0,0,0]
"""
