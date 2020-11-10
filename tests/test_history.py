import shutil

from httpie.history import get_history
from utils import HTTP_OK, MockEnvironment, http, mk_config_dir

class HistoryTestBase:

    def start_history(self, httpbin):
        self.config_dir = mk_config_dir()

    def teardown_method(self, method):
        shutil.rmtree(self.config_dir)

    def env(self):
        return MockEnvironment(config_dir=self.config_dir)


class TestHistory(HistoryTestBase):

    def test_add_entry(self, httpbin):
        self.start_history(httpbin)

    def test_get_entry(self, httpbin):
        self.start_history(httpbin)

    def test_entry_not_found(self, httpbin):
        self.start_history(httpbin)
