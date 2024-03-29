import os.path
import subprocess

import evdev
import asyncio

from .base import Trigger, TriggerEvent, TriggerError
from trigs.events import unix2mono


_path_discover_shutters = "/usr/local/sbin/trigs_discover_shutters.py"


class ReadIterator:
    """
    This class is a hacked copy from site-packages/evdev/eventio_asyncio.py .
    We created this copy to work around an irritating exception message that occurs when the Bluetooth shutter devices
    lose connection while we are waiting for events (see below).
    """
    def __init__(self, device):
        self.current_batch = iter(())
        self.device = device

    def __aiter__(self):
        return self

    def __anext__(self):
        future = asyncio.Future()
        try:
            # Read from the previous batch of events.
            future.set_result(next(self.current_batch))
        except StopIteration:
            def next_batch_ready(batch):
                try:
                    self.current_batch = batch.result()
                    future.set_result(next(self.current_batch))
                except Exception as e:
                    # It can apparently happen that the future is already done at this point.
                    # We observed this to be the case when the bluetooth shutter devices lose connection while we are
                    # waiting for events.
                    # If it *is* the case, future.set_exception will cause an InvalidStateError
                    # that pollutes the console output, but does not actually crash the process (as it affects only
                    # a future that we anyways stopped listening to...)
                    # See https://github.com/gvalkov/python-evdev/issues/123
                    try:
                        future.set_exception(e)
                    except asyncio.InvalidStateError:
                        pass
            self.device.async_read().add_done_callback(next_batch_ready)
        return future


class BluetoothTrigger(Trigger):
    """
    A Bluetooth device that serves as a trigger.
    This class uses the 'evdev' package in order to detect a certain type of Bluetooth controller that is typically
    used as a remote shutter controller for smartphone cameras. This type of device comes in many different shapes
    and sizes, but very often it contains the same core logic.
    """

    __open = []

    @staticmethod
    def discover():
        """
        Discovers all currently connected trigger devices.
        This procedure first invalidates all BluetoothTrigger instances!
        :return: An iterable of Trigger object.
        """

        if not os.path.isfile(_path_discover_shutters):
            raise FileNotFoundError("The file {} does not exist. You should run sudo ./install.sh to create that file"
                                    " as a copy of ./discover_shutters.py that is owned by root added as a NOPASSWORD"
                                    " exception to /etc/sudoers.d .".format(_path_discover_shutters))

        lines = subprocess.run(['sudo', _path_discover_shutters], text=True, stdout=subprocess.PIPE).stdout

        if "password" in lines:
            raise PermissionError("'sudo' is asking for a password to execute {}, even though there should"
                                  " be a rule in /etc/sudoers.d to avoid this. "
                                  "Did you run ./install.sh properly?".format(_path_discover_shutters))

        for t in list(BluetoothTrigger.__open):
            t.close()

        discovered = []
        try:
            for path in lines.splitlines():
                try:
                    t = BluetoothTrigger(path.strip())
                    discovered.append(t)
                except FileNotFoundError as e:
                    raise TriggerError("A trigger that we just discovered seems to have vanished again!", None) from e
                except OSError as e:
                    raise TriggerError("Something wrong with the trigger device, maybe still in use...", None) from e
        except:
            for d in discovered:
                d.close()
            raise

        return discovered

    def __init__(self, device_path):
        """
        Creates a new Trigger object, representing a hardware device that serves as a 'trigger'.
        :param device_path: The absolute path under which the Linux kernel exposes the input device.
                            Usually under /dev/input/
        """

        try:
            d = evdev.InputDevice(device_path)
        except PermissionError as pe:
            global _path_discover_shutters
            raise PermissionError("The device file {} cannot be accessed due to insufficient permissions. "
                                  "This could likely be resolved by running `sudo chgrp users {}`, "
                                  "but it would be better to run {}, assuming that this script "
                                  "has been installed properly using install.sh and that the device path points"
                                  " at a device actually supported by trigs!".format(device_path, device_path,
                                                                                     _path_discover_shutters))
        super().__init__(d.uniq)
        self._device = d
        d.grab()
        BluetoothTrigger.__open.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    async def next(self):
        """
        Waits for this trigger to be used one more time.
        :return: A TriggerEvent.
        """
        if self._device is None:
            raise RuntimeError("This Trigger object has been closed and cannot be used anymore!")

        EV_VAL_PRESSED = 1
        BTN_SHUTTER = 115

        try:
            async for event in ReadIterator(self._device):
                if (event.type, event.value, event.code) == (evdev.ecodes.EV_KEY, EV_VAL_PRESSED, BTN_SHUTTER):
                    return TriggerEvent(self, unix2mono(event.sec * 10 ** 9 + event.usec * 10 ** 3))
        except OSError as e:  # Likely: Bluetooth connection interrupted.
            raise TriggerError("Failed to await an event, likely "
                               "because the connection to the device was interrupted!", self) from e

    def close(self):
        """
        Closes this instance.
        """
        if self._device is not None:
            d = self._device
            self._device = None

            try:
                BluetoothTrigger.__open.remove(self)
                d.ungrab()
                d.close()
            except OSError:
                # Probably the connection broke down.
                pass
