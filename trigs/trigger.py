import os.path

import evdev

from events import Event, unix2mono
import subprocess

_path_discover_shutters = "/usr/local/sbin/trigs_discover_shutters.py"


class TriggerEvent(Event):
    """
    Represent the event of a trigger being triggered.
    """
    def __init__(self, trigger, time_ns):
        """
        Creates a new trigger event.
        :param trigger: The Trigger that raised this event.
        :param time_ns: The time at which the event has occurred, as a nanosecond integer. The reference point is that of
                     time.monotonic_ns.
        """
        if not isinstance(trigger, Trigger):
            raise TypeError("TriggerEvents can only be raised by Triggers!")
        super().__init__(trigger, time_ns)


class Trigger:
    """
    Represents a device that sends only one type of event.
    This class uses the 'evdev' package in order to detect a certain type of Bluetooth controller that is typically
    used as a remote shutter controller for smartphone cameras. This type of device comes in many different shapes
    and sizes, but very often it contains the same core logic.
    """

    @staticmethod
    def discover():
        """
        Discovers all currently connected trigger devices.
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

        for path in lines.splitlines():
            yield Trigger(path.strip())

    def __init__(self, device_path):
        """
        Creates a new Trigger object, representing a hardware device that serves as a 'trigger'.
        :param device_path: The absolute path under which the Linux kernel exposes the input device.
                            Usually under /dev/input/
        """
        try:
            self._device = evdev.InputDevice(device_path)
        except PermissionError as pe:
            global __path_discover_shutters
            raise PermissionError("The device file {} cannot be accessed due to insufficient permissions. "
                                  "This could likely be resolved by running `sudo chgrp users {}`, "
                                  "but it would be better to run {}, assuming that this script "
                                  "has been installed properly using install.sh and that the device path points"
                                  " at a device actually supported by trigs!".format(device_path, device_path,
                                                                                     __path_discover_shutters))
        self._device.grab()

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

        async for event in self._device.async_read_loop():
            if (event.type, event.value, event.code) == (evdev.ecodes.EV_KEY, EV_VAL_PRESSED, BTN_SHUTTER):
                return TriggerEvent(self, unix2mono(event.sec * 10 ** 9 + event.usec * 10 ** 3))

    def close(self):
        """
        Closes this instance.
        """
        if self._device is not None:
            self._device.ungrab()
            self._device.close()
            self._device = None


