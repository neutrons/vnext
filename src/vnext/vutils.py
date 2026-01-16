import ast
import inspect
import types
from typing import Any, Dict, Iterable, List, Union


def coerce_scalar(text: str) -> Any:
    try:
        return ast.literal_eval(text)
    except Exception:
        return text


def parse_kv_tokens(tokens: Iterable[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    args: List[str] = []
    for t in tokens:
        if "=" in t:
            k, v = t.split("=", 1)
            out[k] = coerce_scalar(v)
        else:
            if t.isidentifier() and t not in out:
                out[t] = True
            else:
                args.append(t)
    if args:
        out["_args"] = args
    return out


def to_int_if_possible(s: str) -> Union[int, str]:
    try:
        return int(s, 10)
    except Exception:
        return s


class _Backend:
    def __init__(self, src: Union[types.ModuleType, Dict[str, Any]]):
        self._is_module = inspect.ismodule(src)
        self._src = src

    def get(self, name: str):
        func = getattr(self._src, name, None) if self._is_module else self._src.get(name)
        if func is None or not callable(func):
            raise AttributeError(f"Backend does not provide callable '{name}'")
        return func


class VNEXTOperations:
    _map = {
        "VIEW": "vnextview",
        "VBin": "vnextbin",
        "VBineN": "vnextbinen",
        "VBineNs": "vnextbinens",
        "chopen": "vnextchopen",
        "chopens": "vnextchopens",
        "chop": "vnextchop",
        "Vspf": "vnextspf",
        "gsas": "vnextgsas",
        "vlog": "vdriverecorden",
        "Vfit": "vnextfit",
        "Vprm": "vnextprm",
        "cali": "vnextcali",
        "merge": "vnextmerge",
        "pixel": "vnextpixel2d",
        "pole": "vnextpole",
        "VSUM": "vnextsumgsas",
    }

    def __init__(self, backend: Union[types.ModuleType, Dict[str, Any]]):
        self._backend = _Backend(backend)

    def _call(self, key: str, **_extra):
        func = self._backend.get(self._map[key])
        return func(**_extra)

    def VIEW(self, **_extra):
        return self._call("VIEW", **_extra)

    def VBin(self, **_extra):
        return self._call("VBin", **_extra)

    def VBineN(self, **_extra):
        return self._call("VBineN", **_extra)

    def VBineNs(self, **_extra):
        return self._call("VBineNs", **_extra)

    def chopen(self, **_extra):
        return self._call("chopen", **_extra)

    def chopens(self, **_extra):
        return self._call("chopens", **_extra)

    def chop(self, **_extra):
        return self._call("chop", **_extra)

    def Vspf(self, **_extra):
        return self._call("Vspf", **_extra)

    def gsas(self, **_extra):
        return self._call("gsas", **_extra)

    def vlog(self, **_extra):
        return self._call("vlog", **_extra)

    def Vfit(self, **_extra):
        return self._call("Vfit", **_extra)

    def Vprm(self, **_extra):
        return self._call("Vprm", **_extra)

    def cali(self, **_extra):
        return self._call("cali", **_extra)

    def merge(self, **_extra):
        return self._call("merge", **_extra)

    def pixel(self, **_extra):
        return self._call("pixel", **_extra)

    def pole(self, **_extra):
        return self._call("pole", **_extra)

    def VSUM(self, **_extra):
        return self._call("VSUM", **_extra)

    @classmethod
    def required_backend_names(cls) -> List[str]:
        return sorted(set(cls._map.values()))

    @classmethod
    def method_names(cls) -> List[str]:
        return list(cls._map.keys())
