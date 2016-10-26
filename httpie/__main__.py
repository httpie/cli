#!/usr/bin/env python
"""The main entry point. Invoke as `http' or `python -m httpie'.

"""
import sys


def main():
    try:
        from .core import main
        sys.exit(main())
    except KeyboardInterrupt:
        from . import ExitStatus
        sys.exit(ExitStatus.ERROR_CTRL_C)


if __name__ == '__main__':
    main()
