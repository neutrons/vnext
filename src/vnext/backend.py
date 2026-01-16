import numpy as np


def func(kwargs):
    if "rune" in kwargs:
        a = np.arange(int(kwargs["runs"]), int(kwargs["rune"]) + 1)
        return a
    else:
        a = np.arange(int(kwargs["runs"]), int(kwargs["runs"]) + 1)
        return a


def vnextview(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextview: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextbin(**kwargs):
    runarr = func(kwargs)
    print(runarr)
    for key, value in kwargs.items():
        print(key, value)
    # print(f"vnextbin: IPTS={IPTS}, kwargs={kwargs}")
    return  # {"IPTS": IPTS, "kwargs": kwargs}


def vnextbin_n(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextbin_n: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextbin_ns(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextbin_ns: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextchop(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextchop: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextchop_en(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextchope_n: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextchop_ens(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextchop_ens: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextspf(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextspf: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextgsas(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextgsas: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextlog(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextlog: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextfit(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextfit: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextprm(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextprm: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextcali(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextcali: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextmerge(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextmerge: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextpixel(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextpixel: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextpole(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextpole: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}


def vnextsum(ipts, **kwargs):
    # Replace with real logic
    print(f"vnextsum: IPTS={ipts}, kwargs={kwargs}")
    return {"IPTS": ipts, "kwargs": kwargs}
