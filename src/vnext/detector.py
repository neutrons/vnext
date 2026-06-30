"""Detector-view helpers for the per-pixel diagnostic (``vnextpixel``).

Loads raw event data for a run and reduces it to per-pixel total counts plus
each pixel's physical scattering angles, so the plotting layer can render a
detector contour.  Kept out of ``backend.py`` so the Mantid plumbing lives in
one place.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from mantid.simpleapi import (
    DeleteWorkspace,
    LoadEventAsWorkspace2D,
    PreprocessDetectorsToMD,
    mtd,
)


def extract_pixel_data(ws_name: str) -> dict[str, Any]:
    """Reduce an integrated event workspace to per-pixel counts and angles.

    ``ws_name`` is expected to reference a workspace loaded via
    ``LoadEventAsWorkspace2D``, which already holds a single integrated bin per
    detector pixel.  Returns ``counts`` (total counts per detector pixel)
    alongside each pixel's ``two_theta`` and ``azimuthal`` angle in degrees.
    """

    counts = mtd[ws_name].extractY().ravel()

    detectors = PreprocessDetectorsToMD(InputWorkspace=ws_name, OutputWorkspace=f"{ws_name}_det")
    two_theta = np.degrees(np.asarray(detectors.column("TwoTheta")))
    azimuthal = np.degrees(np.asarray(detectors.column("Azimuthal")))

    DeleteWorkspace(detectors)

    return {"counts": counts, "two_theta": two_theta, "azimuthal": azimuthal}


def pixel_counts(nexus_file: Path) -> dict[str, Any]:
    """Load a run's raw events as an integrated Workspace2D and return its
    per-pixel detector data."""
    ws_name = f"vnextpixel_{nexus_file.stem}"
    # Integrate all events into a single TOF bin per pixel.  The X-bin value is
    # irrelevant for the detector contour, so set it explicitly rather than
    # reading the default 'wavelength' log, which VULCAN files do not carry.
    LoadEventAsWorkspace2D(
        Filename=str(nexus_file),
        OutputWorkspace=ws_name,
        Units="TOF",
        XCenter=1.0,
        XWidth=1.0,
    )
    data = extract_pixel_data(ws_name)
    DeleteWorkspace(ws_name)
    return data
