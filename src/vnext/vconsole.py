import importlib

from IPython.terminal.embed import InteractiveShellEmbed
from IPython.terminal.prompts import Prompts
from pygments.token import Token
from traitlets.config import Config

from vnext import vutils

# Change to your real backend module name
BACKEND_MODULE_NAME = "vnext.backend"


class VPrompts(Prompts):
    def in_prompt_tokens(self, cli=None):  # noqa: ARG002
        return [(Token.Prompt, "VNEXT> ")]

    def out_prompt_tokens(self):
        return [(Token.OutPrompt, "")]


def main(argv=None):  # noqa: ARG001
    # Load backend providing functions like vdriveview, vdrivebin, ...
    try:
        backend = importlib.import_module(BACKEND_MODULE_NAME)
    except RuntimeError:

        class _Stub:
            def __getattr__(self, name):
                def _fn(ipts, **kw):
                    print(f"[stub:{name}] IPTS={ipts} kwargs={kw}")

                return _fn

        backend = _Stub()

    ops = vutils.VNEXTOperations(backend)

    config = Config()
    config.TerminalInteractiveShell.confirm_exit = False

    shell = InteractiveShellEmbed(
        config=config,
        banner1=(
            "VNEXT IPython console\n"
            "- Automagic ON: call magics without leading %\n"
            "- Magics provided: view, vbin, vbine_n, vbine_ns, chopen, chopens, chop,\n"
            "                   vspf, gsas, vlog, vfit, vprm, cali, merge, pixel, pole, vsum\n"
            "Usage: METHOD IPTS [key=value ...]\n"
            "Ctrl-D to exit."
        ),
        exit_msg="Bye.",
    )
    shell.prompts = VPrompts(shell)

    # Put ops in user namespace
    shell.push({"ops": ops})

    # Load magics and enable automagic
    shell.run_line_magic("load_ext", "vnext.vmagic")
    shell.run_line_magic("automagic", "on")

    shell()


if __name__ == "__main__":
    import sys

    main(sys.argv)
