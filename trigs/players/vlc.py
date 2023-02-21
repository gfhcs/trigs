import subprocess
from .base import Player, PlayerStatus


class VLCPlayer(Player):
    """
    A player based on VLC, using playerctl.
    """

    def __init__(self, paths):
        """
        Launches a new media player. The player is paused immediately after launch.
        :param paths: An iterable of paths to media files and/or playlists. These will form the list of sequences the
                      player is playing.
        """
        super().__init__()

        self._player_id = None

        preexisting = set(self._playerctl("-l"))
        self._process = subprocess.Popen(["cvlc",
                                          "--verbose=-1",
                                          "--start-paused", "--play-and-pause", "--no-random", "--no-loop",
                                          *paths], text=True)
        players = preexisting
        while players.issubset(preexisting):
            players = set(self._playerctl("-l"))

        ps = players - preexisting
        assert len(ps) == 1
        self._player_id = ps.pop()

    async def append_sequence(self, data):
        raise NotImplementedError("append_sequence")

    async def remove_sequence(self, sidx):
        raise NotImplementedError("remove_sequence")

    async def clear_sequences(self):
        raise NotImplementedError("clear_sequences")

    @property
    async def num_sequences(self):
        raise NotImplementedError("num_sequences")

    async def get_sequence(self, sidx):
        raise NotImplementedError("get_sequence")

    async def terminate(self):
        if self._process is not None:
            self._process.terminate()
            self._process = None

    def _playerctl(self, *args):
        """
        Executes the 'playerctl' command with the given arguments, addressing only the VLC process owned by this
        object.
        :param args: The command line arguments to pass to playerctl.
        :return: The output from playerctl.
        """

        if self._player_id is not None:
            args = args + ("--player", self._player_id)

        return [line.strip() for line in subprocess.run(["playerctl", *args],
                                                        text=True, stdout=subprocess.PIPE).stdout.splitlines()]

    @property
    async def status(self):
        ss = self._playerctl("status")[0]
        if ss == "Playing":
            return PlayerStatus.PLAYING
        elif ss == "Paused":
            return PlayerStatus.PAUSED
        elif ss == "Stopped":
            return PlayerStatus.STOPPED
        else:
            raise NotImplementedError("An unexpected player status has been returned by playerctl: {}".format(ss))

    async def play(self):
        self._playerctl("play")

    async def pause(self):
        self._playerctl("pause")

    async def stop(self):
        self._playerctl("stop")

    async def next(self):
        self._playerctl("next")

    async def previous(self):
        self._playerctl("previous")

    @property
    async def position(self):
        return float(self._playerctl("position")[0])

    async def set_position(self, value):
        self._playerctl("position", str(value))

    @property
    async def duration(self):
        return float((await self.metadata)['vlc:length']) / 1000

    @property
    async def volume(self):
        return float(self._playerctl("volume")[0])

    async def set_volume(self, value):
        self._playerctl("volume", str(value))

    @property
    async def metadata(self):
        """
        The metadata the player gives for the current sequence.
        :return: A dict mapping string keys to string values.
        """
        data = {}
        for line in self._playerctl("metadata"):
            remainder = line[line.find(" "):].lstrip()
            d = remainder.find(" ")
            key, value = remainder[:d].strip(), remainder[d:].strip()
            data[key] = value
        return data

