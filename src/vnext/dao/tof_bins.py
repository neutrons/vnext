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
    """

    xmin: list[float]
    xdelta: list[float]
    xmax: float
