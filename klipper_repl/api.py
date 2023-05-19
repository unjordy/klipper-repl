#!/usr/bin/env python3

import json
import threading

from enum import IntEnum

from .output import render_output

class ResponseType(IntEnum):
    Info = 0
    Gcode = 1
    Macros = 2

shared = threading.local()
shared.connection_info = {}
shared.macro_list = []

async def update_connection_info(data, event):
    global shared
    shared.connection_info = data.get('result')
    event.set()

async def update_macros(data, event):
    global shared
    output = data.get('result')
    if output is not None:
        shared.macro_list = list(output.keys())
        event.set()

async def receive_task(reader, connect_event, macro_event, disconnect_event):
    try:
        while True:
            data = await reader.readuntil(separator=b'\x03')
            res = json.loads(data[:-1].decode())
            if res.get('key') == ResponseType.Gcode:
                await render_output(res)
            elif res.get('id') == ResponseType.Macros:
                await update_macros(res, macro_event)
            elif res.get('id') == ResponseType.Info:
                await update_connection_info(res, connect_event)
    except Exception as e:
        disconnect_event.set()

def rpc(method, id=None, key=None, params=None):
    call = { 'method': method }
    p = {  }
    if id is not None:
        call['id'] = id
    if key is not None:
        p['response_template'] = { 'key': key }
    if params is not None:
        p.update(params)
    if len(p) > 0:
        call['params'] = p

    return call

async def klipper_call(writer, methods):
    s = '\x03'.join([json.dumps(x, separators=(',', ':')) for x in methods])
    writer.write(('%s\x03' % s).encode())
    await writer.drain()

async def emergency_stop(writer):
    await klipper_call(writer, [
        rpc('emergency_stop', id=0)
    ])

async def send_gcode(writer, gcode):
    cmds = [x.strip() for x in gcode.split(',')]
    if 'M112' in [x.upper() for x in cmds]:
        return await emergency_stop(writer)

    await klipper_call(writer, [rpc('gcode/script',
                                    params={ 'script': x })
                                for x in cmds])
