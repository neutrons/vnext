"""GSAS file reading utilities.

Helpers that turn binned ``.gda`` files into plain per-bank data structures.
Kept out of ``backend.py`` so the backend methods stay thin and the Mantid
``LoadGSS`` plumbing lives in one place.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any

from mantid.api import MatrixWorkspace, TextAxis
from mantid.simpleapi import (
    ConjoinWorkspaces,
    DeleteWorkspace,
    ExtractSingleSpectrum,
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


@contextmanager
def pattern_workspace(gda_file: FilePath, *, title: str = ""):
    """Load a single GSAS file as a workspace for plotting, deleting it on exit.

    Yields the ``LoadGSS`` workspace (one spectrum per bank) so the plotting
    layer can draw it through the ``mantid`` projection.  An optional ``title``
    is stamped on the workspace for use as the plot title.
    """
    ws_name = mtd.unique_name(prefix=f"__vnextview_{Path(gda_file).stem}")
    ws = load_gss(gda_file, ws_name)
    if title:
        ws.setTitle(title)
    try:
        yield ws
    finally:
        if ws_name in mtd:
            DeleteWorkspace(ws_name)


@contextmanager
def sequential_view_workspaces(ipts: int, runs: int, rune: int):
    """Build one 2-D workspace per bank over a run range, deleting on exit.

    Each present run's GSAS file is loaded and its banks split out with
    ``ExtractSingleSpectrum``; the per-run single-bank workspaces are stacked
    with ``ConjoinWorkspaces`` so each bank becomes one workspace with one
    spectrum per run.  Missing runs in the range are skipped.  The run numbers
    go on a text vertical axis, ready for ``pcolormesh``.  Yields
    ``(runs_present, workspaces)``.
    """

    run_files = get_bins_in_range(ipts, runs, rune)
    runs_present = sorted(run_files.keys())
    if not runs_present:
        raise FileNotFoundError(f"No GSAS files found for runs {runs}-{rune} in IPTS {ipts}")

    bank_names: list[str] = []
    run_ws_name = ""
    spectrum_name = ""
    try:
        for run in runs_present:
            run_ws_name = mtd.unique_name(prefix=f"__vnextview_seq_{run}")
            run_ws = load_gss(run_files[run], run_ws_name)
            if not bank_names:
                # First run: each extracted bank spectrum seeds a bank workspace.
                bank_names = [f"vnextview_seq_bank{i + 1}" for i in range(run_ws.getNumberHistograms())]
                for i, bank_name in enumerate(bank_names):
                    ExtractSingleSpectrum(InputWorkspace=run_ws_name, WorkspaceIndex=i, OutputWorkspace=bank_name)
            else:
                for i, bank_name in enumerate(bank_names):
                    spectrum_name = mtd.unique_name(prefix=f"__vnextview_seq_{run}_bank{i + 1}")
                    ExtractSingleSpectrum(InputWorkspace=run_ws_name, WorkspaceIndex=i, OutputWorkspace=spectrum_name)
                    # Appends the spectrum to the bank workspace and removes the
                    # second workspace from the ADS.
                    ConjoinWorkspaces(InputWorkspace1=bank_name, InputWorkspace2=spectrum_name, CheckOverlapping=False)
            DeleteWorkspace(run_ws_name)

        workspaces = []
        for i, bank_name in enumerate(bank_names):
            ws = mtd[bank_name]
            axis = TextAxis.create(len(runs_present))
            for j, run in enumerate(runs_present):
                axis.setLabel(j, str(run))
            ws.replaceAxis(1, axis)
            ws.setTitle(f"bank {i + 1}")
            workspaces.append(ws)
        yield runs_present, workspaces
    finally:
        for ws_name in (run_ws_name, spectrum_name, *bank_names):
            if ws_name and ws_name in mtd:
                DeleteWorkspace(ws_name)


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
            load_ws = mtd.unique_name(prefix=f"__vnext_sum_{run}")
            load_gss(bin_file, load_ws)
            Plus(LHSWorkspace=sum_ws, RHSWorkspace=load_ws, OutputWorkspace=sum_ws)
            DeleteWorkspace(load_ws)
        n_summed += 1

    output_file = output_dir / f"{first_run}.gda"
    save_gss(sum_ws, output_file)
    if sum_ws in mtd:
        DeleteWorkspace(sum_ws)

    return {"output": str(output_file)}
