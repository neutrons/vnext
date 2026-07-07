"""Plotting layer for VNEXT.

Rendering is kept here rather than inside ``Backend`` so the data path stays
testable and the plotting code can be exercised (or swapped for a headless
backend) independently.

These functions draw Mantid workspaces directly through Mantid's matplotlib
integration (the ``mantid`` projection), so axis units, bin-edge handling,
error bars and sample-log slicing come from the workspace itself rather than
being reconstructed by hand.  See
https://docs.mantidproject.org/nightly/plotting/index.html.

Each function accepts an optional ``ax`` (to compose into an existing figure)
and a ``show`` flag, and returns the ``Axes`` it drew on.  A supplied ``ax``
must already use the ``mantid`` projection.
"""

from __future__ import annotations

import math
from typing import Any

import matplotlib.pyplot as plt
from mantid import plots  # noqa: F401  (registers the 'mantid' projection)
from matplotlib.colors import LogNorm

# plot_contour lays banks out in a grid this many subplots wide.
CONTOUR_GRID_NCOLS = 3


def _mantid_subplots(**kwargs):
    """Return ``(fig, ax)`` (or axes array) using the ``mantid`` projection.

    Importing ``mantid.plots`` registers the projection with matplotlib.
    """

    subplot_kw = kwargs.pop("subplot_kw", {})
    subplot_kw.setdefault("projection", "mantid")
    return plt.subplots(subplot_kw=subplot_kw, **kwargs)


def plot_log(workspace, name: str, *, ax=None, show: bool = False, full_time: bool = False):
    """Plot a single sample-environment log as a time series.

    ``workspace`` is a Mantid workspace carrying the run's logs (e.g. loaded
    metadata-only via ``LoadEventNexus``).  The log named ``name`` is drawn with
    Mantid's log-slicing support, so axis labels and units come from the log
    itself.  ``full_time`` switches the x-axis from elapsed seconds to absolute
    time.
    """

    if ax is None:
        _, ax = _mantid_subplots()

    ax.plot(workspace, LogName=name, FullTime=full_time)

    if show:
        plt.show()
    return ax


def plot_pattern(workspace, *, ax=None, show: bool = False):
    """Plot a single run's GSAS pattern, overlaying each bank.

    ``workspace`` is the ``LoadGSS`` workspace; each spectrum is one bank.
    Drawing through the ``mantid`` projection takes the x unit (TOF / d-spacing)
    and bin-centre handling from the workspace.  The figure title is taken from
    the workspace title if one is set.
    """

    if ax is None:
        _, ax = _mantid_subplots()

    for spec in range(workspace.getNumberHistograms()):
        ax.plot(workspace, specNum=spec + 1, label=f"bank {spec + 1}")
    title = workspace.getTitle()
    if title:
        ax.set_title(title)
    ax.legend()

    if show:
        plt.show()
    return ax


def plot_contour(workspaces, *, show: bool = False):
    """Plot sequential-run intensity as a 2-D colour map, one subplot per bank.

    ``workspaces`` is a list of 2-D Mantid workspaces (one per bank), each with
    runs along the vertical axis.  The x unit comes from the workspace; the run
    axis is ticked with the run numbers but carries no axis label, matching the
    VDRIVE convention; intensity is shown by the colour bar.  Banks are laid out in a grid ``CONTOUR_GRID_NCOLS``
    wide.  Intensity is colour-mapped on a log scale (diffraction peaks span
    orders of magnitude, so a linear scale washes out to near-uniform blocks);
    banks with no positive counts fall back to a linear scale and are flagged
    "(no data)".  Returns the list of axes drawn.
    """

    ncols = min(CONTOUR_GRID_NCOLS, len(workspaces))
    nrows = math.ceil(len(workspaces) / ncols)
    fig, axes = _mantid_subplots(
        nrows=nrows,
        ncols=ncols,
        squeeze=False,
        figsize=(4.0 * ncols, 3.0 * nrows),
        layout="constrained",
    )
    flat = axes.ravel()
    drawn = []
    for ax, ws in zip(flat, workspaces):
        title = ws.getTitle()
        intensity = ws.extractY()
        positive = intensity[intensity > 0]
        # Mantid's pcolormesh inspects the norm kwarg if present, so only pass
        # it when there is a log scale to apply.
        mesh_kwargs = {}
        if positive.size:
            mesh_kwargs["norm"] = LogNorm(vmin=positive.min(), vmax=positive.max())
        else:
            title = f"{title} (no data)" if title else "(no data)"
        mesh = ax.pcolormesh(ws, **mesh_kwargs)
        ax.set_ylabel("")
        # A text vertical axis carries the run numbers, but Mantid places the
        # rows at indices 0..n-1 and leaves the ticks as row coordinates, so
        # relabel them with the run numbers (thinned to stay readable).
        vertical_axis = ws.getAxis(1)
        if vertical_axis.isText():
            n_runs = vertical_axis.length()
            step = max(1, math.ceil(n_runs / 10))
            ax.set_yticks(range(0, n_runs, step))
            ax.set_yticklabels([vertical_axis.label(j) for j in range(0, n_runs, step)])
        if title:
            ax.set_title(title)
        fig.colorbar(mesh, ax=ax, label="intensity")
        drawn.append(ax)
    for ax in flat[len(workspaces) :]:
        fig.delaxes(ax)

    if show:
        plt.show()
    return drawn


def plot_pixel(pixel: dict[str, Any], *, ax=None, show: bool = False):
    """Plot a single run's per-pixel detector counts as a scattering-angle map.

    This stays array-based: it scatters ``counts`` over each pixel's
    ``azimuthal`` / ``two_theta`` angle (degrees), for which Mantid's matplotlib
    projection has no equivalent (per-detector angle maps are instrument-view
    territory, not an ``Axes`` primitive).  Expects the dict shape
    ``Backend.vnextpixel`` returns.
    """

    if ax is None:
        _, ax = plt.subplots()

    scatter = ax.scatter(pixel["azimuthal"], pixel["two_theta"], c=pixel["counts"])
    ax.set_xlabel("azimuthal (deg)")
    ax.set_ylabel("2theta (deg)")
    ax.set_title(f"IPTS-{pixel.get('ipts', '?')} run {pixel.get('run', '?')}: pixel counts")
    ax.figure.colorbar(scatter, ax=ax, label="counts")

    if show:
        plt.show()
    return ax
