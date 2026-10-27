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

# When plot_pattern/plot_contour open one figure window per bank, cascade
# each successive window this many pixels down and to the right so the
# corner of every window underneath stays visible.
CASCADE_OFFSET_PX = 40


def _mantid_subplots(**kwargs):
    """Return ``(fig, ax)`` (or axes array) using the ``mantid`` projection.

    Importing ``mantid.plots`` registers the projection with matplotlib.
    """

    subplot_kw = kwargs.pop("subplot_kw", {})
    subplot_kw.setdefault("projection", "mantid")
    return plt.subplots(subplot_kw=subplot_kw, **kwargs)


def _cascade_figures(axes, *, offset: int = CASCADE_OFFSET_PX):
    """Best-effort cascade each axes' figure window so lower ones peek out.

    Each successive window is moved ``offset`` pixels down and to the right,
    so that every window is visible.
    """

    first_window = getattr(axes[0].figure.canvas.manager, "window", None) if axes else None
    if first_window is None:
        return  # unsupported backend; leave default placement alone

    for i, ax in enumerate(axes):
        window = getattr(ax.figure.canvas.manager, "window", None)
        if window is None:
            continue
        x, y = i * offset, i * offset
        if hasattr(window, "move"):
            window.move(x, y)
        elif hasattr(window, "wm_geometry"):
            window.wm_geometry(f"+{x}+{y}")


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


def plot_pattern(workspace, *, show: bool = False):
    """Plot a single run's GSAS pattern, one bank per figure window.

    ``workspace`` is the ``LoadGSS`` workspace; each spectrum is one bank.
    Drawing through the ``mantid`` projection takes the x unit (TOF / d-spacing)
    and bin-centre handling from the workspace.

    Each bank opens in its own figure window.

    Banks with no positive counts are skipped.
    """

    title = workspace.getTitle()
    axes = []
    for spec in range(workspace.getNumberHistograms()):
        if not (workspace.readY(spec) > 0).any():
            continue
        _, ax = _mantid_subplots()
        ax.plot(workspace, specNum=spec + 1)
        ax.set_ylabel("Intensity")
        ax.set_title(f"{title} - bank {spec + 1}" if title else f"bank {spec + 1}")
        axes.append(ax)

    _cascade_figures(axes)
    if show:
        plt.show()
    return axes


def plot_contour(workspaces, *, show: bool = False):
    """Plot sequential-run intensity as a 2-D colour map, one figure window per bank.

    ``workspaces`` is a list of 2-D Mantid workspaces (one per bank), each with
    runs along the vertical axis.  The x unit comes from the workspace; the run
    axis is ticked with the run numbers but carries no axis label, matching the
    VDRIVE convention; intensity is shown by the colour bar.

    Each bank opens in its own figure window.

    Banks with no positive counts are skipped.
    """

    drawn = []
    for ws in workspaces:
        intensity = ws.extractY()
        positive = intensity[intensity > 0]
        if not positive.size:
            continue
        fig, ax = _mantid_subplots(layout="constrained")
        title = ws.getTitle()
        # Mantid's pcolormesh inspects the norm kwarg if present, so only pass
        # it when there is a log scale to apply.
        mesh_kwargs = {"norm": LogNorm(vmin=positive.min(), vmax=positive.max())}
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

    _cascade_figures(drawn)
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
