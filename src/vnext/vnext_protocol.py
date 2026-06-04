from abc import ABC, abstractmethod
from typing import Any

from vnext import UNSET_FLOAT


class VNEXTBackend(ABC):
    """Abstract base class for VNEXT backend implementations.

    Each method corresponds to a magic command and must be implemented
    by the backend to perform the actual data processing and analysis tasks.
    """

    @abstractmethod
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
        """View one GSAS gda data pattern after binning as histogram data.

        Args:
            ipts: IPTS experiment number.
            runs: Start run number.
            rune: End run number.
            chopruns: Chopruns where data are chopped from.
            runv: Vanadium run for normalization.
            norm: Normalize data over proton charge read from xml.
            pc: Normalize with proton charge.
            minv: Cutoff of x axis (minimum).
            maxv: Cutoff of x axis (maximum).
        """

    @abstractmethod
    def vnextbin(
        self,
        *,
        ipts: int,
        runs: int = -1,
        rune: int = -1,
        chopruns: int = -1,
    ) -> dict[str, Any]:
        """Bin event data to GSAS histogram files if not already binned.

        Args:
            ipts: IPTS experiment number.
            runs: Start run number.
            rune: End run number.
            chopruns: Chopruns where data are chopped from.
        """

    @abstractmethod
    def vnextbin_n(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def vnextbin_ns(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def vnextchop_en(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def vnextchop(
        self,
        *,
        ipts: int,
        runs: int = -1,
        dbin: float = 1,
        minv: float = UNSET_FLOAT,
        maxv: float = UNSET_FLOAT,
    ) -> dict[str, Any]:
        """Chop wall clock time, synchronize, and bin continuously collected data.

        Args:
            ipts: IPTS experiment number.
            runs: Start run number.
            dbin: Time bin width.
            minv: Minimum value.
            maxv: Maximum value.
        """

    @abstractmethod
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
        """Chop sample environment, synchronize, and bin continuously collected data.

        Args:
            ipts: IPTS experiment number.
            runs: Start run number.
            se: Name of sample environment to chop on.
            dse: Sample environment bin width.
            minv: Minimum value.
            maxv: Maximum value.
        """

    @abstractmethod
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
        """Conduct GSAS single peak fit.

        Args:
            ipts: IPTS experiment number.
            runs: Start run number.
            rune: End run number.
            chopruns: Chopruns where data are chopped from.
            runv: Vanadium run for normalization.
            runr: Reference run for strain calculation; defaults to the first run.
            pc: Normalize with proton charge.
            norm: Normalize data over proton charge read from xml.
            updated: Update peak positions.
            autofix: Automatically fix peaks.
            npeaks: Number of peaks to automatically generate.
        """

    @abstractmethod
    def vnextgsas(
        self,
        *,
        ipts: int,
        runs: int = -1,
        rune: int = -1,
        choprun: int = -1,
        runm: int = -1,
    ) -> dict[str, Any]:
        """Conduct GSAS Rietveld refinement.

        Args:
            ipts: IPTS experiment number.
            runs: Start run number.
            rune: End run number.
            choprun: Chopruns where data are chopped from.
            runm: Template run; defaults to the first run.
        """

    @abstractmethod
    def vnextlog(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def vnextfit(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def vnextprm(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def vnextcali(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def vnextmerge(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def vnextpixel(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def vnextpole(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...

    @abstractmethod
    def vnextsum(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]: ...
