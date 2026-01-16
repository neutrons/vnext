"""Contains the entry point for the application"""

from importlib import metadata

__version__ = metadata.version("vnext")
del metadata


def VNext():  # noqa N802
    """This is needed for backward compatibility because mantid workbench does "from shiver import Shiver" """
    from .vnext import VNext as vnext  # noqa N813

    return vnext()
