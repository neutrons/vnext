from IPython import get_ipython
from IPython.core.error import UsageError
import shlex
from typing import Dict, List
from vutils import VNEXTOperations, parse_kv_tokens, to_int_if_possible
import vnext_backend as backend

# 2) Create the adapter (ipts optional per your vutils.py)
ops = VNEXTOperations(backend)

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
        if not in_quote and ch == ",":
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)

def _split_tokens(line: str) -> List[str]:
    """
    Split by whitespace while preserving quotes; then strip stray/trailing commas.
    """
    normalized = _normalize_commas(line.strip())
    parts = shlex.split(normalized)
    parts = [p.rstrip(",") for p in parts if p and p != ","]
    return parts

def _normalize_ipts(kwargs: Dict) -> Dict:
    """
    Make ipts key case-insensitive and coerce to int if possible.
    """
    for k in list(kwargs.keys()):
        if k.lower() == "ipts":
            v = kwargs.pop(k)
            kwargs["ipts"] = to_int_if_possible(str(v))
    return kwargs

def _make_handler(method_name: str):
    """
    Factory producing a line-magic handler bound to a specific method.
    """
    def _handler(line: str):
        tokens = _split_tokens(line)
        kwargs = parse_kv_tokens(tokens)
        kwargs = _normalize_ipts(kwargs)
        try:
            target = getattr(ops, method_name)
        except AttributeError:
            valid = ", ".join(ops.method_names())
            raise UsageError(f"Unknown operation '{method_name}'. Valid methods: {valid}")
        return target(**kwargs)
    return _handler

def _generic_dispatch(line: str):
    """
    Generic magic: first token is the method name (with or without trailing comma).
    Example: %V VBin, Ipts=123, runs=45,rune=89
    """
    tokens = _split_tokens(line)
    if not tokens:
        valid = ", ".join(ops.method_names())
        raise UsageError(f"Missing method name. Usage: %V <method> [args]. Valid methods: {valid}")
    method = tokens[0]
    rest = tokens[1:]
    kwargs = parse_kv_tokens(rest)
    kwargs = _normalize_ipts(kwargs)
    try:
        target = getattr(ops, method)
    except AttributeError:
        valid = ", ".join(ops.method_names())
        raise UsageError(f"Unknown operation '{method}'. Valid methods: {valid}")
    return target(**kwargs)

def load_ipython_extension(ip=None):
    ip = ip or get_ipython()
    if ip is None:
        raise RuntimeError("Not in IPython environment")

    # Register a generic dispatcher for flexibility
    ip.register_magic_function(_generic_dispatch, magic_kind="line", magic_name="V")
    ip.register_magic_function(_generic_dispatch, magic_kind="line", magic_name="V,")

    # Register specific magics for all known methods, plus aliases with trailing comma
    for name in ops.method_names():
        handler = _make_handler(name)
        ip.register_magic_function(handler, magic_kind="line", magic_name=name)
        ip.register_magic_function(handler, magic_kind="line", magic_name=f"{name},")
        # Optional: lower-case aliases
        ip.register_magic_function(handler, magic_kind="line", magic_name=name.lower())
        ip.register_magic_function(handler, magic_kind="line", magic_name=f"{name.lower()},")
    # Optional: enable automagic so magics can be used without %
    ip.run_line_magic("automagic", "on")

def unload_ipython_extension(ip=None):
    # IPython does not provide a public API to unregister magics cleanly.
    # You can reload the kernel or avoid unloading.
    pass
