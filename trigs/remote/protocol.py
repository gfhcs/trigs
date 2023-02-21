import asyncio
import io
import struct
from enum import Enum

from trigs.players.base import PlayerStatus


class RequestType(Enum):
    """
    The types of requests that a client can send to a server.
    """
    PLAY = 0
    PAUSE = 1
    STOP = 2
    NEXT = 3
    PREVIOUS = 4
    SETPOSITION = 5
    GETPOSITION = 6
    SETVOLUME = 7
    GETVOLUME = 8
    GETDURATION = 9
    GETSTATUS = 10
    CLEAR = 100
    APPENDWAV = 101
    GETNUMSEQUENCES = 102
    GETSEQUENCE = 103
    REMOVESEQUENCE = 104
    TERMINATECONNECTION = 1001


class ResponseType(Enum):
    """
    The types of responses a server can serve a request with.
    """
    SUCCESS = 0
    VALUE = 1
    ERROR_UNKNOWN = 2
    ERROR_NOTIMPLEMENTED = 3
    ERROR_FORMAT = 4
    ERROR_UNINITIALIZED = 5
    ERROR_NOSEQUENCES = 6


def c2b(c):
    """
    Converts a chunk, i.e. a Python object that can be part of a request, to a bytes object.
    :param c: The Python object to be converted into bytes. Only certain types of objects are supported.
    :return: A bytes object.
    """
    if isinstance(c, (RequestType, ResponseType, PlayerStatus)):
        c = c.value
    if isinstance(c, int):
        assert c >= 0
        assert c.bit_length() <= 32
        return c.to_bytes(4, 'big')
    elif isinstance(c, float):
        return struct.pack('f', c)
    elif isinstance(c, bytes):
        return c


def b2c(t, b):
    """
    Converts a bytes object into a Python object of the given type.
    :param t: The type to convert the bytes into. Only certian types are supported.
    :return: An object of the given type.
    """

    if t in (int, RequestType, ResponseType, PlayerStatus):
        assert len(b) == 4
        b = int.from_bytes(b, 'big')
        if t is int:
            return b
        return t(b)
    elif t is float:
        return struct.unpack('f', b)[0]
    elif t is bytes:
        return b


class PlayerClient:
    """
    This object controls a remote player.
    """

    def __init__(self, connection):
        """
        Creates a new local client for the player protocol.
        :param connection: The Connection via which the requests to the server should be issued.
        """
        self._connection = connection

    async def request(self, command, *args):
        """
        Sends a request to the server and awaits the response.
        :param command: The Command to send.
        :param args: The arguments for the command to send.
        :return: A tuple (possibly of length 0), that contains the return values received for this request.
        """
        await self._connection.send(*map(c2b, (command, *args)))
        rt, *values = await self._connection.recv()

        rt = b2c(ResponseType, rt)

        if rt == ResponseType.SUCCESS:
            if len(values) != 0:
                raise IOError("The server responded with {}, but also sent values, which is a violation of the protocol!".format(rt))
            return
        elif rt == ResponseType.ERROR_FORMAT:
            raise ValueError("The server claims that the arguments given for {}"
                             " were of the wrong kind or number!".format(command))
        elif rt == ResponseType.ERROR_UNKNOWN:
            raise IOError("The server reported an unknown error!")
        elif rt == ResponseType.ERROR_NOSEQUENCES:
            raise RuntimeError("The remote playlist is empty!")
        elif rt == ResponseType.ERROR_UNINITIALIZED:
            raise RuntimeError("The remote player has not been initialized ever!")
        elif rt == ResponseType.ERROR_NOTIMPLEMENTED:
            raise NotImplementedError("Serving this request has not been implemented in the server!")
        elif rt == ResponseType.VALUE:

            if command == RequestType.GETNUMSEQUENCES:
                t = int
            elif command == RequestType.GETSEQUENCE:
                t = bytes
            elif command == RequestType.GETSTATUS:
                t = PlayerStatus
            else:
                t = float

            return b2c(t, values[0])
        else:
            raise IOError("The server reported an unknown error!")


class PlayerServer:

    class Request:
        """
        A request that a server has received from a client.
        """
        def __init__(self, connection, rt, *args):
            """
            Instantiates a new request.
            :param connection: The connection via which the request was received and over which the response will be
                               sent.
            :param rt: The RequestType.
            :param args: The arguments that were sent along with the request.
            """
            self._connection = connection
            self._rt = rt
            self._args = args
            self._response = asyncio.Future()

        def serve(self, rt, *values):
            """
            Provides the response and (possibly) the return values to this request. Must be called on every request
            eventually.
            :param rt: The ResponseType.
            :param values: The values to send along with the response.
            """
            self._response.set_result((rt, *values))

        @property
        def args(self):
            """
            The arguments for this request.
            :return: A tuple of objects.
            """
            return self._args

        @property
        def rtype(self):
            """
            The type of this request.
            :return: A RequestType value.
            """
            return self._rt

        @property
        def connection(self):
            """
            The connection via which this request was received.
            :return: A Connection object.
            """
            return self._connection

        @property
        def response(self):
            return self._response

        def __str__(self):
            return pformat(self._rt, *self._args)

    def __init__(self):
        """
        Instantiates a new server for the player protocol.
        """
        self._requests = asyncio.Queue()

    async def serve_client(self, connection):
        """
        Serves a protocol client, as long as the connection to that client is open.
        Note that the requests received from the client will only be answered if self.next_request is awaited
        sufficiently many times!
        :param connection: The Connection to the client.
        """
        while True:
            try:
                rt, *args = await connection.recv()
            except EOFError:
                connection.close()
                return
            rt = b2c(RequestType, rt)

            if rt == RequestType.GETSEQUENCE:
                ts = (int, )
            elif rt == RequestType.APPENDWAV:
                ts = (int, int, int, bytes)
            else:
                ts = (float, )

            args = [b2c(t, a) for a, t in zip(args, ts)]

            r = PlayerServer.Request(connection, rt, *args)
            await self._requests.put(r)
            await connection.send(*map(c2b, await r.response))

            if rt == RequestType.TERMINATECONNECTION and r.response == ResponseType.SUCCESS:
                return

    async def next_request(self):
        """
        Waits for a request from a client.
        :return: A Request object. It must be processed by the caller in order to respond to the request!
        """
        return await self._requests.get()


def pformat(rt, *args):
    """
    Formats a protocol message.
    :param rt: Either a RequestType or a ResponseType.
    :param args: The arguments that are part of the protocol message.
    :return: A string.
    """
    s = io.StringIO()
    rts = str(rt)
    s.write(rts[rts.find(".") + 1:])
    s.write(": ")
    prefix = ""
    for a in args:
        s.write(prefix)
        if isinstance(a, bytes):
            s.write('<bytes>')
        else:
            s.write(str(a))
        prefix = ", "
    return s.getvalue()
