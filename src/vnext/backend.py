from typing import Any

from vnext import UNSET_FLOAT, VNEXTBackend


def func(kwargs):
    if "rune" in kwargs:
        a = [int(kwargs["rune"])]
        return a
    else:
        a = [int(kwargs["runs"])]
        return a


class Backend(VNEXTBackend):
    """The canonical VNEXT backend."""

    def vnextview(
        self,
        *,
        ipts: int,
        runs: int = -1,
        rune: int = -1,
        chopruns: int = -1,
        runv: int = -1,
        norm: int = -1,
        pc: int = -1,
        minv: float = UNSET_FLOAT,
        maxv: float = UNSET_FLOAT,
    ) -> dict[str, Any]:
        """View one GSAS gda data pattern after binning as histogram data:
        Parameters
        - runs: Start run number
        - rune: End run number
        - chopruns: Chopruns where data are chopped from
        - runv: Vanadium data for normalization
        - norm: Normalize data over proton charge charge read from xml
        - pc:  Normalize with proton charge
        - minv: Cutoff of x axis
        - maxv: Cutoff of x axis."""
        return {
            "name": "vnextview",
            "ipts": ipts,
            "runs": runs,
            "rune": rune,
            "chopruns": chopruns,
            "runv": runv,
            "norm": norm,
            "pc": pc,
            "minv": minv,
            "maxv": maxv,
        }

    def vnextbin(
        self,
        *,
        ipts: int,
        runs: int = -1,
        rune: int = -1,
        chopruns: int = -1,
    ) -> dict[str, Any]:
        """Bin event data to GSAS histogram files if not binned before:
        Parameters
        - runs: Start run number
        - rune: End run number
        - chopruns: Chopruns where data are chopped from"""
        return {"name": "vnextbin", "ipts": ipts, "runs": runs, "rune": rune, "chopruns": chopruns}

    def vnextbin_n(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextbin_n", "ipts": ipts, **kwargs}

    def vnextbin_ns(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextbin_ns", "ipts": ipts, **kwargs}

    def vnextchop(
        self,
        *,
        ipts: int,
        runs: int = -1,
        dbin: float = 1,
        minv: float = UNSET_FLOAT,
        maxv: float = UNSET_FLOAT,
    ) -> dict[str, Any]:
        """Chop wall clock time , synchronize, and bin continuously collected data in seconds
        Parameters
        - runs: Start run number
        - dbin: time bin
        - minv: minimum value
        - maxv: maximum value"""
        return {"name": "vnextchop", "ipts": ipts, "runs": runs, "dbin": dbin, "minv": minv, "maxv": maxv}

    def vnextchop_en(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextchop_en", "ipts": ipts, **kwargs}

    def vnextchop_ens(
        self,
        *,
        ipts: int,
        runs: int = -1,
        se: str = "Temperature",
        dse: float = 1,
        minv: float = UNSET_FLOAT,
        maxv: float = UNSET_FLOAT,
    ) -> dict[str, Any]:
        """Chop sample environment , synchronize, and bin continuously collected data in seconds
        Parameters
        - runs: Start run number
        - se: name of sample environment to be chopped
        - dse (float): sample environment bin
        - minv: minimum value
        - maxv: maximum value"""
        return {"name": "vnextchop_ens", "ipts": ipts, "runs": runs, "se": se, "dse": dse, "minv": minv, "maxv": maxv}

    def vnextspf(
        self,
        *,
        ipts: int,
        runs: int = -1,
        rune: int = -1,
        chopruns: int = -1,
        runv: int = -1,
        runr: int = -1,
        pc: int = -1,
        norm: int = -1,
        updated: int = -1,
        autofix: int = -1,
        npeaks: float = UNSET_FLOAT,
    ) -> dict[str, Any]:
        """Conduct GSAS single peak fit:
        Parameters
        - runs: Start run number
        - rune: End run number
        - chopruns: Chopruns where data are chopped from
        - runv: Vanadium data for normalization
        - norm: Normalize data over proton charge charge read from xml
        - pc: Normalize with proton charge
        - runr: reference run number to calculate strain, default is the first run
        - updated: update peak positions
        - autofix:
        - npeaks: number of peaks to automatically generate."""
        return {
            "name": "vnextspf",
            "ipts": ipts,
            "runs": runs,
            "rune": rune,
            "chopruns": chopruns,
            "runv": runv,
            "runr": runr,
            "pc": pc,
            "norm": norm,
            "updated": updated,
            "autofix": autofix,
            "npeaks": npeaks,
        }

    def vnextgsas(
        self,
        *,
        ipts: int,
        runs: int = -1,
        rune: int = -1,
        choprun: int = -1,
        runm: int = -1,
    ) -> dict[str, Any]:
        """Conduct GSAS Rietveld refinement:
        Parameters
        - runs: Start run number
        - rune: End run number
        - choprun: Chopruns where data are chopped from
        - runm: Template run default is first one"""
        return {"name": "vnextgsas", "ipts": ipts, "runs": runs, "rune": rune, "choprun": choprun, "runm": runm}

    def vnextlog(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextlog", "ipts": ipts, **kwargs}

    def vnextfit(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextfit", "ipts": ipts, **kwargs}

    def vnextprm(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextprm", "ipts": ipts, **kwargs}

    def vnextcali(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextcali", "ipts": ipts, **kwargs}

    def vnextmerge(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextmerge", "ipts": ipts, **kwargs}

    def vnextpixel(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextpixel", "ipts": ipts, **kwargs}

    def vnextpole(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextpole", "ipts": ipts, **kwargs}

    def vnextsum(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextsum", "ipts": ipts, **kwargs}
