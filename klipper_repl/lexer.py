#!/usr/bin/env python3

from prompt_toolkit.styles import Style, style_from_pygments_cls, merge_styles

from pygments.lexer import RegexLexer, bygroups
from pygments.token import Comment, Name, Text, Keyword, Number
from pygments.styles.gruvbox import GruvboxDarkStyle

from .api import shared

style = merge_styles([
    style_from_pygments_cls(GruvboxDarkStyle),
    Style.from_dict({
    'pygments.name.function': '#51b0ff'
    })
])

class KlipperLexer(RegexLexer):
    tokens = {
        'root': [
            (r';.*?$', Comment),
            (r'[gmGM]\d{1,4}', Name.Builtin),  # M or G commands
            (r'([^gGmM])([+-]?\d*[.]?\d+)', bygroups(Keyword, Number)),
            (r',', Text.Punctuation),
            (r'\s', Text.Whitespace),
            (r'\w+', Text),
        ]
    }

    def get_tokens_unprocessed(self, text):
        for index, token, value in RegexLexer.get_tokens_unprocessed(self, text):
            if token is Text and value.upper() in shared.macro_list:
                yield index, Name.Function, value
            else:
                yield index, token, value
