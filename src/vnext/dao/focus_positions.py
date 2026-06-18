import datetime
from dataclasses import dataclass, field
from functools import cache


@dataclass
class FocusPositions:
    """Detector geometry parameters needed to focus neutron event data.

    Attributes:
        l1:        Primary flight path (m), source to sample.
        l2:        Secondary flight paths (m), one per focus group.
        polar:     Effective 2-theta angles (degrees), one per focus group.
        azimuthal: Effective azimuthal angles (degrees), one per focus group.
        specnum:   Spectrum numbers, one per focus group. Auto-assigned 1..N if not provided.
    """

    l1: float
    l2: list[float]
    polar: list[float]
    azimuthal: list[float]
    specnum: list[int] = field(default_factory=list)

    def __post_init__(self):
        """
        Validate the inputs values for focus position.
        This runs after initialization.
        Ensures all lists have the same length, and generates values for optional inputs
        """
        self.l1 = float(self.l1)
        self.l2 = [float(v) for v in self.l2]
        self.polar = [float(v) for v in self.polar]
        self.azimuthal = [float(v) for v in self.azimuthal]

        n = len(self.l2)
        if not (len(self.polar) == n and len(self.azimuthal) == n):
            raise ValueError(
                f"l2, polar, and azimuthal must all be the same length "
                f"(got {n}, {len(self.polar)}, {len(self.azimuthal)})"
            )

        if len(self.specnum) > 0:
            self.specnum = [int(v) for v in self.specnum]
            if len(self.specnum) != n:
                raise ValueError(f"specnum length {len(self.specnum)} does not match focus group count {n}")
        else:
            self.specnum = list(range(1, n + 1))


@cache  # NOTE: standard cache is sufficient here, since it is always the same dict returned
def load_focus_positions() -> dict[datetime.datetime, FocusPositions | str]:
    """Load the era-indexed focus positions from the bundled YAML.

    Returns a dict keyed by the era start date.  Values are either a
    ``FocusPositions`` instance (for eras with inline geometry) or a plain
    ``str`` filename (for eras that must be loaded at runtime via
    ``PDLoadCharacterizations``).
    """
    import yaml  # soft import — only needed here
    from neutrons_standard.config import Resource

    raw = yaml.safe_load(Resource.read("focus_positions.yaml"))

    result: dict[datetime.datetime, FocusPositions | str] = {}
    for entry in raw:
        valid_from = datetime.datetime.fromisoformat(entry["valid_from"])
        if "char_file" in entry:
            result[valid_from] = entry["char_file"]
        else:
            result[valid_from] = FocusPositions(
                l1=entry["l1"],
                l2=entry["l2"],
                polar=entry["polar"],
                azimuthal=entry["azimuthal"],
            )
    return result
