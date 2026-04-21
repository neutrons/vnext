import bisect
import datetime
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union


@dataclass
class FocusPositions:
    l1: float
    specnum: list[int]
    l2: list[float]
    polar: list[float]
    aziumuthal: list[float]

    def __init__(
        self,
        l1: float,
        l2: list[float],
        polar: list[float],
        azimuthal: list[float],
        specnum: Optional[list[int]] = None,
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


FilePath = Union[str, Path]


def get_focuspositions_from_char_file(filepath: FilePath):
    from mantid.simpleapi import PDLoadCharacterizations, mtd

    # use mantid to parse the file
    wkspname = "pdchar"
    (_, _, l1, specnum, l2, polar, azimuthal) = PDLoadCharacterizations(
        Filename=str(filepath), OutputWorkspace=wkspname
    )
    if wkspname in mtd:
        mtd.remove(wkspname)  # it wasn't needed

    # convert to the correct object type
    return FocusPositions(l1=l1, specnum=specnum, l2=l2, polar=polar, azimuthal=azimuthal)


# Each record is
# record[0] calibration file with difc, mask, and grouping
# record[1] focus positions associated with grouping in calibration file
# record[2] bin edges per bank in very implicit manner
CalibrationFilesList = [
    # 2000-1-1 ~ 2017-6-30
    [
        "/SNS/VULCAN/shared/CALIBRATION/2011_1_7/vulcan_foc_all_2bank_11p.cal",
        "/SNS/VULCAN/shared/CALIBRATION/2011_1_7/VULCAN_Characterization_2Banks_v2.txt",
        "/SNS/VULCAN/shared/CALIBRATION/2011_1_7/vdrive_log_bin.dat",
    ],
    # 2017-7-1 ~ 2022-11-4
    [
        "/SNS/VULCAN/shared/CALIBRATION/2019_6_27/VULCAN_calibrate_2019_06_27.h5",
        "/SNS/VULCAN/shared/CALIBRATION/2021_2_15_CAL/VULCAN_Characterization_3Banks_v2.txt",
        "/SNS/VULCAN/shared/CALIBRATION/2017_8_11_CAL/vdrive_3bank_bin.h5",
    ],
    # 2022-11-5 ~ current
    [
        "/SNS/VULCAN/shared/CALIBRATION/B123456DIFCs-12Cross-3456Cal_v4.h5",  # used for focusing
        "/SNS/VULCAN/shared/Malcolm/VULCAN_Characterization_6Banks_v2.txt",  # used for edit instrument geometry
        "/SNS/VULCAN/shared/Malcolm/vdrive_6bank_bin.h5",  # used for matching bin edges to vdrive output
    ],
]
ValidDateList = [
    datetime.datetime(2000, 1, 1),
    datetime.datetime(2017, 7, 1),
    datetime.datetime(2022, 5, 13),
    datetime.datetime(2100, 1, 1),
]


def get_auto_reduction_calibration_files(nexus_file_name):
    """
    get calibration files for auto reduction according to the date of the NeXus event file is generated
    :param nexus_file_name:
    :return:
    """
    # check input
    assert isinstance(nexus_file_name, str), (
        f"Input event NeXus file {nexus_file_name} must be a string but not a {type(nexus_file_name)}."
    )
    if os.path.exists(nexus_file_name) is False:
        raise RuntimeError(f"Event NeXus file {nexus_file_name} does not exist or is not accessible.")

    # get the date of the NeXus file
    event_file_time = datetime.datetime.fromtimestamp(os.path.getmtime(nexus_file_name))

    # locate the position of the date in the list
    char_index = bisect.bisect_right(ValidDateList, event_file_time) - 1
    if char_index < 0 or char_index >= len(ValidDateList):
        raise RuntimeError("File date is out of range.")

    return CalibrationFilesList[char_index]


"""
# TODO should ask the config object up top
calfile = Path("/home/pf9/build/mantid/vulcanperf/B123456DIFCs-12Cross-3456789Cal.h5")
# TODO should use positions from elsewhere
l1 = 43.755
l2 = [2.296,2.296,2.07,2.07,2.07,2.53,2.07,2.07,2.53]
polar=[90,90,120,150,157,65.5,150,157,65.5]
azimuthal=[180,0,0,0,180,180,0,0,0]
"""
