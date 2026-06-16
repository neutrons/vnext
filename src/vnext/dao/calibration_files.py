import datetime
from dataclasses import dataclass


@dataclass
class CalibrationFiles:
    """Paths to the era-specific calibration files for VULCAN reduction.

    Attributes:
        cal_file: HDF5 or .cal file with DIFC, grouping, and mask per detector.
                  Stored as a relative path; combine with the calibration home
                  from Config to get the full path on Analysis.
    """

    cal_file: str


def load_calibration_files() -> dict[datetime.datetime, CalibrationFiles]:
    """Load the era-indexed calibration file references from the bundled YAML.

    The returned ``cal_file`` values are relative paths; callers are responsible for
    resolving them against ``Config["instrument.calibration.home"]``.
    """
    import yaml  # soft import — only needed here
    from neutrons_standard.config import Resource

    raw = yaml.safe_load(Resource.read("calibration_files.yaml"))

    return {
        datetime.datetime.fromisoformat(entry["valid_from"]): CalibrationFiles(
            cal_file=entry["cal_file"],
        )
        for entry in raw
    }
