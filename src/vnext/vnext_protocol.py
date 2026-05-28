from typing import Any, Protocol


class VNEXTBackend(Protocol):
    def vnextview(
        self,
        *,
        ipts: int,
        runs: int = 1,
        rune: int | None = None,
        chopruns: int | None = None,
        runv: int | None = None,
        norm: int | None = None,
        pc: int | None = None,
        minv: float | None = None,
        maxv: float | None = None,
    ) -> dict[str, Any]:
        """View one GSAS gda data pattern after binning as histogram data:
        Parameters
        - runs (int): Start run number
        - rune (int | None): End run number
        - chopruns (int | None): Chopruns where data are chopped from
        - runv (int  | None): Vanadium data for normalization
        - norm (int| None): Normalize data over proton charge charge read from xml
        - pc (int  | None):  Normalize with proton charge
        - minv (float | None): Cutoff of x axis
        - maxv (float | None):Cutoff of x axis."""
        ...

    def vnextbin(
        self,
        *,
        ipts: int,
        runs: int = 1,
        rune: int | None = None,
        chopruns: int | None = None,
    ) -> dict[str, Any]:
        """Bin event data to GSAS histogram files if not binned before:
        Parameters
        - runs (int): Start run number
        - rune (int | None): End run number
        - chopruns (int | None): Chopruns where data are chopped from"""
        ...

    def vnextbin_n(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    def vnextbin_ns(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    def vnextchop_en(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    def vnextchop_ens(
        self,
        *,
        ipts: int,
        runs: int = 1,
        se: str = "Temperature",
        dse: float = 1,
        minv: float | None = None,
        maxv: float | None = None,
    ) -> dict[str, Any]:
        """Chop sample environment , synchronize, and bin continuously collected data in seconds
        Parameters
        - runs (int): Start run number
        -se(str): name of sample environment to be chopped
        - minv (float | None): minimum value
        - maxv (float | None):maximum value
        - dse(float| None): sample environment bin"""
        ...

    def vnextchop(
        self,
        *,
        ipts: int,
        runs: int = 1,
        dbin: float = 1,
        minv: float | None = None,
        maxv: float | None = None,
    ) -> dict[str, Any]:
        """Chop wall clock time , synchronize, and bin continuously collected data in seconds
        Parameters
        - runs (int): Start run number
        - minv (float | None): minimum value
        - maxv (float | None):maximum value
        - dbin(float| None): time bin"""
        ...

    def vnextspf(
        self,
        *,
        ipts: int,
        runs: int = 1,
        rune: int | None = None,
        chopruns: int | None = None,
        runv: int | None = None,
        runr: int | None = None,
        pc: int | None = None,
        norm: int | None = None,
        updated: int | None = None,
        autofix: int | None = None,
        npeaks: float | None = None,
    ) -> dict[str, Any]:
        """Conduct GSAS single peak fit:
        Parameters
        - runs (int): Start run number
        - rune (int | None): End run number
        - chopruns (int | None): Chopruns where data are chopped from
        - runv (int  | None): Vanadium data for normalization
        - norm (int| None): Normalize data over proton charge charge read from xml
        - pc (int  | None):  Normalize with proton charge
        - runr(int | None): reference run number to calculate strain, default is the first run
        - updated(int /None):  update peak positions
        - autofix (int| None):
        - npeaks (float | None):number of peaks to automatically generate."""
        ...

    def vnextgsas(
        self,
        *,
        ipts: int,
        runs: int = 1,
        rune: int | None = None,
        choprun: int | None = None,
        runm: int | None = None,
    ) -> dict[str, Any]:
        """Conduct GSAS Rietveld refinement:
        Parameters
        - runs (int): Start run number
        - rune (int | None): End run number
        - choprun (int | None): Chopruns where data are chopped from
        - runm (int  | None): Template run default is first one"""
        ...

    def vnextlog(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    def vnextfit(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    def vnextprm(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    def vnextcali(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    def vnextmerge(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    def vnextpixel(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    def vnextpole(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    def vnextsum(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...
