"""GSAS file reading utilities.

Helpers that turn binned ``.gda`` files into plain per-bank data structures.
Kept out of ``backend.py`` so the backend methods stay thin and the Mantid
``LoadGSS`` plumbing lives in one place.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np
from mantid.api import MatrixWorkspace
from mantid.simpleapi import (
    CreateWorkspace,
    DeleteWorkspace,
    LoadGSS,
    Plus,
    SaveGSS,
    mtd,
)

from vnext import Config, FilePath
from vnext.fileservice import get_bins_in_range


def load_gss(gda_file: FilePath, ws_name: str) -> MatrixWorkspace:
    """Load a VULCAN-style GSAS file into a Mantid workspace"""

    LoadGSS(Filename=str(gda_file), OutputWorkspace=ws_name)
    return mtd[ws_name]


def save_gss(ws_name: str, output_file: FilePath) -> str:
    """Write *ws_name* to a VULCAN-style GSAS file and return the output path."""

    SaveGSS(
        InputWorkspace=ws_name,
        Filename=str(output_file),
        SplitFiles=False,
        Append=False,
        Format="SLOG",
        MultiplyByBinWidth=False,
        ExtendedHeader=True,
        UseSpectrumNumberAsBankID=True,
    )
    return str(output_file)


def banks_from_workspace(ws: MatrixWorkspace) -> list[dict[str, Any]]:
    """Extract per-bank centre-x / intensity arrays from a loaded GSAS workspace.

    Each entry is ``{"bank": <1-based id>, "x": <bin centres>, "y": <intensity>}``.
    The workspace is left intact (the caller owns its lifecycle).
    """
    banks = []
    for spec in range(ws.getNumberHistograms()):
        x = ws.readX(spec)
        y = ws.readY(spec)
        # GSAS histograms carry bin edges; use centres so x and y align.
        centres = 0.5 * (x[:-1] + x[1:]) if len(x) == len(y) + 1 else x.copy()
        banks.append({"bank": spec + 1, "x": np.asarray(centres), "y": y.copy()})
    return banks


def read_gsas_banks(gda_file: FilePath) -> list[dict[str, Any]]:
    """Load a GSAS file and return its per-bank centre-x / intensity arrays."""
    ws_name = f"vnextview_{Path(gda_file).stem}"
    ws = load_gss(gda_file, ws_name)
    banks = banks_from_workspace(ws)
    DeleteWorkspace(ws_name)
    return banks


@contextmanager
def pattern_workspace(gda_file: FilePath, *, title: str = ""):
    """Load a single GSAS file as a workspace for plotting, deleting it on exit.

    Yields the ``LoadGSS`` workspace (one spectrum per bank) so the plotting
    layer can draw it through the ``mantid`` projection.  An optional ``title``
    is stamped on the workspace for use as the plot title.
    """
    ws_name = f"vnextview_{Path(gda_file).stem}"
    ws = load_gss(gda_file, ws_name)
    if title:
        ws.setTitle(title)
    try:
        yield ws
    finally:
        if ws_name in mtd:
            DeleteWorkspace(ws_name)


@contextmanager
def sequential_view_workspaces(view: dict[str, Any]):
    """Build one 2-D workspace per bank from a sequential view, deleting on exit.

    ``view`` is the dict returned by :func:`build_sequential_view`.  Each bank's
    ``intensity`` grid (runs x x) becomes a workspace with one spectrum per run
    and the run numbers on a ``Label`` vertical axis, ready for ``pcolormesh``.
    Yields the list of workspaces.
    """
    runs = [str(r) for r in view["runs_present"]]
    names = []
    workspaces = []
    try:
        for bank in view["banks"]:
            ws_name = f"vnextview_seq_bank{bank['bank']}"
            x = np.asarray(bank["x"], dtype=float)
            intensity = np.asarray(bank["intensity"], dtype=float)
            ws = CreateWorkspace(
                DataX=np.tile(x, len(runs)),
                DataY=intensity.ravel(),
                NSpec=len(runs),
                UnitX="TOF",
                VerticalAxisUnit="Label",
                VerticalAxisValues=runs,
                OutputWorkspace=ws_name,
            )
            ws.setTitle(f"bank {bank['bank']}")
            names.append(ws_name)
            workspaces.append(ws)
        yield workspaces
    finally:
        for ws_name in names:
            if ws_name in mtd:
                DeleteWorkspace(ws_name)


def build_sequential_view(ipts: int, runs: int, rune: int) -> dict[str, Any]:
    """Assemble sequential-view data: per-bank 2-D intensity grids over a run range.

    Missing runs in the range are skipped.  Each bank carries the shared ``x``
    axis, the list of runs present, and an ``intensity`` grid of shape
    ``(n_runs, n_xbins)``.
    """

    run_files = get_bins_in_range(ipts, runs, rune)
    runs_present = sorted(run_files.keys())
    if not runs_present:
        raise FileNotFoundError(f"No GSAS files found for runs {runs}-{rune} in IPTS {ipts}")

    per_run = {r: read_gsas_banks(run_files[r]) for r in runs_present}
    first = per_run[runs_present[0]]
    banks = []
    for i, bank in enumerate(first):
        intensity = np.vstack([per_run[r][i]["y"] for r in runs_present])
        banks.append({"bank": bank["bank"], "x": bank["x"], "runs": runs_present, "intensity": intensity})

    return {"ipts": ipts, "runs": runs, "rune": rune, "runs_present": runs_present, "banks": banks}


def sum_gss_files(
    ipts: int,
    runs: int,
    rune: int,
    runlist: list[int] | None = None,
    runfile: FilePath | None = None,
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
    """

    binned_dir = Path(Config["instrument.reduction.bin"].format(IPTS=ipts))
    assert binned_dir.exists(), f"Input directory does not exist: {binned_dir}"

    if runlist is not None:
        runs = min(runlist)
        rune = max(runlist)
    elif runfile:
        file_runs = [int(tok) for tok in Path(runfile).read_text().split()]
        runs = min(file_runs)
        rune = max(file_runs)

    output_dir = Path(Config["instrument.reduction.sum"].format(IPTS=ipts))
    output_dir.mkdir(parents=True, exist_ok=True)

    run_numbers = get_bins_in_range(ipts, runs, rune)
    if not run_numbers:
        return {"output": str(output_dir)}

    sum_ws = "vnextsum_accumulator"
    first_run = None
    n_summed = 0
    for run, bin_file in run_numbers.items():
        if first_run is None:
            first_run = run
            load_gss(bin_file, sum_ws)
        else:
            load_ws = f"vnext_sum_{run}"
            load_gss(bin_file, load_ws)
            Plus(LHSWorkspace=sum_ws, RHSWorkspace=load_ws, OutputWorkspace=sum_ws)
            DeleteWorkspace(load_ws)
        n_summed += 1

    output_file = output_dir / f"{first_run}.gda"
    save_gss(sum_ws, output_file)
    if sum_ws in mtd:
        DeleteWorkspace(sum_ws)

    return {"output": str(output_file)}
