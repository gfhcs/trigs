from .connection import Connection
import asyncio


class TCPConnection(Connection):
    """
    A TCP socket that connects the local client machine to a remote server.
    """

    def __init__(self, reader, writer):
        self._reader = reader
        self._writer = writer

    @staticmethod
    async def open_outgoing(host, port):
        """
        Opens a TCP connection to a remote host.
        :param host: The host name of the remote machine.
        :param port: The port on which to open the connection.
        :return: A TCPConnection object.
        """
        return TCPConnection(*(await asyncio.open_connection(host, port)))

    @staticmethod
    async def serve(host, port, s):
        """
        Creates a server that accepts TCPConnections.
        :param host: The host name for which this server should listen.
        :param port: The port this server should listen on.
        :param s: A callback that accepts a TCPConnection as its only argument. This callback will be responsible
                 for the entire communication with the client.
        """
        async def handle_client(reader, writer):
            await s(TCPConnection(reader, writer))
        server = await asyncio.start_server(handle_client, host, port)
        async with server:
            await server.serve_forever()

    def close(self):
        if self._reader is not None:
            self._reader.close()
            self._reader = None
        if self._writer is not None:
            self._writer.close()
            self._writer = None

    async def send(self, cmd, *args):
        n = 1 + len(args)
        n = n.to_bytes(4, 'big')
        self._writer.write(n)
        for chunk in (cmd, *args):
            n = len(chunk)
            n = n.to_bytes(4, 'big')
            self._writer.write(n)
            self._writer.write(chunk)
        await self._writer.drain()

    async def recv(self):
        num_chunks = int.from_bytes(await self._reader.read(4), 'big')
        assert num_chunks > 1
        chunks = []
        for _ in range(num_chunks):
            chunk_size = int.from_bytes(await self._reader.read(4), 'big')
            chunks.append(await self._reader.read(chunk_size))
        return chunks
