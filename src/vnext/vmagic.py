import shlex
from typing import Any, Callable, ClassVar

from IPython import get_ipython
from IPython.core.error import UsageError
from IPython.core.magic import Magics, magics_class

from vnext.vnext_protocol import VNEXTBackend
from vnext.vutils import parse_kv_tokens, to_int_if_possible


def _normalize_commas(line: str) -> str:
    """
    Replace commas outside quotes with spaces so commas act as separators.
    Commas inside quotes are preserved.
    """
    out = []
    in_quote = False
    q = ""
    for ch in line:
        if ch in ("'", '"'):
            if in_quote and ch == q:
                in_quote = False
            elif not in_quote:
                in_quote = True
                q = ch
            out.append(ch)
            continue
        out.append(" " if (not in_quote and ch == ",") else ch)
    return "".join(out)


def _split_tokens(line: str) -> list[str]:
    """
    Split by whitespace while preserving quotes; then strip stray/trailing commas.
    """
    parts = shlex.split(_normalize_commas(line.strip()))
    return [p.rstrip(",") for p in parts if p and p != ","]


def _normalize_ipts(kwargs: dict[str, Any]) -> dict[str, Any]:
    """
    Make ipts key case-insensitive and coerce to int if possible.
    """
    for k in list(kwargs.keys()):
        if k.lower() == "ipts":
            kwargs["ipts"] = to_int_if_possible(str(kwargs.pop(k)))
    return kwargs


@magics_class
class VNEXTMagics(Magics):
    _map: ClassVar[dict[str, Callable[..., Any]]] = {
        "view": VNEXTBackend.vnextview,
        "vbin": VNEXTBackend.vnextbin,
        "vbinen": VNEXTBackend.vnextbin_n,
        "vbinens": VNEXTBackend.vnextbin_ns,
        "chopen": VNEXTBackend.vnextchop_en,
        "chopens": VNEXTBackend.vnextchop_ens,
        "chop": VNEXTBackend.vnextchop,
        "vspf": VNEXTBackend.vnextspf,
        "gsas": VNEXTBackend.vnextgsas,
        "vlog": VNEXTBackend.vnextlog,
        "vfit": VNEXTBackend.vnextfit,
        "vprm": VNEXTBackend.vnextprm,
        "cali": VNEXTBackend.vnextcali,
        "merge": VNEXTBackend.vnextmerge,
        "pixel": VNEXTBackend.vnextpixel,
        "pole": VNEXTBackend.vnextpole,
        "vsum": VNEXTBackend.vnextsum,
    }

    def __init__(self, shell, backend: VNEXTBackend) -> None:
        super().__init__(shell)
        self.backend = backend

    def _make_handler(self, proto_method: Callable[..., Any]) -> Callable[[str], Any]:
        """
        Factory producing a line-magic handler bound to a specific method.
        """
        backend_name = proto_method.__name__

        def handler(line: str) -> Any:
            kwargs = parse_kv_tokens(_split_tokens(line))
            _normalize_ipts(kwargs)
            return getattr(self.backend, backend_name)(**kwargs)

        handler.__name__ = backend_name
        handler.__doc__ = proto_method.__doc__
        return handler

    def _dispatch(self, line: str) -> Any:
        """
        Generic dispatcher: %V <operation> [key=value ...]
        Example: %V VBin, Ipts=123, runs=45,rune=89
        """
        tokens = _split_tokens(line)
        if not tokens:
            raise UsageError(f"Missing operation name. Valid: {', '.join(self._map)}")
        name, *rest = tokens
        name_lower = name.lower()
        if name_lower not in self._map:
            raise UsageError(f"Unknown operation '{name}'. Valid: {', '.join(self._map)}")
        kwargs = parse_kv_tokens(rest)
        _normalize_ipts(kwargs)
        return getattr(self.backend, self._map[name_lower].__name__)(**kwargs)


def load_ipython_extension(ipython=None, *, backend: VNEXTBackend) -> None:
    ipython = ipython or get_ipython()
    if ipython is None:
        raise RuntimeError("Not in an IPython environment")
    if backend is None:
        raise RuntimeError("A VNEXTBackend instance must be supplied via the backend= argument")

    magics = VNEXTMagics(ipython, backend)

    for name, proto_method in VNEXTMagics._map.items():
        handler = magics._make_handler(proto_method)
        ipython.register_magic_function(handler, magic_kind="line", magic_name=name)
        ipython.register_magic_function(handler, magic_kind="line", magic_name=f"{name},")
        # Optional: lower-case aliases
        ipython.register_magic_function(handler, magic_kind="line", magic_name=name.lower())
        ipython.register_magic_function(handler, magic_kind="line", magic_name=f"{name.lower()},")
    # Register a generic dispatcher for flexibility
    ipython.register_magic_function(magics._dispatch, magic_kind="line", magic_name="V")
    ipython.register_magic_function(magics._dispatch, magic_kind="line", magic_name="V,")
    # Optional: enable automagic so magics can be used without %
    ipython.run_line_magic("automagic", "on")


def unload_ipython_extension(ip=None) -> None:
    # IPython does not provide a public API to unregister magics cleanly.
    # You can reload the kernel or avoid unloading.
    pass
