"""Contains the entry point for the application"""

from importlib import metadata

import neutrons_standard
from mantid.kernel import Property

UNSET_FLOAT: float = Property.EMPTY_DBL
del Property

# Register this package with neutrons_standard before importing Config.  Config is a
# singleton that loads vnext/resources/application.yml on first import, and it needs to
# know the client package name to locate those resources.
neutrons_standard.init("vnext")
from neutrons_standard.config import Config  # noqa: E402

from ._typing import FilePath  # noqa: E402
from .vnext_protocol import VNEXTBackend  # noqa: E402

__version__ = metadata.version("vnext")
del metadata

__all__ = ["Config", "FilePath", "VNEXTBackend", "VNext", "UNSET_FLOAT", "__version__"]


def VNext():  # noqa N802
    """This is needed for backward compatibility because mantid workbench does "from shiver import Shiver" """
    from vnext import VNext as vnext  # noqa N813

    return vnext()
