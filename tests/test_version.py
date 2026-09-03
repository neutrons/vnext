import re

from vnext import __version__

# PEP 440-style version produced by versioningit, e.g. "0.2.0", "0.2.0rc1",
VERSION_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)"
    r"(?:\.(?P<patch>0|[1-9]\d*))?"
    r"(?P<prerelease>(?:rc|a|b)\d*)?"
    r"(?:\.?(?P<dev>dev\d+))?$"
)


def is_pep440_compliant(version_str):
    return VERSION_RE.fullmatch(version_str) is not None


def test_valid_versions():
    valid_versions = ["0.2.0rc1", "1.0.0", "1.5.6a12", "2.0.3rc5", "1.4dev5", "16.2.3"]
    for v in valid_versions:
        assert is_pep440_compliant(v), f"Expected {v} to be valid"


def test_invalid_versions():
    invalid_versions = [
        "01.2.3",
        "1.2.3.4",
        "1.2-beta",
        "1.3+",
        "1.4#dev",
        "1.1.0.rc2",
        "1.0.0.dev",
        "1.0.0.dev20260831191257extra",
    ]
    for v in invalid_versions:
        assert not is_pep440_compliant(v), f"Expected {v} to be invalid"


def test_version():
    assert __version__ == "unknown" or is_pep440_compliant(__version__), (
        f"__version__={__version__!r} is not a valid version string"
    )
