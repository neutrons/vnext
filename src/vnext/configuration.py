"""VNext configuration — loaded from a YAML file with ${key} substitution."""

import os
import re
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from vnext._typing import FilePath

# configuration settings file path - this is where linux puts things by default
CONFIG_PATH_USER: Path = Path.home() / ".config" / "vnext" / "configuration.ini"
_SUBST_RE = re.compile(r"\$\{([a-zA-Z0-9_.]+)\}")


class Configuration:
    """Singleton configuration loaded from YAML with ``${key}`` substitution.

    Only one instance exists per process.  On first use the instance is built
    from:

    1. The bundled ``configuration.yml`` package defaults.
    2. An override YAML at the path given by the ``VNEXT_CONFIG`` environment
       variable, if set (intended for test and site-specific overrides).

    Keys are accessed with dot notation: ``config["instrument.calibration.home"]``.
    Values may reference other keys via ``${other.key}`` resolved recursively.
    Runtime template placeholders such as ``{IPTS}`` are left untouched.

    A ``project.root`` key is injected automatically as the repository root
    so override YAMLs can write ``${project.root}/tests/data`` without
    hard-coding absolute paths.

    Call ``Configuration.reset()`` to destroy the singleton (e.g. in tests that
    need to reload config after changing ``VNEXT_CONFIG``).
    """

    _instance: "Configuration | None" = None

    def __new__(cls, config_path: FilePath | None = None) -> "Configuration":
        if cls._instance is None or config_path is not None:
            instance = super().__new__(cls)
            instance._setup(config_path)
            cls._instance = instance
        return cls._instance

    def __init__(self, config_path: FilePath | None = None) -> None:
        pass  # setup is done once in _setup(), called from __new__

    # ------------------------------------------------------------------ #
    # Singleton lifecycle                                                  #
    # ------------------------------------------------------------------ #

    @classmethod
    def reset(cls) -> None:
        """Destroy the singleton so the next ``Configuration()`` call rebuilds it.

        Useful in tests that change ``VNEXT_CONFIG`` between test functions.
        """
        cls._instance = None

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def __getitem__(self, key: str) -> Any:
        """Dot-notation key lookup with ``${key}`` substitution."""
        value = self._find(key)
        if value is None:
            raise KeyError(f"Configuration key '{key}' not found")
        return self._resolve(value)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def get_calibration_path(self) -> Path:
        return Path(self["instrument.calibration.home"]).expanduser()

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _setup(self, config_path: FilePath | None = None) -> None:
        default_text = files("vnext.resource").joinpath("configuration.yml").read_text(encoding="utf-8")
        self._data: dict[str, Any] = yaml.safe_load(default_text)

        import vnext

        project_root = Path(vnext.__file__).parent.parent.parent
        self._data.setdefault("project", {})["root"] = str(project_root)

        # Apply env-var override, then explicit override (explicit wins).
        env_path = os.environ.get("VNEXT_CONFIG")
        for path in filter(None, [env_path, config_path]):
            override = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
            if isinstance(override, dict):
                _deep_merge(self._data, override)

    def _find(self, key: str) -> Any:
        parts = key.split(".")
        node = self._data
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node

    def _resolve(self, value: Any, _chain: tuple[str, ...] = ()) -> Any:
        if not isinstance(value, str):
            return value

        def _replace(match: re.Match) -> str:
            ref = match.group(1)
            if ref in _chain:
                cycle = " -> ".join([*_chain, ref])
                raise ValueError(f"Circular configuration reference detected: {cycle}")
            resolved = self._find(ref)
            if resolved is None:
                return match.group(0)
            return str(self._resolve(resolved, (*_chain, ref)))

        return _SUBST_RE.sub(_replace, value)


# ------------------------------------------------------------------ #
# Module-level helpers                                                #
# ------------------------------------------------------------------ #


def _deep_merge(base: dict, override: dict) -> None:
    """Merge *override* into *base* in-place; nested dicts are merged recursively."""
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
