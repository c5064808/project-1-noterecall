"""Convenience wrapper: scripts/build_index.py [options] == python -m noterecall index [...]"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from noterecall.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(["index", *sys.argv[1:]]))
