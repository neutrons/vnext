"""Contains the entry point for the application"""

from importlib import metadata

from mantid.kernel import Property

UNSET_FLOAT: float = Property.EMPTY_DBL
del Property

from .configuration import Configuration  # noqa: E402, F401
from .vnext_protocol import VNEXTBackend  # noqa: E402, F401

__version__ = metadata.version("vnext")
del metadata


def VNext():  # noqa N802
    """This is needed for backward compatibility because mantid workbench does "from shiver import Shiver" """
    from .vnext import VNext as vnext  # noqa N813

    return vnext()
