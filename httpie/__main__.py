"""The main entry point. Invoke as `http' or `python -m httpie'.

"""


def main():
    try:
        from httpie.core import main
        exit_status = main()
    except KeyboardInterrupt:
        from httpie.status import ExitStatus
        exit_status = ExitStatus.ERROR_CTRL_C

    return exit_status.value


if __name__ == '__main__':  # pragma: nocover
    import sys
    sys.exit(main())
