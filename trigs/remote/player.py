import time

from trigs.players.base import Player
from .protocol import RequestType


class RemotePlayer(Player):
    """
    Represents a player that is running on a remote machine.
    """

    def __init__(self, client, ttl=1/20):
        """
        Makes a remote player available as a local object.
        :param client: The PlayerClient object that is used to communicate with the remote player.
        :param ttl: The "time to live" of information queried from the remote player, in seconds.
                    Certain information queried from
                    the player will be cached for this amount of time. This assumes that the remote player does not
                    change its state in a relevant way during that time and avoids unnecessary network traffic.
        """
        super().__init__()
        self._client = client
        self._ttl = ttl
        self._status_ttl = (None, None)

    @property
    async def num_sequences(self):
        """
        The number of sequences in the playlist of the remote player.
        :return: A nonnegative integer.
        """
        _, num_sequences = await self._client.request(RequestType.GETNUMSEQUENCES)
        return num_sequences

    async def get_sequence(self, idx):
        """
        Downloads a sequence from the remote player.
        :param idx: The index of the sequence to download.
        :return: A bytes object that holds the audio data of the sequence.
        """
        _, data = await self._client.request(RequestType.GETSEQUENCE, idx)
        return data

    async def append_sequence(self, data):
        """
        Appends a sequence to the playlist of the remote player.
        :param data: A bytes object that holds the audio data of the sequence.
        """
        await self._client.request(RequestType.APPEND, data)

    @property
    async def status(self):
        s, ts = self._status_ttl
        now = time.monotonic_ns()

        if ts is None or now - ts > self._ttl * 10 ** 9:
            _, s = await self._client.request(RequestType.GETSTATUS)
            self._status_ttl = (s, now)

        return s

    async def play(self):
        await self._client.request(RequestType.PLAY)

    async def pause(self):
        await self._client.request(RequestType.PAUSE)

    async def stop(self):
        await self._client.request(RequestType.STOP)

    async def next(self):
        await self._client.request(RequestType.NEXT)

    async def previous(self):
        await self._client.request(RequestType.PREVIOUS)

    @property
    async def position(self):
        _, p = await self._client.request(RequestType.GETPOSITION)
        return p

    @position.setter
    async def position(self, value):
        await self._client.request(RequestType.SETPOSITION, value)

    @property
    async def duration(self):
        _, d = await self._client.request(RequestType.GETDURATION)
        return d

    @property
    async def volume(self):
        _, v = await self._client.request(RequestType.GETVOLUME)
        return v

    @volume.setter
    async def volume(self, value):
        await self._client.request(RequestType.SETVOLUME, value)

    async def terminate(self):
        await self._client.request(RequestType.TERMINATECONNECTION)
