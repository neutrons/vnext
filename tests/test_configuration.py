from pathlib import Path

from vnext import Configuration


def test_config():
    config = Configuration()
    assert config
    assert config.get_calibration_path()


def test_config_override():
    config = Configuration(**{"Paths.calibration": Path("/tmp/calibration")})

    assert config.get_calibration_path() == Path("/tmp/calibration")
