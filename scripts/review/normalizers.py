"""Compatibility shim for review normalizers now hosted in avidtools."""

import sys
from pathlib import Path

script_dir_path = Path(__file__).resolve().parent
sys.path = [
    path
    for path in sys.path
    if Path(path or ".").resolve() != script_dir_path
]

avidtools_path = (
    Path(__file__).resolve().parent.parent.parent.parent / "avidtools"
)
sys.path.insert(0, str(avidtools_path))

from avidtools.connectors.utils import *  # noqa: E402,F401,F403
