"""
JSON lexer by Norman Richards

It's already been merged into Pygments but not released yet,
so we are temporarily bundling it with HTTPie.

It can be removed once Pygments > 1.4 has been released.

See <https://github.com/jkbr/httpie/pull/25> for more details.

"""
import re
from pygments import token
from pygments.lexer import RegexLexer, include


class JSONLexer(RegexLexer):
    name = 'JSON Lexer'
    aliases = ['json']
    filenames = ['*.json']
    mimetypes = []


    flags = re.DOTALL
    tokens = {
        'whitespace': [
            (r'\s+', token.Text),
        ],

        # represents a simple terminal value
        'simplevalue':[
            (r'(true|false|null)\b', token.Keyword.Constant),
            (r'-?[0-9]+', token.Number.Integer),
            (r'"(\\\\|\\"|[^"])*"', token.String.Double),
        ],


        # the right hand side of an object, after the attribute name
        'objectattribute': [
            include('value'),
            (r':', token.Punctuation),
            # comma terminates the attribute but expects more
            (r',', token.Punctuation, '#pop'),
            # a closing bracket terminates the entire object, so pop twice
            (r'}', token.Punctuation, ('#pop', '#pop')),
        ],

        # a json object - { attr, attr, ... }
        'objectvalue': [
            include('whitespace'),
            (r'"(\\\\|\\"|[^"])*"', token.Name.Tag, 'objectattribute'),
            (r'}', token.Punctuation, '#pop'),
        ],

        # json array - [ value, value, ... }
        'arrayvalue': [
            include('whitespace'),
            include('value'),
            (r',', token.Punctuation),
            (r']', token.Punctuation, '#pop'),
        ],

        # a json value - either a simple value or a complex value (object or array)
        'value': [
            include('whitespace'),
            include('simplevalue'),
            (r'{', token.Punctuation, 'objectvalue'),
            (r'\[', token.Punctuation, 'arrayvalue'),
        ],


        # the root of a json document would be a value
        'root': [
            include('value'),
        ],

    }
