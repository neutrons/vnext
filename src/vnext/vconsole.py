from IPython.terminal.embed import InteractiveShellEmbed
from IPython.terminal.prompts import Prompts
from pygments.token import Token
from traitlets.config import Config

from vnext.backend import Backend
from vnext.vmagic import load_ipython_extension


class VPrompts(Prompts):
    def in_prompt_tokens(self, cli=None):  # noqa: ARG002
        return [(Token.Prompt, "VNEXT> ")]

    def out_prompt_tokens(self):
        return [(Token.OutPrompt, "")]


def main(argv=None):  # noqa: ARG001
    backend = Backend()

    config = Config()
    config.TerminalInteractiveShell.confirm_exit = False

    shell = InteractiveShellEmbed(
        config=config,
        banner1=(
            "VNEXT IPython console\n"
            "- Automagic ON: call magics without leading %\n"
            "- Magics provided: view, vbin, vbinen, vbinens, chopen, chopens, chop,\n"
            "                   vspf, gsas, vlog, vfit, vprm, cali, merge, pixel, pole, vsum\n"
            "Usage: METHOD ipts=<IPTS> [key=value ...]\n"
            "Ctrl-D to exit."
        ),
        exit_msg="Bye.",
    )
    shell.prompts = VPrompts(shell)

    load_ipython_extension(shell, backend=backend)

    shell()


if __name__ == "__main__":
    import sys

    main(sys.argv)
