
import abc


class Connection(abc.ABC):
    """
    Represents a connection between two communication partners.
    Partners can send and receive binary data over the connection.
    """

    def __init__(self):
        """
        Creates a new connection.
        """
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @abc.abstractmethod
    def close(self):
        """
        Closes this connection. No further communication is possible.
        """
        pass

    @abc.abstractmethod
    async def send(self, cmd, *args):
        """
        Sends data over this connection.
        :param cmd: A bytes-like object representing the command that is sent.
        :param args: A number of bytes-like objects that are sent as arguments to the command.
        """
        pass

    @abc.abstractmethod
    async def recv(self):
        """
        Receives data over this connection.
        :return: A tuple (cmd, *args) of bytes-like objects.
        """
        pass
