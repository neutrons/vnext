"""Plotting layer for VNEXT.

Backend methods return plain data (numpy arrays / dicts); this module turns that
data into figures.  Keeping rendering here — rather than inside ``Backend`` —
means the data path stays import-light and unit-testable, and the plotting code
can be exercised (or swapped for a GUI/headless backend) independently.

Each function accepts an optional ``ax`` (to compose into an existing figure) and
a ``show`` flag, and returns the ``Axes`` it drew on.
"""

from __future__ import annotations

from typing import Any


def plot_log(log: dict[str, Any], *, ax=None, show: bool = False):
    """Plot a single sample-environment log as a time series.

    Expects the dict shape returned by ``Backend.vnextlog`` for a named log:
    ``time`` (elapsed seconds), ``value``, and optional ``units``/``time_units``
    and ``name`` for axis labelling.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots()

    ax.plot(log["time"], log["value"])
    time_units = log.get("time_units") or "s"
    ax.set_xlabel(f"time ({time_units})")
    ylabel = log.get("name", "value")
    if log.get("units"):
        ylabel = f"{ylabel} ({log['units']})"
    ax.set_ylabel(ylabel)
    ax.set_title(f"IPTS-{log.get('ipts', '?')} run {log.get('run', '?')}: {log.get('name', '')}")

    if show:
        plt.show()
    return ax


def plot_pattern(view: dict[str, Any], *, ax=None, show: bool = False):
    """Plot a single run's GSAS pattern, overlaying each bank.

    Expects the dict shape ``Backend.vnextview`` returns for a single run:
    ``banks`` is a list of ``{"bank", "x", "y"}``.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots()

    for bank in view["banks"]:
        ax.plot(bank["x"], bank["y"], label=f"bank {bank['bank']}")
    ax.set_xlabel("TOF")
    ax.set_ylabel("intensity")
    ax.set_title(f"IPTS-{view.get('ipts', '?')} run {view.get('runs', '?')}")
    ax.legend()

    if show:
        plt.show()
    return ax


def plot_pixel(pixel: dict[str, Any], *, ax=None, show: bool = False):
    """Plot a single run's per-pixel detector counts as a scattering-angle map.

    Expects the dict shape ``Backend.vnextpixel`` returns: ``counts`` coloured
    over each pixel's ``azimuthal`` / ``two_theta`` angle (degrees).
    """
    import matplotlib.pyplot as plt

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


def plot_contour(view: dict[str, Any], *, show: bool = False):
    """Plot sequential-run intensity as a 2-D contour, one subplot per bank.

    Expects the dict shape ``Backend.vnextview`` returns for a run range:
    each bank carries ``x``, ``runs`` and a 2-D ``intensity`` grid (runs x x).
    Returns the list of axes drawn.
    """
    import matplotlib.pyplot as plt

    banks = view["banks"]
    _, axes = plt.subplots(1, len(banks), squeeze=False)
    drawn = []
    for ax, bank in zip(axes[0], banks):
        ax.contourf(bank["x"], bank["runs"], bank["intensity"])
        ax.set_xlabel("TOF")
        ax.set_ylabel("run")
        ax.set_title(f"bank {bank['bank']}")
        drawn.append(ax)

    if show:
        plt.show()
    return drawn
