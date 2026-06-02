"""Contains the entry point for the application"""

from importlib import metadata

from .configuration import Configuration  # noqa: F401
from .vnext_protocol import VNEXTBackend, unset_float  # noqa: F401

__version__ = metadata.version("vnext")
del metadata


def VNext():  # noqa N802
    """This is needed for backward compatibility because mantid workbench does "from shiver import Shiver" """
    from .vnext import VNext as vnext  # noqa N813

    return vnext()
