from pathlib import Path

import pytest

from vnext import Config

TESTS_DIR = Path(__file__).parent


def test_config_defaults():
    # In the test environment ${module.root} resolves to the tests/ directory, so
    # calibration home is redirected to tests/data by tests/resources/test.yml.
    assert Path(Config["instrument.calibration.home"]) == TESTS_DIR / "data"


def test_config_substitution():
    # ${IPTS.root} and ${facility.root} should resolve to the same value
    assert Config["IPTS.root"] == Config["facility.root"]


def test_config_instrument_home():
    # In the test environment, instrument.home is overridden to tests/data/vulcan
    assert "vulcan" in Config["instrument.home"].lower()


def test_config_nexus_keys():
    assert Config["instrument.nexus.native.extension"] == ".nxs.h5"
    assert "VULCAN_" in Config["instrument.nexus.native.prefix"]


def test_config_pvlogs():
    assert Config["instrument.PVLogs.rootGroup"] == "/entry/DASlogs"
    # wavelength is a list of alternatives; first entry is the preferred name
    wavelength_keys = Config["instrument.PVLogs.choppers.skf34.wavelength"]
    assert isinstance(wavelength_keys, list)
    assert wavelength_keys[0] == "BL7:Chop:Skf34:CenterWavelength"
    assert "skf34.lambda" in wavelength_keys


def test_config_missing_key():
    with pytest.raises(KeyError):
        _ = Config["does.not.exist"]


def test_config_module_root_injected():
    # neutrons_standard injects module.root; in the test environment it is tests/.
    root = Path(Config["module.root"])
    assert root.exists()
    assert root.name == "tests"


def test_config_override(config_override):
    config_override("instrument.calibration.home", "/custom/path")
    assert Config["instrument.calibration.home"] == "/custom/path"
