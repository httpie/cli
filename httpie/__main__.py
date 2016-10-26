#!/usr/bin/env python
"""The main entry point. Invoke as `http' or `python -m httpie'.

"""
import sys


if __name__ == '__main__':
    try:
        from .core import main
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
