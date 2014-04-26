from httpie.context import Environment
from .headers import HeadersProcessor
from .json import JSONProcessor
from .xml import XMLProcessor
from .colors import PygmentsProcessor


class ProcessorManager(object):
    """A delegate class that invokes the actual processors."""

    available = {
        'format': [
            HeadersProcessor,
            JSONProcessor,
            XMLProcessor
        ],
        'colors': [
            PygmentsProcessor
        ]
    }

    def __init__(self, groups, env=Environment(), **kwargs):
        """
        :param groups: names of processor groups to be applied
        :param env: Environment
        :param kwargs: additional keyword arguments for processors

        """
        self.enabled = []
        for group in groups:
            for cls in self.available[group]:
                p = cls(env, **kwargs)
                if p.enabled:
                    self.enabled.append(p)

    def process_headers(self, headers):
        for p in self.enabled:
            headers = p.process_headers(headers)
        return headers

    def process_body(self, body, mime):
        for p in self.enabled:
            body = p.process_body(body, mime)
        return body
