from pathlib import Path

import pytest

from vnext import Configuration

TESTS_DIR = Path(__file__).parent


def test_config_defaults():
    # With VNEXT_CONFIG set by conftest, calibration home is redirected to tests/data
    config = Configuration()
    assert config.get_calibration_path() == TESTS_DIR / "data"


def test_config_substitution():
    # ${IPTS.root} and ${facility.root} should resolve to the same value
    config = Configuration()
    assert config["IPTS.root"] == config["facility.root"]


def test_config_instrument_home():
    # In the test environment, instrument.home is overridden to tests/data/vulcan
    config = Configuration()
    assert "vulcan" in config["instrument.home"].lower()


def test_config_nexus_keys():
    config = Configuration()
    assert config["instrument.nexus.native.extension"] == ".nxs.h5"
    assert "VULCAN_" in config["instrument.nexus.native.prefix"]


def test_config_pvlogs():
    config = Configuration()
    assert config["instrument.PVLogs.rootGroup"] == "/entry/DASlogs"
    # wavelength is now a list of alternatives; first entry is the preferred name
    wavelength_keys = config["instrument.PVLogs.choppers.skf34.wavelength"]
    assert isinstance(wavelength_keys, list)
    assert wavelength_keys[0] == "BL7:Chop:Skf34:CenterWavelength"
    assert "skf34.lambda" in wavelength_keys


def test_config_missing_key():
    config = Configuration()
    with pytest.raises(KeyError):
        _ = config["does.not.exist"]


def test_config_get_default():
    config = Configuration()
    assert config.get("does.not.exist", "fallback") == "fallback"


def test_config_singleton():
    assert Configuration() is Configuration()


def test_config_explicit_override(tmp_path):
    override = tmp_path / "override.yml"
    override.write_text("instrument:\n  calibration:\n    home: /custom/path\n")
    config = Configuration(config_path=override)
    try:
        assert config.get_calibration_path().as_posix() == "/custom/path"
        # Rebuilding without a path returns the same (now-updated) singleton
        assert Configuration() is config
    finally:
        # Restore for subsequent tests
        Configuration.reset()


def test_config_project_root_injected():
    config = Configuration()
    root = Path(config["project.root"])
    assert root.exists()
    assert (root / "src" / "vnext").exists()
