import pytest
from numpy import testing as nptest

from vnext.calibration import FocusPositions, get_focuspositions_from_char_file


def test_focuspos():
    # intentionally pass all parameters with the wrong type for the values
    fp = FocusPositions(l1=1.0, l2=[1, 2], polar=[3, 4], azimuthal=[5, 6])
    assert fp
    assert fp.l1 == 1.0
    assert fp.l2 == [1.0, 2.0]
    assert fp.polar == [3.0, 4.0]
    assert fp.azimuthal == [5.0, 6.0]
    assert fp.specnum == [1, 2]

    # intentionally pass all parameters with the wrong type for the values
    fp = FocusPositions(l1=1.0, l2=[1, 2], polar=[3, 4], azimuthal=[5, 6], specnum=[7.0, 8.0])
    assert fp
    assert fp.l1 == 1.0
    assert fp.l2 == [1.0, 2.0]
    assert fp.polar == [3.0, 4.0]
    assert fp.azimuthal == [5.0, 6.0]
    assert fp.specnum == [7, 8]


def test_focuspos_not_parallel():
    with pytest.raises(ValueError):
        _ = FocusPositions(l1=1.0, l2=[1], polar=[3, 4], azimuthal=[5, 6])

    with pytest.raises(ValueError):
        _ = FocusPositions(l1=1.0, l2=[1, 2], polar=[3], azimuthal=[5, 6])

    with pytest.raises(ValueError):
        _ = FocusPositions(l1=1.0, l2=[1, 2], polar=[3, 4], azimuthal=[5, 6], specnum=[7, 8, 9])


def test_get_focuspos_from_char_file():
    # TODO be resilient about file path
    fp = get_focuspositions_from_char_file("tests/data/VULCAN_Characterization_3Banks_v2.txt")
    nptest.assert_allclose(fp.l1, 43.755)
    nptest.assert_allclose(fp.l2, (2.296492906, 2.296492906, 1.999243))
    nptest.assert_allclose(fp.polar, (89.9260985, 89.9260985, 149.8646347))
    nptest.assert_allclose(fp.azimuthal, (0, 0, 0))
    assert fp.specnum == [1, 2, 3]
