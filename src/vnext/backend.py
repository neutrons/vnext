from pathlib import Path
from typing import Any

from vnext import UNSET_FLOAT, Config, VNEXTBackend, plotting
from vnext.fileservice import get_bins_in_range
from vnext.gsas import build_sequential_view, read_gsas_banks
from vnext.nexus import extract_log
from vnext.reduction import bin_runs

# vnextview options that are accepted for VDRIVE compatibility but not yet
# implemented; each maps to the "unset" sentinel that means "not requested".
_VIEW_UNSUPPORTED = (
    ("chopruns", -1),
    ("runv", -1),
    ("norm", -1),
    ("pc", -1),
    ("minv", UNSET_FLOAT),
    ("maxv", UNSET_FLOAT),
)


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
        runs: int,
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

        requested = {"chopruns": chopruns, "runv": runv, "norm": norm, "pc": pc, "minv": minv, "maxv": maxv}
        for option, sentinel in _VIEW_UNSUPPORTED:
            if requested[option] != sentinel:
                raise NotImplementedError(f"vnextview option '{option}' is not yet implemented")

        # Single pattern: rune unset (or equal to runs).
        if rune == -1 or rune == runs:
            bins = get_bins_in_range(ipts, runs)
            if not bins:
                raise FileNotFoundError(f"GSAS file not found for run {runs} in IPTS {ipts}")
            result = {"ipts": ipts, "runs": runs, "banks": read_gsas_banks(bins[runs])}
            plotting.plot_pattern(result, show=True)
            return result

        # Sequential patterns: stack each present run's intensity per bank into a 2-D grid.
        result = build_sequential_view(ipts, runs, rune)
        plotting.plot_contour(result, show=True)
        return result

    def vnextbin(
        self,
        *,
        ipts: int,
        runs: int,
        rune: int = -1,
        chopruns: int = -1,
    ) -> dict[str, Any]:
        """Bin event data to GSAS histogram files if not binned before:
        Parameters
        - runs: Start run number
        - rune: End run number
        - chopruns: Chopruns where data are chopped from"""

        if chopruns != -1:
            raise NotImplementedError("Binning of pre-chopped data is not yet implemented")

        return bin_runs(ipts, runs, rune)

    def vnextbin_n(
        self,
        *,
        ipts: int,
        runs: int,
        rune: int = -1,
        runv: int = -1,
        chopruns: int = -1,
    ) -> dict[str, Any]:
        """Bin event data and normalize by a vanadium run.

        Same focusing pipeline as ``vnextbin``, but each run is divided by the
        focused vanadium spectrum (an ordinary event run identified by ``runv``).

        Parameters
        - runs: Start run number
        - rune: End run number
        - runv: Vanadium run number for normalization (required)
        - chopruns: Chopruns where data are chopped from"""

        if chopruns != -1:
            raise NotImplementedError("Binning of pre-chopped data is not yet implemented")
        if runv == -1:
            raise ValueError("vnextbin_n requires runv (the vanadium run number)")

        return bin_runs(ipts, runs, rune, runv=runv)

    def vnextbin_ns(
        self,
        *,
        ipts: int,
        runs: int,
        rune: int = -1,
        runv: int = -1,
        chopruns: int = -1,
    ) -> dict[str, Any]:
        """Bin event data and normalize by a smoothed vanadium run.

        As ``vnextbin_n`` but the vanadium spectrum is boxcar-smoothed before the
        division, approximating the ``-s.gda`` smoothed vanadium from VPEAK.
        """
        if chopruns != -1:
            raise NotImplementedError("Binning of pre-chopped data is not yet implemented")
        if runv == -1:
            raise ValueError("vnextbin_ns requires runv (the vanadium run number)")

        return bin_runs(ipts, runs, rune, runv=runv, smooth=True)

    def vnextchop(
        self,
        *,
        ipts: int,
        runs: int,
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
        runs: int,
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
        runs: int,
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
        runs: int,
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

    def vnextlog(
        self,
        *,
        ipts: int,
        runs: int = -1,
        name: str = "",
    ) -> dict[str, Any]:
        """Open a run's sample-environment (DASlogs) data from its NeXus file.

        Without ``name`` the available log names are returned.  With ``name`` the
        elapsed-time / value series for that log is returned and handed to the
        plotting layer for display.

        Parameters
        - runs: Run number whose NeXus file is read
        - name: Name of the DASlog to extract; omit to list available logs"""

        nexus_file = Path(Config["instrument.data.file"].format(IPTS=ipts, run=runs))
        if not nexus_file.exists():
            raise FileNotFoundError(f"NeXus file not found for run {runs}: {nexus_file}")

        log_info = extract_log(nexus_file, name)

        result = {"ipts": ipts, "run": runs, **log_info}
        if name:
            plotting.plot_log(result, show=True)
        return result

    def vnextfit(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextfit", "ipts": ipts, **kwargs}

    def vnextprm(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextprm", "ipts": ipts, **kwargs}

    def vnextcali(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextcali", "ipts": ipts, **kwargs}

    def vnextmerge(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextmerge", "ipts": ipts, **kwargs}

    def vnextpixel(
        self,
        *,
        ipts: int,
        runs: int,
        runv: int = -1,
    ) -> dict[str, Any]:
        """View the per-pixel detector intensity contour for a single run.

        Loads the run's raw events, integrates total counts per detector pixel,
        and hands the result to the plotting layer as a scattering-angle map.

        Parameters
        - runs: Run number whose NeXus file is read
        - runv: Instrument parameter run (not yet implemented)"""

        from vnext import plotting
        from vnext.detector import pixel_counts

        if runv != -1:
            raise NotImplementedError("vnextpixel option 'runv' is not yet implemented")

        nexus_file = Path(Config["instrument.data.file"].format(IPTS=ipts, run=runs))
        if not nexus_file.exists():
            raise FileNotFoundError(f"NeXus file not found for run {runs}: {nexus_file}")

        result = {"ipts": ipts, "run": runs, **pixel_counts(nexus_file)}
        plotting.plot_pixel(result, show=True)
        return result

    def vnextpole(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextpole", "ipts": ipts, **kwargs}

    def vnextsum(
        self,
        *,
        ipts: int,
        runs: int = -1,
        rune: int = -1,
        runlist: list[int] | None = None,
        runfile: str = "",
        runv: int = -1,
    ) -> dict[str, Any]:
        """Sum (co-add) GSAS histogram files over a set of runs into one file.

        The set of runs is taken, in priority order, from ``runlist`` (an explicit
        list), ``runfile`` (a whitespace/newline-delimited text file of run numbers),
        or the ``runs``/``rune`` range.  Inputs are read from ``binned_data/`` and the
        summed file is written to ``Summed_GDA/<first run>.gda``.  Missing ``.gda``
        files are skipped silently, mirroring ``vnextbin``.

        Parameters
        - runs: Start run number (used with rune when no runlist/runfile given)
        - rune: End run number
        - runlist: Explicit list of run numbers to sum
        - runfile: Path to a text file of run numbers (whitespace/newline delimited)
        - runv: Vanadium run for normalization (not yet implemented)"""

        from vnext.gsas import sum_gss_files

        if runv != -1:
            raise NotImplementedError("Vanadium normalization (runv) is not yet implemented for vnextsum")

        return sum_gss_files(ipts, runs, rune, runlist, runfile)
