from traitlets.config import Config
from IPython.terminal.embed import InteractiveShellEmbed
from IPython.terminal.prompts import Prompts
from pygments.token import Token
import importlib
import vutils

# Change to your real backend module name
BACKEND_MODULE_NAME = "vnext_backend"

class VPrompts(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [(Token.Prompt, "VNEXT> ")]
    def out_prompt_tokens(self):
        return [(Token.OutPrompt, "")]

def main():
    # Load backend providing functions like vdriveview, vdrivebin, ...
    try:
        backend = importlib.import_module(BACKEND_MODULE_NAME)
    except Exception:
        class _Stub:
            def __getattr__(self, name):
                def _fn(IPTS, **kw):
                    print(f"[stub:{name}] IPTS={IPTS} kwargs={kw}")
                return _fn
        backend = _Stub()

    ops = vutils.VNEXTOperations(backend)

    c = Config()
    c.TerminalInteractiveShell.confirm_exit = False

    shell = InteractiveShellEmbed(
        config=c,
        banner1=(
            "VNEXT IPython console\n"
            "- Automagic ON: call magics without leading %\n"
            "- Magics provided: VIEW, VBin, VBineN, VBineNs, chopen, chopens, chop,\n"
            "                   Vspf, gsas, vlog, Vfit, Vprm, cali, merge, pixel, pole, VSUM\n"
            "Usage: METHOD IPTS [key=value ...]\n"
            "Ctrl-D to exit."
        ),
        exit_msg="Bye."
    )
    shell.prompts = VPrompts(shell)

    # Put ops in user namespace
    shell.push({"ops": ops})

    # Load magics and enable automagic
    shell.run_line_magic("load_ext", "vmagic")
    shell.run_line_magic("automagic", "on")

    shell()

if __name__ == "__main__":
    main()
