#!/usr/bin/python3
# coding=utf8

import argparse
import asyncio

from trigs.asynchronous import first
from trigs.display import Display
from trigs.error import TrigsError
from trigs.player import Player, PlayerStatus
from trigs.trigger import Trigger

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

        while True:
            print("\tPlease trigger 'forward' once!")
            forward = (await first((t.next() for t in triggers))).source
            print("\tForward triggered.")

            print("\tPlease trigger 'backward' once!")
            backward = (await first((t.next() for t in triggers))).source
            print("\tBackward triggered.")

            if forward is backward:
                print("Cannot use the same trigger for forward and backward! Please try again!")
                continue
            break

        print("CALIBRATION COMPLETE.")

        with Player(paths=[args.playlist]) as player, \
                Display(2) as display:
            while True:

                try:
                    event = await first((forward.next(), backward.next(), display.live()))
                except:
                    # TODO: When the triggers lose connection (either distance too large or power save), we should get a
                    #       proper exception from next. We then turn the display to blue and repeat calibration.
                    #       --> For this, calibration should be a dedicated procedure and it should make the left half
                    #           of the display blue as long as the first button is not there and the right half as long as
                    #           the second is missing.
                    raise

                if event.source is display:
                    # Mere GUI update. We don't care.
                    continue
                if event.source is forward:
                    # If this happens while a sequence is still underway, ignore it.
                    if player.status == PlayerStatus.PLAYING:
                        print("IGNORED FORWARD, because sequence still playing!")
                        continue
                    # Begin with the next sequence:
                    player.play()
                    player.play() # Necessary because of the weird semantics VLC/playerctl give to 'stop'.

                    display.flash(0, (0, 255, 0))
                    display.flash(1, (0, 255, 0))

                    print("FORWARD!")
                elif event.source is backward:
                    # If this happens while we are NOT playing a sequence, it probably happens while we are paused at
                    # the end of a sequence we just finished. In that case we certainly do not want to jump back to the
                    # beginning:
                    if player.status != PlayerStatus.PLAYING:
                        print("IGNORED BACKWARD, because we are already stopped!")
                        continue
                    # The previous FORWARD was a mistake and should be undone. Since the only FORWARDs that ever take
                    # effect are those that we receive while we are paused in-between sequences, we just have to stop
                    # playback:
                    player.stop()

                    display.flash(0, (255, 0, 0))
                    display.flash(1, (255, 0, 0))

                    print("UNDO!")
                else:
                    print("UNKNOWN EVENT:", event)

    except TrigsError as te:
        print(str(te))


if __name__ == '__main__':
    asyncio.run(main())

