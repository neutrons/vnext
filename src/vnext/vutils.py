import ast
from typing import Any, Iterable


def coerce_scalar(text: str) -> Any:
    try:
        return ast.literal_eval(text)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return text


def parse_kv_tokens(tokens: Iterable[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    args: list[str] = []
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


def to_int_if_possible(s: str) -> int | str:
    try:
        return int(s, 10)
    except ValueError:
        return s
