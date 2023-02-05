import evdev

class Trigger:
    # TODO: Have a class 'Trigger'. It should know the device path to read events from.
    #       It does not need a dedicated thread, because it offers an async interface.
    #       So it can offer the method async def next() for getting the next button press event.

    #  TODO: If permissions are missing, fail with an exception that recommends: sudo chgrp users /dev/input/event17


    @staticmethod
    def discover():
        """
        Discovers all currently connected trigger devices.
        :return: An iterable of Trigger object.
        """
        # TODO: Get the output of "cat /proc/bus/input/devices"
        # TODO: From that output, find the paths to the trigger devices.

    pass