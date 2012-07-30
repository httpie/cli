# -*- coding: utf-8 -*-

"""
    solarized256
    ------------

    A Pygments style inspired by Solarized's 256 color mode.

    :copyright: (c) 2011 by Hank Gay, (c) 2012 by John Mastro.
    :license: BSD, see LICENSE for more details.
"""

from pygments.style import Style
from pygments.token import Token, Comment, Name, Keyword, Generic, Number, \
    Operator, String

BASE03  = "#1c1c1c"
BASE02  = "#262626"
BASE01  = "#4e4e4e"
BASE00  = "#585858"
BASE0   = "#808080"
BASE1   = "#8a8a8a"
BASE2   = "#d7d7af"
BASE3   = "#ffffd7"
YELLOW  = "#af8700"
ORANGE  = "#d75f00"
RED     = "#af0000"
MAGENTA = "#af005f"
VIOLET  = "#5f5faf"
BLUE    = "#0087ff"
CYAN    = "#00afaf"
GREEN   = "#5f8700"


class Solarized256Style(Style):
    background_color = BASE03
    styles = {
        Keyword: GREEN,
        Keyword.Constant: ORANGE,
        Keyword.Declaration: BLUE,
        Keyword.Namespace: ORANGE,
        #Keyword.Pseudo
        Keyword.Reserved: BLUE,
        Keyword.Type: RED,

        #Name
        Name.Attribute: BASE1,
        Name.Builtin: BLUE,
        Name.Builtin.Pseudo: BLUE,
        Name.Class: BLUE,
        Name.Constant: ORANGE,
        Name.Decorator: BLUE,
        Name.Entity: ORANGE,
        Name.Exception: YELLOW,
        Name.Function: BLUE,
        #Name.Label
        #Name.Namespace
        #Name.Other
        Name.Tag: BLUE,
        Name.Variable: BLUE,
        #Name.Variable.Class
        #Name.Variable.Global
        #Name.Variable.Instance

        #Literal
        #Literal.Date
        String: CYAN,
        String.Backtick: BASE01,
        String.Char: CYAN,
        String.Doc: CYAN,
        #String.Double
        String.Escape: RED,
        String.Heredoc: CYAN,
        #String.Interpol
        #String.Other
        String.Regex: RED,
        #String.Single
        #String.Symbol
        Number: CYAN,
        #Number.Float
        #Number.Hex
        #Number.Integer
        #Number.Integer.Long
        #Number.Oct

        Operator: BASE1,
        Operator.Word: GREEN,

        #Punctuation: ORANGE,

        Comment: BASE01,
        #Comment.Multiline
        Comment.Preproc: GREEN,
        #Comment.Single
        Comment.Special: GREEN,

        #Generic
        Generic.Deleted: CYAN,
        Generic.Emph: 'italic',
        Generic.Error: RED,
        Generic.Heading: ORANGE,
        Generic.Inserted: GREEN,
        #Generic.Output
        #Generic.Prompt
        Generic.Strong: 'bold',
        Generic.Subheading: ORANGE,
        #Generic.Traceback

        Token: BASE1,
        Token.Other: ORANGE,
    }
