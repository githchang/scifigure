#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

# Allow execution directly from the skill folder without installation.
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from scifigure.cli import main

if __name__=='__main__':
    raise SystemExit(main())
