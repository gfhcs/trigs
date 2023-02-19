import io
import multiprocessing
import queue
import time
from enum import Enum

import pyaudio

from trigs.playlist import resolve_playlist, load_wav
from .base import Player, PlayerStatus


class PyAudioPlayer(Player):
    """
    A player based on pyaudio.
    """

    class PlaybackCommand(Enum):
        """
        The types of commands that the playback process underlying a PyAudioPlayer can receive and implement.
        """
        PLAY = 0
        PAUSE = 1
        STOP = 2
        NEXT = 3
        PREVIOUS = 4
        SETPOSITION = 5
        SETVOLUME = 6
        TERMINATE = 7

    @staticmethod
    def _playback(q, sequences, sampwidth, nchannels, framerate):
        """
        The code to be executed by a background process. The background process operates in parallel to the main
        process.
        :param q: The multiprocessing.QUEUE via which the background process receives commands that control playback.
        :param sequences: An iterable of byte arrays representing the sequences to be played.
        :param sampwidth: The width of the audio samples to play back, in bytes.
        :param nchannels: The number of channels of the audio sequences to play back.
        :param framerate: The number of audio frames per second to play back.
        """

        interval = 1 / 100

        frames_per_buffer = int(framerate * interval)

        zeros = b'\00' * (frames_per_buffer * nchannels * sampwidth)
        data = io.BytesIO()

        pa = None
        stream = None
        try:
            pa = pyaudio.PyAudio()

            playing = False
            sidx = 0
            offset = 0

            def produce(_, frame_count, time_info, status):
                nonlocal data, sidx, offset, playing
                data.seek(0, io.SEEK_SET)
                if playing:
                    bs = sequences[sidx][offset:offset + frame_count * nchannels * sampwidth]
                    offset += len(bs)
                    if len(bs) < frame_count * nchannels * sampwidth:
                        playing = False
                        offset = 0
                        sidx = min(len(sequences), sidx + 1)
                else:
                    bs = b''
                data.write(bs)
                data.write(zeros[len(bs):])
                r = data.getvalue()
                assert len(r) == frame_count * nchannels * sampwidth
                return (r, pyaudio.paContinue)

            stream = pa.open(format=pa.get_format_from_width(sampwidth),
                             channels=nchannels,
                             rate=framerate,
                             frames_per_buffer=frames_per_buffer,
                             stream_callback=produce,
                             output=True)

            while True:
                try:
                    cmd, *args = q.get(block=True)
                except queue.Empty:
                    continue

                if cmd == PyAudioPlayer.PlaybackCommand.PLAY:
                    playing = True
                elif cmd == PyAudioPlayer.PlaybackCommand.PAUSE:
                    playing = False
                elif cmd == PyAudioPlayer.PlaybackCommand.STOP:
                    playing = False
                    offset = 0
                elif cmd == PyAudioPlayer.PlaybackCommand.NEXT:
                    sidx = min(len(sequences) - 1, sidx + 1)
                elif cmd == PyAudioPlayer.PlaybackCommand.PREVIOUS:
                    sidx = max(0, sidx - 1)
                elif cmd == PyAudioPlayer.PlaybackCommand.SETPOSITION:
                    offset = framerate * args[0]
                elif cmd == PyAudioPlayer.PlaybackCommand.SETVOLUME:
                    raise NotImplementedError("Cannot change the volume of a PyAudio stream!")
                elif cmd == PyAudioPlayer.PlaybackCommand.TERMINATE:
                    return
                else:
                    raise NotImplementedError(cmd)

        finally:
            if stream is not None:
                stream.close()
            if pa is not None:
                pa.terminate()

    def __init__(self, paths):
        """
        Launches a new media player. The player is paused immediately after launch.
        :param paths: An iterable of paths to media files and/or playlists. These will form the list of sequences the
                      player is playing.
        """
        super().__init__()

        sequences = []
        sampwidth = None
        nchannels = None
        framerate = None

        for path in resolve_playlist(paths):
            w, c, r, data = load_wav(path)
            if sampwidth is None and nchannels is None and framerate is None:
                sampwidth, nchannels, framerate = w, c, r
            else:
                if w != sampwidth:
                    raise ValueError("PyAudioPlayer requires all audio sequences to have the same sample width!")
                if c != nchannels:
                    raise ValueError("PyAudioPlayer requires all audio sequences to have the same sample width!")
                if r != framerate:
                    raise ValueError("PyAudioPlayer requires all audio sequences to have the same sample width!")
            sequences.append(data)

        self._q = multiprocessing.Queue()
        self._p = multiprocessing.Process(target=PyAudioPlayer._playback, args=(self._q, sequences,
                                                                                sampwidth, nchannels, framerate))
        self._p.start()

        self._status = PlayerStatus.STOPPED
        self._volume = 1
        self._durations = [len(s) / (framerate * nchannels * sampwidth) for s in sequences]
        self._sidx = 0
        self._posat = (0, time.monotonic())

    def _detect_end(self):
        """
        This procedure checks if playback has run over the end of the current sequence,
        in which case it must have stopped.
        """
        if self._status == PlayerStatus.PLAYING:
            pos, at = self._posat
            if pos + (time.monotonic() - at) >= self._durations[self._sidx]:
                self._status = PlayerStatus.STOPPED
                self._posat = (0, time.monotonic())
                self._sidx = min(len(self._durations), self._sidx + 1)

    @property
    async def status(self):
        self._detect_end()
        return self._status

    async def play(self):
        self._detect_end()
        if await self.status != PlayerStatus.PLAYING:
            self._posat = (await self.position, time.monotonic())
            self._q.put((PyAudioPlayer.PlaybackCommand.PLAY, ))
            self._status = PlayerStatus.PLAYING

    async def pause(self):
        self._detect_end()
        if await self.status != PlayerStatus.PAUSED:
            self._posat = (await self.position, time.monotonic())
            self._q.put((PyAudioPlayer.PlaybackCommand.PAUSE, ))
            self._status = PlayerStatus.PAUSED

    async def stop(self):
        self._detect_end()
        if await self.status != PlayerStatus.STOPPED:
            self._q.put((PyAudioPlayer.PlaybackCommand.STOP, ))
            self._posat = (0, time.monotonic())
            self._status = PlayerStatus.STOPPED

    async def next(self):
        self._detect_end()
        self._posat = (0, time.monotonic())
        self._q.put((PyAudioPlayer.PlaybackCommand.NEXT, ))
        self._sidx = min(len(self._durations), self._sidx + 1)

    async def previous(self):
        self._detect_end()
        self._posat = (0, time.monotonic())
        self._q.put((PyAudioPlayer.PlaybackCommand.PREVIOUS, ))
        self._sidx = max(0, self._sidx - 1)

    @property
    async def position(self):
        self._detect_end()
        pos, at = self._posat
        if self._status == PlayerStatus.PLAYING:
            return pos + (time.monotonic() - at)
        else:
            return pos

    @position.setter
    async def position(self, value):
        self._detect_end()
        self._posat = (value, time.monotonic())
        self._q.put((PyAudioPlayer.PlaybackCommand.SETPOSITION, value))

    @property
    async def duration(self):
        self._detect_end()
        return self._durations[self._sidx]

    @property
    async def volume(self):
        return self._volume

    @volume.setter
    async def volume(self, value):
        self._q.put((PyAudioPlayer.PlaybackCommand.SETVOLUME, value))

    def terminate(self):
        self._q.put((PyAudioPlayer.PlaybackCommand.TERMINATE, ))
        self._p.join()
