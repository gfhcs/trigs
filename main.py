#!/usr/bin/python3
# coding=utf8

import argparse
import asyncio

from trigs.asynchronous import first
from trigs.error import TrigsError
from trigs.player import Player
from trigs.scheduler import Scheduler
from trigs.trigger import Trigger
from trigs.display import Display

# region Argument parsing

parser = argparse.ArgumentParser(description='Processes the input events from trigger devices to control a playlist'
                                             'of media files.')

parser.add_argument('playlist', type=str, help='The path to the playlist file that is to be controlled.')

# endregion


async def main():

    args = parser.parse_args()

    try:

        triggers = list(Trigger.discover())

        if len(triggers) < 2:
            raise TrigsError("Fewer than 2 trigger devices have been detected!")

        print("CALIBRATION:")

        print("\tPlease trigger 'forward' once!")
        forward = await first((t.next() for t in triggers))
        print("\tForward triggered.")

        print("\tPlease trigger 'backward' once!")
        backward = await first((t.next() for t in triggers))
        print("\tBackward triggered.")

        print("CALIBRATION COMPLETE.")

        display_scheduler = Scheduler()
        player_scheduler = Scheduler()

        with Player(paths=[args.playlist]) as player, \
                Display() as display:
            while True:

                event = await first((forward.next(), backward.next(), display_scheduler.next(), player_scheduler.next()))

                print(event)

                # TODO: If it's a forward event, call player.next(). Then enqueue an event that makes us pause the
                #  player after the duration of the sequence that is playing! This duration can probably be queried
                #  via playerctl. Indicate on the display by flashing it green.

                # TODO: If it's a backward event, call player.pause() and then player.prev() and then player.next()
                #       Indicate on the display by flashing it red.

                # TODO: Make sure that before scheduling something, we first clear the respective scheduler of previously
                #       scheduled stuff!

                # TODO: Also log events on the console!

    except TrigsError as te:
        print(str(te))


if __name__ == '__main__':
    asyncio.run(main())

