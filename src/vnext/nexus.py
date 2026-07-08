import datetime
from pathlib import Path
from typing import Any

import h5py
from mantid.simpleapi import DeleteWorkspace, LoadEventNexus, mtd

from vnext import Config, FilePath


def extract_nexus_metadata(nexus_file: FilePath) -> tuple[datetime.datetime, float, float]:
    """
    Read run metadata from NeXus.
    VULCAN has two chopper pairs; Skf34 (20 Hz, ~2.8 Å) is used for
    standard wide-range powder reduction.  Log names may vary by era —
    try each name in order and use the first one present.
    """

    # Chopper log names — first entry in each list is the preferred (current) name.
    wl_keys = Config["instrument.PVLogs.choppers.skf34.wavelength"]
    spd_keys = Config["instrument.PVLogs.choppers.skf34.speed"]

    with h5py.File(nexus_file, "r") as f:
        logs = f[Config["instrument.nexus.das_logs"]]
        run_date = datetime.datetime.fromisoformat(f[Config["instrument.nexus.start_time_log"]][0].decode()[:19])
        center_wavelength = float(next(logs[k] for k in wl_keys if k in logs)["value"][0])
        frequency = float(next(logs[k] for k in spd_keys if k in logs)["value"][0])

    return run_date, center_wavelength, frequency


def load_run_logs(nexus_file: FilePath, ws_name: str, *, require: str = ""):
    """Load a run's logs into a Mantid workspace without the event data.

    Uses ``LoadEventNexus(MetaDataOnly=True, LoadLogs=True)`` so the returned
    workspace carries the run's sample-environment logs (for plotting via the
    ``mantid`` projection) but skips the heavy event arrays.  The workspace is
    left in the ADS under ``ws_name``.

    When ``require`` names a log, only that log is loaded (via ``AllowList``)
    alongside ``proton_charge`` — which the log plot references for the
    first-pulse time — rather than every DASlog.  If the required log is absent,
    the workspace is discarded and a ``KeyError`` is raised.
    """

    allow = {"AllowList": f"{require},proton_charge"} if require else {}
    LoadEventNexus(
        Filename=str(nexus_file),
        OutputWorkspace=ws_name,
        MetaDataOnly=True,
        LoadLogs=True,
        **allow,
    )
    ws = mtd[ws_name]
    if require and not ws.run().hasProperty(require):
        DeleteWorkspace(ws_name)
        raise KeyError(f"Log '{require}' not found in {nexus_file}")
    return ws


def extract_log(nexus_file: FilePath, name: str = "") -> dict[str, Any]:
    if not Path(nexus_file).exists():
        raise FileNotFoundError(f"NeXus file {nexus_file} not found")

    root_group = Config["instrument.PVLogs.rootGroup"]
    with h5py.File(nexus_file, "r") as f:
        daslogs = f[root_group]

        if not name:
            log_names = sorted(daslogs.keys())
            return {"file": nexus_file, "logs": log_names}

        if name not in daslogs:
            raise KeyError(f"Log '{name}' not found in {nexus_file}")

        log_group = daslogs[name]
        time = log_group["time"][:]
        value = log_group["value"][:]
        units = log_group["value"].attrs.get("units", b"")
        time_units = log_group["time"].attrs.get("units", b"")

    def _decode(raw: Any) -> str:
        return raw.decode() if isinstance(raw, bytes) else str(raw)

    return {
        "name": name,
        "time": time,
        "value": value,
        "units": _decode(units),
        "time_units": _decode(time_units),
    }
