import numpy as np


def func(kwargs):
    if "rune" in kwargs:
        a = np.arange(int(kwargs["runs"]), int(kwargs["rune"]) + 1)
        return a
    else:
        a = np.arange(int(kwargs["runs"]), int(kwargs["runs"]) + 1)
        return a


def vnextview(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextview: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextbin(**kwargs):
    runarr = func(kwargs)
    print(runarr)
    for key, value in kwargs.items():
        print(key, value)
    # print(f"vnextbin: IPTS={IPTS}, kwargs={kwargs}")
    return  # {"IPTS": IPTS, "kwargs": kwargs}


def vnextbinN(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextbinN: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextbinNs(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextbinNs: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextchop(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextchop: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextchopen(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextchopen: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextchopens(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextchopens: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextspf(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextspf: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextgsas(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextgsas: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextlog(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextlog: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextfit(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextfit: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextprm(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextprm: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextcali(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextcali: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextmerge(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextmerge: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextpixel(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextpixel: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextpole(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextpole: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}


def vnextsum(IPTS, **kwargs):
    # Replace with real logic
    print(f"vnextsum: IPTS={IPTS}, kwargs={kwargs}")
    return {"IPTS": IPTS, "kwargs": kwargs}
