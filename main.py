#!/usr/bin/python3
# coding=utf8

import argparse
import asyncio

from trigs.asynchronous import first
from trigs.display import Display
from trigs.error import TrigsError
from trigs.players.pyaudio import PyAudioPlayer, PlayerStatus
from trigs.triggers.bluetooth import BluetoothTrigger, TriggerError
from trigs.triggers.virtual import VirtualTriggerWindow

# region Argument parsing

parser = argparse.ArgumentParser(description='Processes the input events from trigger devices to control a playlist'
                                             'of media files.')

parser.add_argument('playlist', type=str, help='The path to the playlist file that is to be controlled.')

parser.add_argument('--virtual', action='store_true', default=False,
                    help='Instead of expecting bluetooth devices to be connected, show an'
                         'array of virtual triggers that can be activated by mouse click or'
                         'key press.')

# endregion


async def calibrate(display=None, forward_uniq=None, backward_uniq=None):
    """
    Waits for two trigger devices to be connected and asks the user to indicate their roles.
    :param display: The Display object that should be used issue signals during the calibration process.
    :param forward_uniq: The unique and persistent identifier of the device that should be used for the 'forward' trigger.
                         If this is given and connected, the user won't be asked to actively participate in calibration.
    :param backward_uniq: The unique and persistent identifier of the device that should be used for the 'backward' trigger.
                         If this is given and connected, the user won't be asked to actively participate in calibration.
    :return: A pair (forward, backward) of Trigger objects.
    """

    while True:
        triggers = []
        print("Waiting for at least 2 trigger devices to be connected...")

        if display is not None:
            display.set_color(0, (0, 0, 255))
            display.set_color(1, (0, 0, 255))

        while len(triggers) < 2:
            # Close previously discovered trigger objects, because they still might have devices grabbed that 'discover'
            # would try to grab again:
            for t in triggers:
                t.close()
            triggers.clear()

            try:
                triggers = list(BluetoothTrigger.discover())
            except TriggerError:
                print("FAILED TO DISCOVER TRIGGERS. Trying again...")
                pass

            await asyncio.sleep(0.2)

        print("Triggers connected!")

        uniq2trig = {t.uniq: t for t in triggers}

        while True:

            if display is not None:
                display.set_color(0, (0, 0, 255))
                display.set_color(0, (0, 0, 255))

            try:
                forward = uniq2trig[forward_uniq]
            except KeyError:
                try:
                    print("\tPlease trigger 'forward' once!")
                    forward = (await first((t.next() for t in triggers))).source
                    print("\tForward triggered.")
                except TriggerError:
                    print("LOST CONNECTION TO A TRIGGER DURING CALIBRATION!")
                    break

            if display is not None:
                display.set_color(1, (255, 255, 255))

            try:
                backward = uniq2trig[backward_uniq]
            except KeyError:
                try:
                    print("\tPlease trigger 'backward' once!")
                    backward = (await first((t.next() for t in triggers))).source
                    print("\tBackward triggered.")
                except TriggerError:
                    print("LOST CONNECTION TO A TRIGGER DURING CALIBRATION!")
                    break

            if display is not None:
                display.set_color(0, (255, 255, 255))

            if forward is backward:
                print("Cannot use the same trigger for forward and backward! Please try again!")
                continue

            print("CALIBRATION COMPLETE.")
            return forward, backward


async def main():

    args = parser.parse_args()

    def on_window_closed():
        for t in asyncio.all_tasks():
            if t is not asyncio.current_task():
                t.cancel()

    window = None

    try:
        if args.virtual:
            window = VirtualTriggerWindow([("Stop (Key: s)", "s"), ("Next (Key: k)", "k")], on_close=on_window_closed)
        else:
            window = Display(2, on_close=on_window_closed)

        with PyAudioPlayer(paths=[args.playlist]) as player:

            if args.virtual:
                backward, forward = window.triggers
            else:
                forward, backward = await calibrate(display=window)

            while True:

                try:
                    event = await first((forward.next(), backward.next()))
                except TriggerError:
                    if args.virtual:
                        raise
                    else:
                        print("LOST CONNECTION TO AT LEAST ONE TRIGGER!")
                        # Close the triggers, to make sure none of them remain grabbed:
                        fu = forward.uniq
                        bu = backward.uniq
                        forward.close()
                        backward.close()
                        del forward, backward
                        forward, backward = await calibrate(display=window, forward_uniq=fu, backward_uniq=bu)
                        continue

                if event.source is forward:
                    # If this happens while a sequence is still underway, ignore it.
                    if await player.status == PlayerStatus.PLAYING:
                        print("IGNORED FORWARD, because sequence still playing!")
                        continue
                    # Begin with the next sequence:
                    await player.play()
                    await player.play()  # Necessary because of the weird semantics VLC/playerctl give to 'stop'.

                    if not args.virtual:
                        d = await player.duration
                        window.flash(0, (0, 255, 0), duration=d)
                        window.flash(1, (0, 255, 0), duration=d)

                    print("FORWARD!")
                elif event.source is backward:
                    # If this happens while we are NOT playing a sequence, it probably happens while we are paused at
                    # the end of a sequence we just finished. In that case we certainly do not want to jump back to the
                    # beginning:
                    if await player.status != PlayerStatus.PLAYING:
                        print("IGNORED BACKWARD, because we are already stopped!")
                        continue
                    # The previous FORWARD was a mistake and should be undone. Since the only FORWARDs that ever take
                    # effect are those that we receive while we are paused in-between sequences, we just have to stop
                    # playback:
                    await player.stop()

                    if not args.virtual:
                        window.flash(0, (255, 0, 0))
                        window.flash(1, (255, 0, 0))

                    print("UNDO!")
                else:
                    print("UNKNOWN EVENT:", event)

    except TrigsError as te:
        print(str(te))
    except asyncio.exceptions.CancelledError:
        print("Exiting.")
    finally:
        if window is not None:
            window.close()


if __name__ == '__main__':
    asyncio.run(main())

