from dataclasses import dataclass


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

    def __post_init__(self):
        """Validate the input values for TOF bins.

        This runs after initialization.  Ensures that all lists have either a single value. or the same length
        """
        self.xmin = [float(v) for v in self.xmin] if isinstance(self.xmin, list) else [float(self.xmin)]
        self.xdelta = [-float(v) for v in self.xdelta] if isinstance(self.xdelta, list) else [float(self.xdelta)]
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
