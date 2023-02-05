#!/usr/bin/python3
# coding=utf8

import asyncio


async def main():





    # TODO: Discover all connected Bluetooth buttons, with cat /proc/bus/input/devices
    #  Fail gracefully if access permissions are missing.
    #  Make sure that the expected number of buttons are detected.
    #  The following command is the right way to allow me to access the event files: sudo chgrp users /dev/input/event17

    # TODO: Have one central asyncio event queue. Events are dumped into that.

    # TODO: Go into event loop: Get an event from the queue, process it. As a first working hypothesis,
    #       we want button 1 to start playing the next sequence, while button 2 pauses and jumps to before the
    #       beginning of the current sequence. VLC should automatically pause after every sequence.
    #       Every button action is signalled to the display by changing its color and scheduling
    #       a color reset. Before the color reset is scheduler, scheduler.clear should be called.
    #       We also want console output!

    pass


if __name__ == '__main__':
    asyncio.run(main())

