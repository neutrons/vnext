"""Main Qt application"""

import sys

from mantid.kernel import Logger

# make sure the algorithms have been loaded so they are available to the AlgorithmManager
import mantid.simpleapi  # noqa: F401, E402 pylint: disable=unused-import, wrong-import-position

from vnext import __version__  # noqa: E402 pylint: disable=wrong-import-position
from vnext.configuration import Configuration  # noqa: E402 pylint: disable=wrong-import-position

logger = Logger("VNEXT")

class VNext:
    """Main Package window"""

    def __init__(self):
        logger.information(f"VNext version: {__version__}")
        config = Configuration()

        if not config.is_valid():
            msg = (
                "Error with configuration settings!",
                f"Check and update your file: {config.config_file_path}",
                "with the latest settings found here:",
                f"{config.template_file_path} and start the application again.",
            )

            print(" ".join(msg))
            sys.exit(-1)
        print(f"VNEXT - {__version__}")


def gui():
    """Main entry point for Qt application"""
    input_flags = sys.argv[1::]
    if "--v" in input_flags or "--version" in input_flags:
        print(__version__)
        sys.exit()
    else:
        VNext()
        sys.exit()
