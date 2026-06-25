from functools import lru_cache
from pathlib import Path

from mantid.api import FileFinder
from mantid.kernel import Logger

from vnext import Config

_log = Logger("vnext.fileservice")


@lru_cache
def find_run_file(run: int) -> Path | None:
    """Find the on-disk path for a VULCAN run"""

    instrument = Config["instrument.name"]
    run_id = f"{instrument}_{run}" if run > 0 else None

    # look for a file
    file_path = None
    if run_id:
        # use filefinder to look
        try:
            file_path = FileFinder.findRuns(run_id)
            if isinstance(file_path, list) and len(file_path) > 0:
                file_path = file_path[0]  # take the first one if multiple found
        except RuntimeError:
            pass  # just keep looking

    # if none found, return None
    if file_path:
        return Path(file_path)
    else:
        return None


@lru_cache
def get_ipts(run: int) -> int | None:
    filename = str(find_run_file(run))

    ipts = None
    if bool(filename):
        # extract the IPTS directory from the path
        ipts_loc = filename.find("IPTS")
        if ipts_loc <= 0:
            raise RuntimeError("Failed to determine IPTS directory " + "from path '%s'" % filename)
        else:
            number_loc = filename.find("/", ipts_loc)
            ipts = filename[ipts_loc + len("IPTS") + 1 : number_loc]
    if ipts:
        return int(ipts)
    else:
        return None


def get_runs_in_range(ipts: int, runs: int, rune: int = -1) -> dict[int, Path]:
    # ensure any runs were passed and that they exist in the data directory
    run_end = rune if rune != -1 else runs
    runs_range = range(runs, run_end + 1)
    all_runs = {}
    for run in runs_range:
        file_path = Path(Config["instrument.data.file"].format(IPTS=ipts, run=run))
        if file_path.exists():
            all_runs[run] = file_path
        else:
            _log.warning(f"Run {run} does not exist in IPTS {ipts}, skipping.")

    return all_runs
