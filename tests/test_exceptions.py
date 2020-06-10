'''Test suite for custom exception classes'''
import mock
from pytest import raises
from requests import Request
from requests.exceptions import ConnectionError
from httpie.status import ExitStatus
from utils import HTTP_OK, http