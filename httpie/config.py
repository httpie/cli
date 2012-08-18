import os
from requests.compat import  is_windows

__author__ = 'jakub'


CONFIG_DIR = (os.path.expanduser('~/.httpie') if not is_windows else
              os.path.expandvars(r'%APPDATA%\\httpie'))
