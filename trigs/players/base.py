import abc
from enum import Enum


class PlayerStatus(Enum):
    """
    The status of a media player.
    """
    PLAYING = 0  # Playback is active.
    PAUSED = 1  # The player is paused.
    STOPPED = 2  # The player is stopped.


class Player(abc.ABC):
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

        self._paths = tuple(paths)

    @property
    def paths(self):
        """
        An iterable of paths to media files and/or playlists. These form the list of sequences this player is playing.
        """
        return self._paths

    @property
    @abc.abstractmethod
    def status(self):
        """
        The current status of this player.
        :return: A PlayerStatus object.
        """
        pass

    @abc.abstractmethod
    def play(self):
        """
        Starts or resume playback.
        """
        pass

    @abc.abstractmethod
    def pause(self):
        """
        Pauses playback, i.e. stops it without changing the position in the sequence.
        """
        pass

    @abc.abstractmethod
    def stop(self):
        """
        Stops playback, resetting the position in the current sequence to the start.
        """
        pass

    @abc.abstractmethod
    def next(self):
        """
        Stops playback and jumps to the start of the next sequence.
        """
        pass

    @abc.abstractmethod
    def previous(self):
        """
        Stops playback and jumps to the start of the previous sequence.
        """
        pass

    @property
    @abc.abstractmethod
    def position(self):
        """
        The position of the player in the current sequence, in seconds.
        :return: A floating number representing the position in seconds.
        """
        pass

    @position.setter
    @abc.abstractmethod
    def position(self, value):
        pass

    @property
    @abc.abstractmethod
    def volume(self):
        """
        The volume at which playback happens, as a fraction of the maximum.
        :return: A floating number representing the volume.
        """
        pass

    @volume.setter
    @abc.abstractmethod
    def volume(self, value):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()

    @abc.abstractmethod
    def terminate(self):
        pass
