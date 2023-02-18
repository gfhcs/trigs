import asyncio
import itertools
import math
import time
import tkinter
from tkinter import Tk

from .base import Trigger, TriggerEvent, TriggerError


class VirtualTriggerWindow:
    """
    A graphical window showing multiple virtual triggers. They can be activated by mouse click or key press.
    """

    class VirtualTrigger(Trigger):
        """
        A trigger that does not exist physically, but is emulated in software. It can be activated by mouse click or key press.
        """

        def __init__(self, ):
            """
            Creates a new VirtualTrigger.
            """
            super().__init__(str(id(self)))
            self._futures = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

        def activate(self):
            """
            Activates this trigger, i.e. makes it register an event.
            """
            t = time.monotonic_ns()
            ff = None
            for f in self._futures:
                if not f.done():
                    ff = f
            if ff is None:
                ff = asyncio.Future()

            ff.set_result(TriggerEvent(self, t))

        async def next(self):
            """
            Waits for this trigger to be used one more time.
            :return: A TriggerEvent.
            """

            if len(self._futures) == 0:
                self._futures.append(asyncio.Future())

            f = self._futures[0]

            try:
                r = await f
            finally:
                if len(self._futures) > 0 and self._futures[0] is f:
                    self._futures.pop(0)

            return r

        def close(self):
            """
            Closes this instance.
            """
            for f in self._futures:
                f.set_exception(TriggerError("The virtual trigger was closed!"))
            self._futures.clear()

    def __init__(self, lkpairs, width=1200, height=860, title="Virtual triggers"):
        """
        Initializes a new array of virtual triggers.
        :param lkpairs: An iterable of pairs (label, k), where 'label' is a string labelling a virtual trigger and
                        'k' is the character to be pressed on the keyboard to activate that trigger.
                        There will be as many triggers as there are lkpairs given.
        :param width: The initial width of this window.
        :param height: The initial height of this window.
        :param title: The title of this window.
        """
        super().__init__()

        lkpairs = tuple(lkpairs)
        num_triggers = len(lkpairs)

        n = num_triggers ** 0.5
        root_n = int(math.ceil(n))
        if num_triggers == 1:
            num_cols, num_rows = 1, 1
        elif num_triggers == 2:
            num_cols, num_rows = 2, 1
        else:
            num_cols, num_rows = root_n, root_n

        root = Tk()
        root.geometry("{}x{}".format(width, height))
        root.rowconfigure(tuple(range(num_rows)), weight=1)
        root.columnconfigure(tuple(range(num_cols)), weight=1)

        self._triggers = {}
        self._buttons = []
        for (label, key), (x, y) in zip(lkpairs, itertools.product(range(num_cols), range(num_rows))):
            t = VirtualTriggerWindow.VirtualTrigger()
            b = tkinter.Button(root, text=label, command=t.activate)
            b.grid(row=y, column=x, sticky='NSEW')
            self._buttons.append(b)
            if key is not None:
                self._triggers[key] = t

        root.title(title)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.focus_set()
        root.bind("<KeyPress>", self._keydown)

        self._window = root

    def _keydown(self, event):
        try:
            self._triggers[event.char].activate()
        except KeyError:
            pass

    @property
    def triggers(self):
        return tuple(self._triggers.values())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    async def live(self, wait=1 / 60):
        """
        Makes the display process all outstanding GUI events.
        This method needs to be called often, to keep the GUI responsive.
        :param wait: The number of seconds to wait before this call actually enters the event loop. This can be useful to limit
                     the frequency with which this method is actually executed.
        """
        await asyncio.sleep(wait)

        if self._window is None:
            raise RuntimeError("The virtual trigger window has been closed!")

        self._window.update()

    async def life(self, wait=1 / 60):
        """
        Calls VirtualTriggerWindow.live in an infinite loop. This method is useful for creating an asyncio task that regularly
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
