"""Event-reduction helpers shared by the binning backend methods.

Focuses raw VULCAN NeXus event data into a histogram workspace and writes the
GSAS ``.gda`` output.  Kept out of ``backend.py`` so the binning methods
(``vnextbin`` and its normalized variants) share one reduction path instead of
duplicating the Mantid plumbing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mantid.api import WorkspaceGroup
from mantid.simpleapi import (
    AlignAndFocusPowderSlim,
    DeleteWorkspace,
    Divide,
    GenerateEventsFilter,
    LoadEventNexus,
    RebinToWorkspace,
    SmoothData,
    mtd,
)

from vnext import UNSET_FLOAT, Config
from vnext.calibration import get_calibration_info, get_tof_bins
from vnext.fileservice import get_runs_in_range
from vnext.gsas import save_gss
from vnext.nexus import extract_nexus_metadata

# Boxcar window for smoothing the vanadium spectrum in normalize+smooth binning,
# mirroring VDRIVE VPEAK's default Nsmooth.
VANADIUM_SMOOTH_NPOINTS = 51


def focus_run(nexus_file: Path, ws_name: str, *, splitter_ws: str | None = None) -> str:
    """Focus one raw NeXus run into the histogram workspace *ws_name*.

    Reads the run's chopper settings, picks the date-appropriate calibration and
    focus positions, computes per-bank TOF binning, and runs
    ``AlignAndFocusPowderSlim``.  Returns *ws_name* for convenience.

    When *splitter_ws* is given, the events are time/value-sliced by that splitter
    while streaming from the file, so *ws_name* becomes a ``WorkspaceGroup`` with
    one focused histogram per slice (this is how ``chop_runs`` reuses the binning
    path).
    """

    run_date, center_wavelength, frequency = extract_nexus_metadata(nexus_file)
    calib_file, focus_pos = get_calibration_info(run_date)
    tof = get_tof_bins(run_date)

    optional = {"SplitterWorkspace": splitter_ws} if splitter_ws is not None else {}
    AlignAndFocusPowderSlim(
        Filename=str(nexus_file),
        CalFileName=str(calib_file),
        L1=focus_pos.l1,
        L2=focus_pos.l2,
        Polar=focus_pos.polar,
        Azimuthal=focus_pos.azimuthal,
        BinningUnits="TOF",
        XMin=tof.xmin,
        XDelta=tof.xdelta,
        XMax=tof.xmax,
        LogBlockList=r"Phase*,Speed*,BL*:Chop:*,chopper*TDC",
        OutputWorkspace=ws_name,
        **optional,
    )
    return ws_name


def focus_vanadium(nexus_file: Path, ws_name: str, *, smooth: bool = False) -> str:
    """Focus a vanadium run; optionally boxcar-smooth its spectrum.

    The vanadium is reduced the same way as a sample run (it is an ordinary event
    NeXus file identified by ``runv``).  Smoothing approximates the ``-s.gda``
    smoothed vanadium that VDRIVE's VPEAK produces.
    """
    focus_run(nexus_file, ws_name)
    if smooth:
        SmoothData(InputWorkspace=ws_name, NPoints=VANADIUM_SMOOTH_NPOINTS, OutputWorkspace=ws_name)
    return ws_name


def divide_by_vanadium(sample_ws: str, vanadium_ws: str) -> None:
    """Normalize *sample_ws* in place by *vanadium_ws*.

    The vanadium is rebinned to the sample's bins first so the division is valid
    even when the two runs were reduced with slightly different TOF binning.
    """

    aligned = mtd.unique_name(prefix=f"__{vanadium_ws}_aligned")
    RebinToWorkspace(WorkspaceToRebin=vanadium_ws, WorkspaceToMatch=sample_ws, OutputWorkspace=aligned)
    Divide(LHSWorkspace=sample_ws, RHSWorkspace=aligned, OutputWorkspace=sample_ws)
    if aligned in mtd:
        DeleteWorkspace(aligned)


def bin_runs(ipts: int, runs: int, rune: int, *, runv: int = -1, smooth: bool = False) -> dict[str, Any]:
    """Focus a range of runs to GSAS files, optionally normalized by vanadium.

    Missing run files are skipped silently.  When ``runv`` is given, that run is
    focused once (and smoothed when ``smooth`` is set) and divided into every
    sample run.  Returns the single output path when one file is written,
    otherwise the output directory.
    """

    output_dir = Path(Config["instrument.reduction.bin"].format(IPTS=ipts))
    output_dir.mkdir(parents=True, exist_ok=True)

    vanadium_ws = None
    if runv != -1:
        vanadium_file = Path(Config["instrument.data.file"].format(IPTS=ipts, run=runv))
        if not vanadium_file.exists():
            raise FileNotFoundError(f"Vanadium NeXus file not found for run {runv}: {vanadium_file}")
        vanadium_ws = focus_vanadium(vanadium_file, mtd.unique_name(prefix=f"__VULCAN_van_{runv}"), smooth=smooth)

    all_runs = get_runs_in_range(ipts, runs, rune)
    if len(all_runs) == 0:
        raise ValueError(f"No valid runs found for IPTS {ipts} in range {runs}-{rune}")

    saved_files = []

    for run, nexus_file in all_runs.items():
        ws_name = mtd.unique_name(prefix=f"__VULCAN_{run}")
        focus_run(nexus_file, ws_name)
        if vanadium_ws is not None:
            divide_by_vanadium(ws_name, vanadium_ws)
        saved_files.append(save_gss(ws_name, output_dir / f"{run}.gda"))

        if ws_name in mtd:
            DeleteWorkspace(ws_name)

    if vanadium_ws is not None and vanadium_ws in mtd:
        DeleteWorkspace(vanadium_ws)

    if len(saved_files) == 1:
        return {"output": saved_files[0]}
    return {"output": str(output_dir)}


def _generate_chop_splitter(logs_ws: str, splitter_ws: str, info_ws: str, *, dbin, se, dse, minv, maxv) -> None:
    """Build a slicing splitter from a run's logs with ``GenerateEventsFilter``.

    Two modes, selected by *se*:

    - time slicing (``se is None``): contiguous slices of width *dbin* seconds,
      relative to the run start, optionally bounded by *minv*/*maxv* seconds.
    - sample-environment slicing: slices of width *dse* in the value of log *se*,
      optionally bounded by *minv*/*maxv* in that log's units.
    """

    common = {"InputWorkspace": logs_ws, "OutputWorkspace": splitter_ws, "InformationWorkspace": info_ws}
    if se is None:
        bounds = {}
        if minv != UNSET_FLOAT:
            bounds["StartTime"] = str(minv)
        if maxv != UNSET_FLOAT:
            bounds["StopTime"] = str(maxv)
        GenerateEventsFilter(**common, UnitOfTime="Seconds", RelativeTime=True, TimeInterval=dbin, **bounds)
    else:
        bounds = {}
        if minv != UNSET_FLOAT:
            bounds["MinimumLogValue"] = minv
        if maxv != UNSET_FLOAT:
            bounds["MaximumLogValue"] = maxv
        GenerateEventsFilter(**common, LogName=se, LogValueInterval=dse, **bounds)


def chop_runs(
    ipts: int,
    run: int,
    *,
    dbin: float = 1.0,
    se: str | None = None,
    dse: float = 1.0,
    minv: float = UNSET_FLOAT,
    maxv: float = UNSET_FLOAT,
) -> dict[str, Any]:
    """Chop one continuously collected run into slices and focus each to GSAS.

    The run's events are sliced — by wall-clock time (*dbin* seconds) or by a
    sample-environment log value (*se*/*dse*) — and every slice is focused with
    the same calibration/TOF path as ``bin_runs``.  Output GSAS files are written
    to ``binned_data/<run>/<i>.gda`` (1-based slice index), the location VDRIVE's
    ``VBIN``/``VIEW`` read back from via ``choprun=<run>``.

    Returns the chopped-data directory and the list of files written.

    Note: writing the synchronized sample-environment summary files
    (``<run>sampleenv_chopped_{mean,start,end}.txt``) is not done here yet; it
    depends on sample-environment log selection that the chop signatures do not
    expose, and is tracked separately.
    """

    nexus_file = Path(Config["instrument.data.file"].format(IPTS=ipts, run=run))
    if not nexus_file.exists():
        raise FileNotFoundError(f"NeXus file not found for run {run}: {nexus_file}")

    output_dir = Path(Config["instrument.reduction.bin"].format(IPTS=ipts)) / str(run)
    output_dir.mkdir(parents=True, exist_ok=True)

    logs_ws = mtd.unique_name(prefix=f"__VULCAN_{run}_logs")
    splitter_ws = mtd.unique_name(prefix=f"__VULCAN_{run}_splitter")
    info_ws = mtd.unique_name(prefix=f"__VULCAN_{run}_splitinfo")
    chopped_ws = mtd.unique_name(prefix=f"__VULCAN_{run}_chopped")

    LoadEventNexus(Filename=str(nexus_file), OutputWorkspace=logs_ws, MetaDataOnly=True, LoadLogs=True)
    _generate_chop_splitter(logs_ws, splitter_ws, info_ws, dbin=dbin, se=se, dse=dse, minv=minv, maxv=maxv)
    focus_run(nexus_file, chopped_ws, splitter_ws=splitter_ws)

    # Slicing yields a WorkspaceGroup (one focused histogram per slice); a single
    # slice may come back as a bare workspace.
    focused = mtd[chopped_ws]
    members = list(focused.getNames()) if isinstance(focused, WorkspaceGroup) else [chopped_ws]

    saved_files = []
    for index, member in enumerate(members, start=1):
        saved_files.append(save_gss(member, output_dir / f"{index}.gda"))

    for temp_ws in (chopped_ws, logs_ws, splitter_ws, info_ws):
        if temp_ws in mtd:
            DeleteWorkspace(temp_ws)

    return {"output": str(output_dir), "run": run, "segments": len(saved_files), "files": saved_files}
