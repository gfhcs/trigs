#!/usr/bin/python3
# coding=utf8

import asyncio


async def main():

    # TODO: Have a class 'Trigger'. It should know the device path to read events from.
    #       It should have its own thread that listens to events. It should know an event queue
    #       that it dumps events into, with a time stamp.

    # TODO: Have a class 'Player'. It should represent a VLC process. It is initialized with
    #       the path to a playlist file that VLC opens. We will use playerctl. It should make sure that loop status is 'None'
    #       and that 'shuffle' is "Off". Use --player=vlc

    # TODO: Have a class 'Display'.
    #  Under the hood it creates a separate process that  displays a Tkinter window with a certain color.
    #  The color can be changed and there can be text displayed. The window should be full-screenable.
    #  The separate process receives commands via a queue. It listens to that queue and reacts to commands.
    #

    # TODO: Have one class 'Scheduler'. Its contructor receives an event queue to fire
    #       events into.
    #       There is a method 'submit' that takes an event and a (relative) time stamp.
    #       This method creates a task that waits until the time stamp has expired and then
    #       enqueues the event into the event queue. The task must be created with asyncio's
    #       'create_task' and then kept around in the Scheduler, such that it is not deallocated.
    #       The last step in each task is to remove itself from the list of tasks.
    #       There should also be a method 'clear' that unschedules all pending tasks.

    # TODO: Discover all connected Bluetooth buttons.
    #  Fail gracefully if access permissions are missing.
    #  Make sure that the expected number of buttons are detected.

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

