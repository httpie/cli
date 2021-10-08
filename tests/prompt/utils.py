import os
import sys


def get_http_prompt_path():
    """Get the path to http-prompt executable."""
    python_dir = os.path.dirname(sys.executable)
    bin_name = 'http-prompt'
    if sys.platform == 'win32':
        bin_name += '.exe'

    paths = [
        os.path.join(python_dir, bin_name),
        os.path.join(python_dir, 'Scripts', bin_name),  # Windows
        '/usr/bin/http-prompt'  # Homebrew installation
    ]
    for path in paths:
        if os.path.exists(path):
            return path

    raise OSError("could not locate http-prompt executable, "
                  "Python directory: %s" % python_dir)
