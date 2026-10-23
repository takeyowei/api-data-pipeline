#!/usr/bin/env python3
"""Entry point: python run.py {fetch|changes|report|export}"""

import sys

from pipeline.cli import main

if __name__ == "__main__":
    sys.exit(main())
