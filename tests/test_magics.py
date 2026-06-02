import pytest
from IPython.core.error import UsageError
from IPython.terminal.embed import InteractiveShellEmbed
from traitlets.config import Config

from tests.util.testbackend import TestBackend
from vnext.vmagic import VNEXTMagics, load_ipython_extension


@pytest.fixture(scope="module")
def shell():
    config = Config()
    config.TerminalInteractiveShell.confirm_exit = False
    s = InteractiveShellEmbed(config=config, banner1="", exit_msg="")
    load_ipython_extension(s, backend=TestBackend())
    return s


@pytest.mark.parametrize(
    "magic_name,proto_method",
    VNEXTMagics._map.items(),
    ids=list(VNEXTMagics._map.keys()),
)
def test_magic_routes_and_passes_kwargs(shell, magic_name, proto_method):
    result = shell.run_line_magic(magic_name, "ipts=123 runs=456")
    assert result["name"] == proto_method.__name__
    assert result["ipts"] == 123
    assert result["runs"] == 456


def test_generic_dispatcher(shell):
    result = shell.run_line_magic("V", "vbin ipts=123 runs=456")
    assert result["name"] == "vnextbin"
    assert result["ipts"] == 123
    assert result["runs"] == 456


def test_generic_dispatcher_unknown_operation(shell):
    with pytest.raises(UsageError, match="Unknown operation"):
        shell.run_line_magic("V", "nonexistent ipts=123")


def test_ipts_case_insensitive(shell):
    result = shell.run_line_magic("vbin", "IPTS=123 runs=456")
    assert result["ipts"] == 123
    assert result["runs"] == 456
    assert "IPTS" not in result


def test_comma_separated_args(shell):
    result = shell.run_line_magic("vbin", "ipts=123, runs=456")
    assert result["ipts"] == 123
    assert result["runs"] == 456


def test_trailing_comma_magic_name(shell):
    result = shell.run_line_magic("vbin,", "ipts=123 runs=456")
    assert result["name"] == "vnextbin"
    assert result["ipts"] == 123
    assert result["runs"] == 456
