import subprocess

from enum import Enum


class PlayerStatus(Enum):
    """
    The status of a media player.
    """
    PLAYING = 0  # Playback is active.
    PAUSED = 1  # The player is paused.
    STOPPED = 2  # The player is stopped.


class Player:
    """
    Represents a media player that is playing a list of sequences.
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
    def status(self):
        """
        The current status of this player.
        :return: A PlayerStatus object.
        """
        ss = self._playerctl("status")[0]
        if ss == "Playing":
            return PlayerStatus.PLAYING
        elif ss == "Paused":
            return PlayerStatus.PAUSED
        elif ss == "Stopped":
            return PlayerStatus.STOPPED
        else:
            raise NotImplementedError("An unexpected player status has been returned by playerctl: {}".format(ss))

    def play(self):
        """
        Starts or resume playback.
        """
        self._playerctl("play")

    def pause(self):
        """
        Pauses playback, i.e. stops it without changing the position in the sequence.
        """
        self._playerctl("pause")

    def stop(self):
        """
        Stops playback, resetting the position in the current sequence to the start.
        """
        self._playerctl("stop")

    def next(self):
        """
        Stops playback and jumps to the start of the next sequence.
        """
        self._playerctl("next")

    def previous(self):
        """
        Stops playback and jumps to the start of the previous sequence.
        """
        self._playerctl("previous")

    @property
    def position(self):
        """
        The position of the player in the current sequence, in seconds.
        :return: A floating number representing the position in seconds.
        """
        return float(self._playerctl("position")[0])

    @position.setter
    def position(self, value):
        self._playerctl("position", str(value))

    @property
    def volume(self):
        """
        The volume at which playback happens, as a fraction of the maximum.
        :return: A floating number representing the volume.
        """
        return float(self._playerctl("volume")[0])

    @volume.setter
    def volume(self, value):
        self._playerctl("volume", str(value))

    @property
    def metadata(self):
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()

    def terminate(self):
        if self._process is not None:
            self._process.terminate()
            self._process = None