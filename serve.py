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
        print("WARNING: The communication of this server is not secure! Everyone on the network can read and manipulate "
              "its communication! Use this server only in environments where this is not a concern!")
        print("Serving for {}:{}...".format(args.hostname, args.port))
        server = PlayerServer()
        listener = asyncio.create_task(TCPConnection.serve(args.hostname, args.port, server.serve_client))

        while True:
            request = await server.next_request()
            rt = None
            values = ()
            try:

                if request.rtype == RequestType.APPENDWAV:
                    *swncfr, _ = request.args
                    if player is None:
                        player = PyAudioPlayer(*swncfr)
                    await player.append_sequence(request.args)
                    rt = ResponseType.SUCCESS
                elif request.rtype == RequestType.GETNUMSEQUENCES:
                    values = (0, ) if player is None else (player.num_sequences, )
                    rt = ResponseType.VALUE
                elif request.rtype == RequestType.CLEAR:
                    if player is not None:
                        await player.clear_sequences()
                    rt = ResponseType.SUCCESS
                elif request.rtype == RequestType.GETSTATUS:
                    values = (PlayerStatus.STOPPED, ) if player is None else (await player.status, )
                    rt = ResponseType.VALUE

                if rt is not None:
                    continue

                if player is None:
                    rt = ResponseType.ERROR_UNINITIALIZED
                elif request.rtype == RequestType.GETVOLUME:
                    values = (await player.volume, )
                    rt = ResponseType.VALUE
                elif request.rtype == RequestType.SETVOLUME:
                    await player.set_volume(*values)
                    rt = ResponseType.SUCCESS

                if rt is not None:
                    continue

                if player.num_sequences == 0:
                    rt = ResponseType.ERROR_NOSEQUENCES
                elif request.rtype == RequestType.GETSEQUENCE:
                    sidx, = request.args
                    values = tuple(*(await player.get_sequence(sidx)))
                    rt = ResponseType.VALUE
                elif request.rtype == RequestType.REMOVESEQUENCE:
                    sidx, = request.args
                    await player.remove_sequence(sidx)
                    rt = ResponseType.SUCCESS
                elif request.rtype == RequestType.GETDURATION:
                    values = (await player.duration, )
                    rt = ResponseType.VALUE
                elif request.rtype == RequestType.PLAY:
                    await player.play()
                    rt = ResponseType.SUCCESS
                elif request.rtype == RequestType.PAUSE:
                    await player.pause()
                    rt = ResponseType.SUCCESS
                elif request.rtype == RequestType.STOP:
                    await player.stop()
                    rt = ResponseType.SUCCESS
                elif request.rtype == RequestType.NEXT:
                    await player.next()
                    rt = ResponseType.SUCCESS
                elif request.rtype == RequestType.PREVIOUS:
                    await player.previous()
                    rt = ResponseType.SUCCESS
                elif request.rtype == RequestType.GETPOSITION:
                    values = (await player.position, )
                    rt = ResponseType.VALUE
                elif request.rtype == RequestType.SETPOSITION:
                    await player.set_position(*values)
                    rt = ResponseType.SUCCESS
                elif request.rtype == RequestType.TERMINATECONNECTION:
                    rt = ResponseType.SUCCESS
                else:
                    raise NotImplementedError(request.rtype)

            except NotImplementedError:
                rt = ResponseType.ERROR_NOTIMPLEMENTED
                values = ()
            except:
                rt = ResponseType.ERROR_UNKNOWN
                values = ()
            finally:
                request.serve(rt, *values)
                print("<-- {}".format(request))
                print("\t--> {}".format(pformat(rt, *values)))

    finally:
        if listener is not None:
            listener.cancel()
        if player is not None:
            player.terminate()


if __name__ == '__main__':
    asyncio.run(main())

