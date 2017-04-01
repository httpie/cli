#!/usr/bin/env python
"""The main entry point. Invoke as `http' or `python -m httpie'.

"""
import sys

if sys.platform.startswith('win') and sys.version_info[0] == 2:
    # https://github.com/jakubroztocil/httpie/issues/572

    # https://stackoverflow.com/questions/846850/read-unicode-characters-from-command-line-arguments-in-python-2-x-on-windows/846931#846931
    def win32_unicode_argv():
        """Use shell32.GetCommandLineArgvW to get sys.argv as a list of
        Unicode strings.

        Versions 2.x of Python don't support Unicode in sys.argv on
        Windows, with the underlying Windows API instead replacing
        multi-byte characters with '?'.
        """

        from ctypes import POINTER, byref, cdll, c_int, windll
        from ctypes.wintypes import LPCWSTR, LPWSTR

        GetCommandLineW = cdll.kernel32.GetCommandLineW
        GetCommandLineW.argtypes = []
        GetCommandLineW.restype = LPCWSTR

        CommandLineToArgvW = windll.shell32.CommandLineToArgvW
        CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(c_int)]
        CommandLineToArgvW.restype = POINTER(LPWSTR)

        cmd = GetCommandLineW()
        argc = c_int(0)
        argv = CommandLineToArgvW(cmd, byref(argc))
        if argc.value > 0:
            # Remove Python executable and commands if present
            start = argc.value - len(sys.argv)
            return [argv[i] for i in xrange(start, argc.value)]

    argv = win32_unicode_argv()
else:
    argv = sys.argv


def main(argv):
    try:
        from .core import main
        sys.exit(main(argv[1:]))
    except KeyboardInterrupt:
        from . import ExitStatus
        sys.exit(ExitStatus.ERROR_CTRL_C)


if __name__ == '__main__':
    main(argv)
