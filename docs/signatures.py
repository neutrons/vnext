def vnextview(runs=1, rune=None, chopruns=None, runv=None, norm=None, pc=None, minv=None, maxv=None):
    """View one GSAS gda data pattern after binning as histogram data:
    Parameters
    - runs (int): Start run number
    - rune (int | None): End run number
    - chopruns (int | None): Chopruns where data are chopped from
    - runv (int  | None): Vanadium data for normalization
    - norm (int| None): Normalize data over proton charge charge read from xml
    - pc (int  | None):  Normalize with proton charge
    - minv (float | None): Cutoff of x axis
    - maxv (float | None):Cutoff of x axis."""
    raise NotImplementedError("Implement view")


def vnextbin(runs=1, rune=None, chopruns=None):
    """Bin event data to GSAS histogram files if not binned before:
    Parameters
    - runs (int): Start run number
    - rune (int | None): End run number
    - chopruns (int | None): Chopruns where data are chopped from"""
    raise NotImplementedError("Implement vbin")


def vnextchop(runs=1, dbin=1, minv=None, maxv=None):
    """Chop wall clock time , synchronize, and bin continuously collected data in seconds
    Parameters
    - runs (int): Start run number
    - minv (float | None): minimum value
    - maxv (float | None):maximum value
    - dbin(float| None): time bin"""
    raise NotImplementedError("Implement chop")


def vnextchopse(runs=1, se="Temperature", dse=1, minv=None, maxv=None):
    """Chop sample environment , synchronize, and bin continuously collected data in seconds
    Parameters
    - runs (int): Start run number
    -se(str): name of sample environment to be chopped
    - minv (float | None): minimum value
    - maxv (float | None):maximum value
    - dse(float| None): sample environment bin"""
    raise NotImplementedError("Implement chopse")


def vnextspf(
    runs=1, rune=None, chopruns=None, runv=None, runr=None, pc=None, norm=None, updated=None, autofix=None, npeaks=None
):
    """Conduct GSAS single peak fit:
    Parameters
    - runs (int): Start run number
    - rune (int | None): End run number
    - chopruns (int | None): Chopruns where data are chopped from
    - runv (int  | None): Vanadium data for normalization
    - norm (int| None): Normalize data over proton charge charge read from xml
    - pc (int  | None):  Normalize with proton charge
    - runr(int | None): reference run number to calculate strain, default is the first run
    - updatedp(int /None):  update peak positions
    - autofix (int| None):
    - autopeak (int | None):automatically find peak wi
    - npeaks (float | None):number of peaks to automatically generate.
    """
    raise NotImplementedError("Implement single peak fit")


def vnextgsas(runs=1, rune=None, choprun=None, runm=None):
    """Conduct GSAS Rietveld refinement:
    Parameters
    - runs (int): Start run number
    - rune (int | None): End run number
    - chopruns (int | None): Chopruns where data are chopped from
    - runm (int  | None): Template run default is first one"""

    raise NotImplementedError("Implement gsas")
