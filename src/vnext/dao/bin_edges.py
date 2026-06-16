import datetime
from dataclasses import dataclass


@dataclass
class BinEdges:
    """Path to the era-specific TOF bin-edge file for VULCAN reduction.

    The bin-edge era boundaries are independent of the calibration file eras.

    Attributes:
        bin_edges_file: HDF5 or .dat file containing the exact TOF bin edges
                        used by VDRIVE for histogram output matching.
                        Stored as a relative path; combine with the calibration
                        home from Config to get the full path on Analysis.
    """

    bin_edges_file: str


def load_bin_edges() -> dict[datetime.datetime, BinEdges]:
    """Load the era-indexed bin-edge file references from the bundled YAML.

    The returned ``bin_edges_file`` values are relative paths; callers are
    responsible for resolving them against ``Config["instrument.calibration.home"]``.
    """
    import yaml  # soft import — only needed here
    from neutrons_standard.config import Resource

    raw = yaml.safe_load(Resource.read("bin_edges.yaml"))

    return {
        datetime.datetime.fromisoformat(entry["valid_from"]): BinEdges(
            bin_edges_file=entry["bin_edges_file"],
        )
        for entry in raw
    }
