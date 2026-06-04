"""Type definitions used in vnext"""

from pathlib import Path

# define a type for file paths that can be either a string or a Path object
FilePath = str | Path

del Path
