"""Unit tests for vnext.detector — per-pixel detector data extraction.

``extract_pixel_data`` is exercised against a small in-memory event workspace
(via CreateSampleWorkspace) so the real Mantid reduction runs without loading a
full VULCAN event file.
"""

import numpy as np
import pytest

from vnext.detector import extract_pixel_data


@pytest.fixture
def sample_event_ws():
    """A small 2-bank event workspace; yields its name and cleans up."""
    from mantid.simpleapi import (
        CreateSampleWorkspace,
        DeleteWorkspace,
        mtd,
    )

    name = "test_detector_ws"
    CreateSampleWorkspace(
        WorkspaceType="Event",
        NumBanks=2,
        BankPixelWidth=3,
        OutputWorkspace=name,
    )
    yield name
    for ws in (name, f"{name}_int", f"{name}_det"):
        if ws in mtd:
            DeleteWorkspace(ws)


def test_extract_pixel_data_keys_and_lengths(sample_event_ws):
    data = extract_pixel_data(sample_event_ws)

    assert set(data) == {"counts", "two_theta", "azimuthal"}
    # 2 banks x 3x3 pixels = 18 detectors; all arrays align one-per-pixel.
    assert len(data["counts"]) == 18
    assert len(data["two_theta"]) == 18
    assert len(data["azimuthal"]) == 18


def test_extract_pixel_data_returns_arrays(sample_event_ws):
    data = extract_pixel_data(sample_event_ws)

    for key in ("counts", "two_theta", "azimuthal"):
        assert isinstance(data[key], np.ndarray)


def test_extract_pixel_data_angles_in_degrees(sample_event_ws):
    """Angles are converted to degrees, so 2theta spans a plausible range."""
    data = extract_pixel_data(sample_event_ws)

    assert np.all(data["two_theta"] >= 0.0)
    assert np.all(data["two_theta"] <= 180.0)


def test_extract_pixel_data_cleans_up_workspaces(sample_event_ws):
    from mantid.simpleapi import mtd

    extract_pixel_data(sample_event_ws)
    # the intermediate integration / detector workspaces are removed
    assert f"{sample_event_ws}_int" not in mtd
    assert f"{sample_event_ws}_det" not in mtd
