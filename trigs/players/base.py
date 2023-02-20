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

    @abc.abstractmethod
    async def append_sequence(self, data):
        """
        Appends a sequence to the playlist of this player.
        :param data: An object that encodes the sequence to add.
        """
        pass

    @abc.abstractmethod
    async def remove_sequence(self, sidx):
        """
        Removes a sequence from the playlist of this player.
        :param sidx: The index of the sequence to remove.
        """
        pass

    @abc.abstractmethod
    async def clear_sequences(self):
        """
        Clears the playlist of this player.
        """
        pass

    @property
    @abc.abstractmethod
    async def num_sequences(self):
        """
        The number of sequences in the playlist of this player.
        :return: A nonnegative integer.
        """
        pass

    @abc.abstractmethod
    async def get_sequence(self, sidx):
        """
        Retrieves a sequence from the playlist of this player.
        :param sidx: The index of the sequence to retrieve
        :return: A representation of the sequence to retrieve.
        """
        pass

    @property
    @abc.abstractmethod
    async def status(self):
        """
        The current status of this player.
        :return: A PlayerStatus object.
        """
        pass

    @abc.abstractmethod
    async def play(self):
        """
        Starts or resume playback.
        """
        pass

    @abc.abstractmethod
    async def pause(self):
        """
        Pauses playback, i.e. stops it without changing the position in the sequence.
        """
        pass

    @abc.abstractmethod
    async def stop(self):
        """
        Stops playback, resetting the position in the current sequence to the start.
        """
        pass

    @abc.abstractmethod
    async def next(self):
        """
        Stops playback and jumps to the start of the next sequence.
        """
        pass

    @abc.abstractmethod
    async def previous(self):
        """
        Stops playback and jumps to the start of the previous sequence.
        """
        pass

    @property
    @abc.abstractmethod
    async def position(self):
        """
        The position of the player in the current sequence, in seconds.
        :return: A floating number representing the position in seconds.
        """
        pass

    @property
    @abc.abstractmethod
    async def duration(self):
        """
        The duration of the current sequence, in seconds.
        :return: A float.
        """
        pass

    @position.setter
    @abc.abstractmethod
    async def position(self, value):
        pass

    @property
    @abc.abstractmethod
    async def volume(self):
        """
        The volume at which playback happens, as a fraction of the maximum.
        :return: A floating number representing the volume.
        """
        pass

    @volume.setter
    @abc.abstractmethod
    async def volume(self, value):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.terminate()

    @abc.abstractmethod
    async def terminate(self):
        pass


