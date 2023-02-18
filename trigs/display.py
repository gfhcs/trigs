import asyncio
import time
import tkinter
from tkinter import Tk, Frame, LEFT, RIGHT, BOTH
import itertools
import math
from .events import Event


class DisplayUpdate(Event):
    """
    An event that occurs immediately after a display has updated itself.
    """
    def __init__(self, display):
        super().__init__(display, time.monotonic_ns())


class Display:
    """
    A display is a graphical window on the screen that is divided into a number of colored segments.
    The window does not take any input.
    """

    def __init__(self, num_segments, width=1200, height=860, title="trigs"):
        """
        Initializes a new graphical display.
        :param num_segments: The number of segments that the display is to be partitioned into.
        :param width: The initial width of this display.
        :param height: The initial height of this display.
        :param title: The title of this display window.

        """
        super().__init__()

        self._colors = [(255, ) * 3, ] * num_segments
        self._resets = [None, ] * num_segments

        n = num_segments ** 0.5
        root_n = int(math.ceil(n))
        if num_segments == 1:
            num_cols, num_rows = 1, 1
        elif num_segments == 2:
            num_cols, num_rows = 2, 1
        else:
            num_cols, num_rows = root_n, root_n

        root = Tk()
        root.geometry("{}x{}".format(width, height))
        root.rowconfigure(tuple(range(num_rows)), weight=1)
        root.columnconfigure(tuple(range(num_cols)), weight=1)

        self._canvases = []
        for x, y in itertools.product(range(num_cols), range(num_rows)):
            c = tkinter.Canvas(root, background='white')
            c.grid(row=y, column=x, sticky='NSEW')
            self._canvases.append(c)

        root.title(title)
        root.protocol("WM_DELETE_WINDOW", self.close)

        self._window = root

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    async def live(self, wait=1/60):
        """
        Makes the display process all outstanding GUI events.
        This method needs to be called often, to keep the GUI responsive.
        :param wait: The number of seconds to wait before this call actually enters the event loop. This can be useful to limit
                     the frequency with which this method is actually executed.
        :return: A DisplayUpdate object.
        """
        await asyncio.sleep(wait)

        if self._window is None:
            raise RuntimeError("The display has been closed!")

        # Execute pending resets:
        t = time.monotonic_ns()
        for sidx, reset in enumerate(list(self._resets)):
            if reset is not None:
                rgb, rtime = reset
                if t >= rtime:
                    self._set_color(sidx, rgb, check=False, cancel_reset=False)
                    self._resets[sidx] = None

        self._window.update()
        return DisplayUpdate(self)

    async def life(self, wait=1/60):
        """
        Calls Display.live in an infinite loop. This method is useful for creating an asyncio task that regularly
        updates the display GUI.
        :param wait: The number of seconds to wait in-between updates. Values that are too large will make the GUI laggy,
                     values that are too small will needlessly burn compute power and slow down asyncio.
        """
        while True:
            await self.live(wait=wait)

    def close(self):
        if self._window is not None:
            self._window.destroy()
            self._window = None

    @property
    def colors(self):
        """
        The colors of the segments of this display.
        :return: A tuple of triples: There is one triple per segment and each triple encodes color as RGB values from
                 range 0 to 255.
        """
        return tuple(self._colors)

    @colors.setter
    def colors(self, value):

        if len(value) != len(self._colors):
            raise ValueError("The given tuple has {} entries, but this display has {} segments!".format(len(value), len(self._colors)))

        for sidx, rgb in enumerate(value):
            self.set_color(sidx, rgb)

    def _set_color(self, sidx, rgb, check=True, cancel_reset=True):
        """
        Sets the color of one segment.
        :param sidx: The index of the segment to set the color for.
        :param rgb: The color to set the segment to.
        :param check: Whether the 'rgb' input should be checked for validity.
        :param cancel_reset: Whether this call should cancel any pending color reset for the given segment.
        """

        if check:
            if len(rgb) != 3:
                raise ValueError("Colors must be specified as RGB tuples, which {} is not!".format(rgb))

            for x in rgb:
                if not (isinstance(x, int) and 0 <= x <= 255):
                    raise ValueError("RGB values must be nonnegative integers no larger than 255!")

        self._colors[sidx] = rgb

        if cancel_reset:
            self._resets[sidx] = None

        self._canvases[sidx].configure(background='#{:02x}{:02x}{:02x}'.format(*rgb))

    def set_color(self, sidx, rgb):
        """
        Sets the color of one segment.
        :param sidx: The index of the segment to set the color for.
        :param rgb: The color to set the segment to.
        """
        self._set_color(sidx, rgb)

    def flash(self, sidx, rgb, duration=0.5):
        """
        Makes a segment temporarily change its color.
        :param sidx: The index of the segment to flash.
        :param rgb: The color that should be shown temporarily.
        :param duration: The duration for which the given color should be shown.
        """

        # First take note of the "original" color that we need to reset the segment to.
        # If there already is a reset color, then that's the one we want.
        try:
            old, _ = self._resets[sidx]
        except TypeError:  # self._resets[sidx] is None
            old = self._colors[sidx]

        self.set_color(sidx, rgb)

        # Schedule a reset:
        self._resets[sidx] = (old, time.monotonic_ns() + int(duration * 10 ** 9))
