import datetime
from dataclasses import dataclass
from functools import cache
from typing import Literal

BinningMode = Literal["Linear", "Logarithmic"]

TOF_MIN_DEFAULT = 5000.0
TOF_MAX_DEFAULT = 70000.0


@dataclass
class TofBins:
    """Per-bank TOF binning parameters for VULCAN reduction.

    Passed to AlignAndFocusPowderSlim as XMin, XDelta, XMax with
    BinningUnits="TOF" and BinningMode="Logarithmic".

    Attributes:
        xmin:   Minimum TOF (microseconds) per focus group.
        xdelta: Logarithmic bin step size per focus group.
        xmax:   Maximum TOF (microseconds), applied to all focus groups.

    All values must either be scalar or lists of the same length as the number of focus groups.
    """

    xmin: list[float]
    xdelta: list[float]
    xmax: list[float]
    binning_mode: BinningMode = "Logarithmic"

    def __post_init__(self):
        """Validate the input values for TOF bins.

        This runs after initialization.  Ensures that all lists have either a single value. or the same length
        """
        self.xmin = [float(v) for v in self.xmin] if isinstance(self.xmin, list) else [float(self.xmin)]
        self.xdelta = [float(v) for v in self.xdelta] if isinstance(self.xdelta, list) else [float(self.xdelta)]
        self.xmax = [float(v) for v in self.xmax] if isinstance(self.xmax, list) else [float(self.xmax)]

        nmin = len(self.xmin)
        nmax = len(self.xmax)
        nbin = len(self.xdelta)
        n = max(nmin, nmax, nbin)

        if nmin not in (1, n) or nmax not in (1, n) or nbin not in (1, n):
            raise ValueError(
                f"xmax must either be a single value or have the same length as xmin and xdelta "
                f"(got len(xmin) = {nmin}, len(xmax) = {nmax} and len(xdelta) = {nbin})"
            )


@cache  # NOTE: standard cache is sufficient here, since it is always the same dict returned
def load_tof_bins() -> dict[datetime.datetime, TofBins]:
    """Load the era-indexed TOF binning references from the bundled YAML."""
    import yaml  # soft import — only needed here
    from neutrons_standard.config import Resource

    raw = yaml.safe_load(Resource.read("tof_bins.yaml"))

    return {
        datetime.datetime.fromisoformat(entry["valid_from"]): TofBins(
            xmin=entry["xmin"],
            xdelta=entry["xdelta"],
            xmax=entry["xmax"],
            binning_mode=entry.get("binning_mode", "Logarithmic"),
        )
        for entry in raw
    }
