#!/usr/bin/python3
# coding=utf8

import argparse
import asyncio

from trigs.remote.protocol import PlayerServer, RequestType, ResponseType, pformat
from trigs.remote.tcp import TCPConnection
from trigs.players.pyaudio import PyAudioPlayer, PlayerStatus

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

                if request.rtype == RequestType.APPENDWAV:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.GETNUMSEQUENCES:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.GETSEQUENCE:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.REMOVESEQUENCE:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.CLEAR:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.GETDURATION:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.GETSTATUS:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.PLAY:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.PAUSE:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.STOP:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.NEXT:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.PREVIOUS:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.GETPOSITION:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.SETPOSITION:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.GETVOLUME:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.SETVOLUME:
                    raise NotImplementedError(request.rtype)
                elif request.rtype == RequestType.TERMINATECONNECTION:
                    rt = ResponseType.SUCCESS
                else:
                    raise NotImplementedError(request.rtype)

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

