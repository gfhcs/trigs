import io
import time

import pyaudio

from .base import Player, PlayerStatus


class PyAudioPlayer(Player):
    """
    A player based on pyaudio.
    """

    def __init__(self, sampwidth, nchannels, framerate, interval=1/100):
        """
        Launches a new audio player based on PyAudio (and thus libportaudio).
        """
        super().__init__()

        self._status = PlayerStatus.STOPPED
        self._volume = 1
        self._sequences = []
        self._sidx = 0
        self._swncfr = (sampwidth, nchannels, framerate)
        self._offsetat = (0, time.monotonic())
        self._pa = pyaudio.PyAudio()
        self._buffer = io.BytesIO()
        self._frames_per_buffer = int(framerate * interval)

        self._stream = self._pa.open(format=self._pa.get_format_from_width(sampwidth),
                         channels=nchannels,
                         rate=framerate,
                         frames_per_buffer=self._frames_per_buffer,
                         stream_callback=self._produce,
                         output=True)

    def _produce(self, _, frame_count, time_info, status):
        now = time.monotonic()
        sw, nc, fr = self._swncfr
        self._buffer.seek(0, io.SEEK_SET)
        bs = b''
        offset, _ = self._offsetat
        if self._status == PlayerStatus.PLAYING:
            bs = self._sequences[self._sidx][offset:offset + frame_count * nc * sw]
            if len(bs) < frame_count * nc * sw: # We've reached the end of the current sequence!
                # Stop playback:
                self._status = PlayerStatus.STOPPED
                self._offsetat = (0, now)
                self._sidx = min(len(self._sequences), self._sidx + 1)
            else:
                self._offsetat = (offset + len(bs),
                                  now + (time_info['output_buffer_dac_time'] - time_info['current_time']))

        elif self._status == PlayerStatus.STOPPED:
            self._offsetat = (0, now)
        elif self._status == PlayerStatus.PAUSED:
            self.offsetat = (offset, now)

        self._buffer.write(bs)

        self._buffer.write(b'\00' * ((self._frames_per_buffer - len(bs)) * nc * sw))
        r = self._buffer.getvalue()
        assert len(r) == frame_count * nc * sw
        return (r, pyaudio.paContinue)

    async def append_sequence(self, data):
        if len(data) != 4:
            raise ValueError("The given sequence should be a 4-tuple holding WAV information and samples!")
        (*swncfr, data) = data
        if not isinstance(data, bytes):
            raise ValueError("The last entry of the 4-tuple must be a 'bytes' object!")

        if tuple(swncfr) != self._swncfr:
            raise ValueError("The given WAV sequence has sample width {}, {} channels and framerate {}, "
                             "but this player has initialized its audio stream "
                             "for sample width {}, {} channels and framerate {}".format(*swncfr, *self._swncfr))
        self._sequences.append(data)

    async def remove_sequence(self, sidx):
        if self._sidx == sidx:
            await self.stop()
        self._sequences.remove(sidx)

    async def clear_sequences(self):
        await self.stop()
        self._sequences.clear()
        self._sidx = 0

    @property
    async def num_sequences(self):
        return len(self._sequences)

    async def get_sequence(self, sidx):
        return self._sequences[sidx]

    @property
    async def status(self):
        return self._status

    async def play(self):
        self._status = PlayerStatus.PLAYING
        self._offsetat = (self._offsetat[0], time.monotonic())

    async def pause(self):
        self._status = PlayerStatus.PAUSED
        self._offsetat = (self._offsetat[0], time.monotonic())

    async def stop(self):
        self._status = PlayerStatus.STOPPED
        self._offsetat = (0, time.monotonic())

    async def next(self):
        self._sidx = min(self.num_sequences - 1, self._sidx + 1)
        self._offsetat = (0, time.monotonic())

    async def previous(self):
        self._sidx = max(0, self._sidx - 1)
        self._offsetat = (0, time.monotonic())

    @property
    async def position(self):
        offset, at = self._offsetat
        sw, nc, fr = self._swncfr
        pos = offset / (sw * nc * fr)
        if self._status == PlayerStatus.PLAYING:
            return pos + (time.monotonic() - at)
        else:
            return pos

    async def set_position(self, pos):
        sw, nc, fr = self._swncfr
        self._offsetat = (int(pos * fr) * (sw * nc), time.monotonic())
        if self._status == PlayerStatus.STOPPED and self._offsetat[0] > 0:
            self._status = PlayerStatus.PAUSED

    @property
    async def duration(self):
        sw, nc, fr = self._swncfr
        return len(self._sequences[self._sidx]) / (sw * nc * fr)

    @property
    async def volume(self):
        return self._volume

    async def set_volume(self, value):
        raise NotImplementedError("Cannot change the volume of a PyAudio stream!")

    async def terminate(self):
        if self._stream is not None:
            self._stream.close()
            self._stream = None
        if self._pa is not None:
            self._pa.terminate()
            self._pa = None
