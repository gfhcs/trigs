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
from trigs.remote.protocol import PlayerServer
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

    listener = None

    try:
        print("Serving for {}:{}...".format(args.host, args.port))
        server = PlayerServer()
        listener = asyncio.create_task(TCPConnection.serve(args.host, args.port, server.serve_client))

        with PyAudioPlayer(paths=[]) as player:

            while True:
                request = await server.next_request()

                print("Got a request :-)")
                return

    finally:
        if listener is not None:
            listener.cancel()


if __name__ == '__main__':
    asyncio.run(main())

