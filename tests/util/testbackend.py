from typing import Any

from vnext import VNEXTBackend, unset_float


class TestBackend(VNEXTBackend):
    def vnextview(
        self,
        *,
        ipts: int,
        runs: int = -1,
        rune: int = -1,
        chopruns: int = -1,
        runv: int = -1,
        norm: int = -1,
        pc: int = -1,
        minv: float = unset_float,
        maxv: float = unset_float,
    ) -> dict[str, Any]:
        return {
            "name": "vnextview",
            "ipts": ipts,
            "runs": runs,
            "rune": rune,
            "chopruns": chopruns,
            "runv": runv,
            "norm": norm,
            "pc": pc,
            "minv": minv,
            "maxv": maxv,
        }

    def vnextbin(
        self,
        *,
        ipts: int,
        runs: int = -1,
        rune: int = -1,
        chopruns: int = -1,
    ) -> dict[str, Any]:
        return {"name": "vnextbin", "ipts": ipts, "runs": runs, "rune": rune, "chopruns": chopruns}

    def vnextbin_n(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextbin_n", "ipts": ipts, **kwargs}

    def vnextbin_ns(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextbin_ns", "ipts": ipts, **kwargs}

    def vnextchop(
        self,
        *,
        ipts: int,
        runs: int = -1,
        dbin: float = 1,
        minv: float = unset_float,
        maxv: float = unset_float,
    ) -> dict[str, Any]:
        return {"name": "vnextchop", "ipts": ipts, "runs": runs, "dbin": dbin, "minv": minv, "maxv": maxv}

    def vnextchop_en(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextchop_en", "ipts": ipts, **kwargs}

    def vnextchop_ens(
        self,
        *,
        ipts: int,
        runs: int = -1,
        se: str = "Temperature",
        dse: float = 1,
        minv: float = unset_float,
        maxv: float = unset_float,
    ) -> dict[str, Any]:
        return {"name": "vnextchop_ens", "ipts": ipts, "runs": runs, "se": se, "dse": dse, "minv": minv, "maxv": maxv}

    def vnextspf(
        self,
        *,
        ipts: int,
        runs: int = -1,
        rune: int = -1,
        chopruns: int = -1,
        runv: int = -1,
        runr: int = -1,
        pc: int = -1,
        norm: int = -1,
        updated: int = -1,
        autofix: int = -1,
        npeaks: float = unset_float,
    ) -> dict[str, Any]:
        return {
            "name": "vnextspf",
            "ipts": ipts,
            "runs": runs,
            "rune": rune,
            "chopruns": chopruns,
            "runv": runv,
            "runr": runr,
            "pc": pc,
            "norm": norm,
            "updated": updated,
            "autofix": autofix,
            "npeaks": npeaks,
        }

    def vnextgsas(
        self,
        *,
        ipts: int,
        runs: int = -1,
        rune: int = -1,
        choprun: int = -1,
        runm: int = -1,
    ) -> dict[str, Any]:
        return {"name": "vnextgsas", "ipts": ipts, "runs": runs, "rune": rune, "choprun": choprun, "runm": runm}

    def vnextlog(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextlog", "ipts": ipts, **kwargs}

    def vnextfit(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextfit", "ipts": ipts, **kwargs}

    def vnextprm(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextprm", "ipts": ipts, **kwargs}

    def vnextcali(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextcali", "ipts": ipts, **kwargs}

    def vnextmerge(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextmerge", "ipts": ipts, **kwargs}

    def vnextpixel(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextpixel", "ipts": ipts, **kwargs}

    def vnextpole(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextpole", "ipts": ipts, **kwargs}

    def vnextsum(self, *, ipts: int, **kwargs: Any) -> dict[str, Any]:
        return {"name": "vnextsum", "ipts": ipts, **kwargs}
