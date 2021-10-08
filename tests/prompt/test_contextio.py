# -*- coding: utf-8 -*-
from .base import TempAppDirTestCase
from httpie.prompt.context import Context
from httpie.prompt.contextio import save_context, load_context


class TestContextIO(TempAppDirTestCase):

    def test_save_and_load_context_non_ascii(self):
        c = Context('http://localhost')
        c.headers.update({
            'User-Agent': 'Ö',
            'Authorization': '中文'
        })
        save_context(c)

        c = Context('http://0.0.0.0')
        load_context(c)

        self.assertEqual(c.url, 'http://localhost')
        self.assertEqual(c.headers, {
            'User-Agent': 'Ö',
            'Authorization': '中文'
        })
