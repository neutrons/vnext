"""Module to load the the settings from SHOME/.packagename/configuration.ini file

Will fall back to a default
"""

from configparser import ConfigParser
from pathlib import Path

from mantid.kernel import Logger

from vnext._typing import FilePath

# configuration settings file path - this is where linux puts things by default
CONFIG_PATH_USER: Path = Path.home() / ".config" / "vnext" / "configuration.ini"


class Configuration(ConfigParser):
    """Load and validate Configuration Data"""

    _log = Logger("vnext.Configuration")

    def __init__(self, filename: FilePath = CONFIG_PATH_USER, **kwargs):
        """Initialization of configuration mechanism
        :param filename: path to the configuration file, defaults to CONFIG_PATH_USER
        :param kwargs: optional overrides for configuration values, in the form of section.key=value"""
        ConfigParser.__init__(self)
        if Path(filename).exists():
            self._log.debug(f"Loading configuration from {filename}")
            self.read(filename)
        else:
            self._log.debug(f"Configuration {filename} does not exist, loading defaults")

        # override with provided kwargs in the form of section.key=value
        for key, value in kwargs.items():
            section, key = key.split(".", 1)
            self._log.debug(f"Overriding configuration: {section} {key}={value}")
            if not self.has_section(section):
                self.add_section(section)
            self.set(section, key, value)

    def get_calibration_path(self) -> Path:
        """Get the path to the calibration files"""
        path = Path(self.get("Paths", "calibration", fallback="/SNS/VULCAN/shared/CALIBRATION/"))
        # user path might be in the path, so expand it
        path = path.expanduser()
        return path
