# coding: utf-8

import functools


MERGE_KEYS = [
    'Accept-Encoding', 'Cookie', 'Accept'
]


def merge_key_arguments(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        print(args, kwargs)
        return func(args, kwargs)
    return inner

