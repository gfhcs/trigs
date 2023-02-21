import time

from trigs.players.base import Player
from .protocol import RequestType


class RemotePlayer(Player):
    """
    Represents a player that is running on a remote machine.
    """

    def __init__(self, client, ttl=1/1000):
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

    async def clear_sequences(self):
        await self._client.request(RequestType.CLEAR)

    @property
    async def num_sequences(self):
        return await self._client.request(RequestType.GETNUMSEQUENCES)

    async def get_sequence(self, sidx):
        return await self._client.request(RequestType.GETSEQUENCE, sidx)

    async def append_sequence(self, wav):
        (sw, nc, fr, data) = wav
        await self._client.request(RequestType.APPENDWAV, sw, nc, fr, data)

    async def remove_sequence(self, sidx):
        await self._client.request(RequestType.REMOVESEQUENCE, sidx)

    @property
    async def status(self):
        _, ts = self._status_ttl
        now = time.monotonic_ns()
        if ts is None or now - ts > self._ttl * 10 ** 9:
            self._status_ttl = (await self._client.request(RequestType.GETSTATUS), now)

        return self._status_ttl[0]

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
        return await self._client.request(RequestType.GETPOSITION)

    async def set_position(self, value):
        await self._client.request(RequestType.SETPOSITION, value)

    @property
    async def duration(self):
        return await self._client.request(RequestType.GETDURATION)

    @property
    async def volume(self):
        return await self._client.request(RequestType.GETVOLUME)

    async def set_volume(self, value):
        await self._client.request(RequestType.SETVOLUME, value)

    async def terminate(self):
        return await self._client.request(RequestType.TERMINATECONNECTION)
