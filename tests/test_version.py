from vnext import __version__


def test_version():
    assert "rc" in __version__ or "dev" in __version__ or "0.1.0" in __version__
