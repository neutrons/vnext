"""Event-reduction helpers shared by the binning backend methods.

Focuses raw VULCAN NeXus event data into a histogram workspace and writes the
GSAS ``.gda`` output.  Kept out of ``backend.py`` so the binning methods
(``vnextbin`` and its normalized variants) share one reduction path instead of
duplicating the Mantid plumbing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mantid.simpleapi import (
    AlignAndFocusPowderSlim,
    DeleteWorkspace,
    Divide,
    RebinToWorkspace,
    SmoothData,
    mtd,
)

from vnext import Config
from vnext.calibration import get_calibration_info, get_tof_bins
from vnext.fileservice import get_runs_in_range
from vnext.gsas import save_gss
from vnext.nexus import extract_nexus_metadata

# Boxcar window for smoothing the vanadium spectrum in normalize+smooth binning,
# mirroring VDRIVE VPEAK's default Nsmooth.
VANADIUM_SMOOTH_NPOINTS = 51


def focus_run(nexus_file: Path, ws_name: str) -> str:
    """Focus one raw NeXus run into the histogram workspace *ws_name*.

    Reads the run's chopper settings, picks the date-appropriate calibration and
    focus positions, computes per-bank TOF binning, and runs
    ``AlignAndFocusPowderSlim``.  Returns *ws_name* for convenience.
    """

    run_date, center_wavelength, frequency = extract_nexus_metadata(nexus_file)
    calib_file, focus_pos = get_calibration_info(run_date)
    tof = get_tof_bins(run_date)

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

    aligned = f"{vanadium_ws}_aligned"
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
        vanadium_ws = focus_vanadium(vanadium_file, f"VULCAN_van_{runv}", smooth=smooth)

    all_runs = get_runs_in_range(ipts, runs, rune)
    if len(all_runs) == 0:
        raise ValueError(f"No valid runs found for IPTS {ipts} in range {runs}-{rune}")

    saved_files = []

    for run, nexus_file in all_runs.items():
        ws_name = f"VULCAN_{run}"
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
