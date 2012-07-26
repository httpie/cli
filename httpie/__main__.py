#!/usr/bin/env python
"""The main entry point. Invoke as `http' or `python -m httpie'.

"""
import sys
from .core import main


if __name__ == '__main__':
    sys.exit(main())
