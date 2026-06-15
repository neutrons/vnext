import os
from pathlib import Path

# Set the test configuration override before any vnext imports so the
# Configuration singleton picks it up on first use.
os.environ["VNEXT_CONFIG"] = str(Path(__file__).parent / "configuration.yml")
