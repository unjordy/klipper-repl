#!/usr/bin/env python3

import re

from time import localtime, strftime

from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.formatted_text import FormattedText

temp_regex = re.compile(r'^(?:ok\s+)?(b|t\d+):\d+\.\d+ \/\d+\.+\d+', flags=re.IGNORECASE)

def format_output(prefix, s):
    if s.startswith('!!'):
        return FormattedText([('red', f'{prefix}  {s}')])
    elif temp_regex.match(s):
        return None
    else:
        return FormattedText([('gray', f'{prefix}  {s}')])

def print_output(s):
    ts = strftime('%I:%M:%S %p', localtime())
    gap = ' ' * len(ts)
    lines = s.splitlines()
    s0 = format_output(ts, lines[0])
    if s0 is not None:
        print(s0)
    for l in lines[1:]:
        s = format_output(gap, l)
        if s is not None:
            print(s)

async def render_output(data):
    output = data.get('params', {}).get('response')
    if output is not None:
        print_output(output)
