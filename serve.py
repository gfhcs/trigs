#!/usr/bin/python3
# coding=utf8

import argparse
import asyncio

from trigs.asynchronous import first
from trigs.console import begin, done
from trigs.display import Display
from trigs.error import TrigsError
from trigs.players.pyaudio import PyAudioPlayer, PlayerStatus
from trigs.playlist import resolve_playlist, load_wav
from trigs.remote.player import RemotePlayer
from trigs.remote.protocol import PlayerServer, RequestType, ResponseType, pformat
from trigs.remote.tcp import TCPConnection
from trigs.triggers.bluetooth import BluetoothTrigger, TriggerError
from trigs.triggers.virtual import VirtualTriggerWindow

# region Argument parsing

parser = argparse.ArgumentParser(description='Serves as an audio player to which remote clients'
                                             ' can connect and control playback.')

parser.add_argument('hostname', type=str, help='The host name for which this server should accept connections.')
parser.add_argument('port', type=int, help='The port on which this server should listen for connections.')


# endregion


async def main():

    args = parser.parse_args()

    player = None
    listener = None

    try:
        print("Serving for {}:{}...".format(args.hostname, args.port))
        server = PlayerServer()
        listener = asyncio.create_task(TCPConnection.serve(args.hostname, args.port, server.serve_client))

        while True:
            request = await server.next_request()
            rt = None
            values = ()
            try:

                if request.rtype == RequestType.TERMINATECONNECTION:
                    rt = ResponseType.SUCCESS
                else:
                    raise NotImplementedError()

            except:
                rt = ResponseType.UNKNOWNERROR
                values = ()
            finally:
                request.serve(rt, *values)
                print("Request: {}".format(request))
                print("Response: {}".format(pformat(rt, *values)))

    finally:
        if listener is not None:
            listener.cancel()
        if player is not None:
            player.terminate()


if __name__ == '__main__':
    asyncio.run(main())

