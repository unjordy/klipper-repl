#!/usr/bin/env python3

import sys
import argparse
import asyncio
import json

from prompt_toolkit import PromptSession, print_formatted_text as print
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.lexers import PygmentsLexer

from .api import ResponseType, rpc, klipper_call, send_gcode, emergency_stop, \
    receive_task, shared
from .lexer import style, KlipperLexer
from .output import print_output, render_output

parser = argparse.ArgumentParser(description='A Klipper g-code command line.')
parser.add_argument('socket', help='The Klipper API socket to connect to')
parser.add_argument('gcode', nargs='*', help='G-code to send to Klipper')

tasks = set()
session = PromptSession(complete_style=CompleteStyle.READLINE_LIKE, style=style)


async def run(args):
    first_connect = True
    first_reconnect = True
    stdin_read = asyncio.StreamReader()
    await asyncio.get_event_loop() \
                     .connect_read_pipe(lambda: asyncio.StreamReaderProtocol(stdin_read), \
                                        sys.stdin)
    while True:
        try:
            sock_read, sock_write = await asyncio.open_unix_connection(
                args.socket
            )
            connect_event = asyncio.Event()
            macro_event = asyncio.Event()
            disconnect_event = asyncio.Event()
            task = asyncio.create_task(receive_task(sock_read,
                                                    connect_event,
                                                    macro_event,
                                                    disconnect_event))
            tasks.add(task)
            task.add_done_callback(tasks.discard)
            await klipper_call(sock_write, [
                rpc('info', id=ResponseType.Info, params={
                    'client_info': { 'version': 'v1' }
                }),
                rpc('gcode/help', id=ResponseType.Macros),
                rpc('gcode/subscribe_output', key=ResponseType.Gcode)
            ])
            await connect_event.wait()

            if len(args.gcode) > 0:
                await send_gcode(sock_write, ' '.join(args.gcode))
                sys.exit(0)

            first_reconnect = True
            hostname = shared.connection_info.get('hostname')
            if first_connect:
                print_output(f'## Connected to Klipper at {hostname}:{args.socket}\n   ^C or ^D to quit; type M112 for emergency stop')
                first_connect = False
            else:
                print_output('## Reconnected to Klipper')
            await macro_event.wait()
            completion = WordCompleter(shared.macro_list, ignore_case=True)
            lexer = PygmentsLexer(KlipperLexer)

            while True:
                try:
                    with patch_stdout():
                        finished, unfinished = await asyncio.wait([
                            session.prompt_async(f'{hostname}:{args.socket}* ', completer=completion, lexer=lexer),
                            disconnect_event.wait()
                        ], return_when=asyncio.FIRST_COMPLETED)

                        if disconnect_event.is_set():
                            for task in unfinished:
                                task.cancel()
                            await asyncio.wait(unfinished)
                            raise ConnectionError("Receive task disconnected")

                        line = list(finished)[0].result()
                        await send_gcode(sock_write, line)
                except KeyboardInterrupt:
                    sys.exit(0)
                except EOFError:
                    sys.exit(0)

        except ConnectionError:
            if first_reconnect:
                print_output('## Disconnected. Waiting for Klipper...')
                first_reconnect = False
            await asyncio.sleep(0.25)

def main():
    if len(sys.argv) < 2:
        parser.print_usage()
        sys.exit(2)
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
