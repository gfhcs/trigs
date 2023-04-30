#!/usr/bin/python3
# coding=utf8

import argparse
import asyncio
import os
import time

from trigs.asynchronous import first
from trigs.console import begin, done
from trigs.display import Display
from trigs.error import TrigsError
from trigs.players.pyaudio import PyAudioPlayer, PlayerStatus
from trigs.playlist import resolve_playlist, load_wav
from trigs.pulsaudio import pacmdlist
from trigs.remote.player import RemotePlayer
from trigs.remote.protocol import PlayerClient
from trigs.remote.tcp import TCPConnection
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

parser.add_argument('--backward_double', action='store_true', default=False,
                    help='Specifies that the backward trigger needs to be used twice in quick succession to actually'
                         'have an effect. This allows the backward trigger to be used occasionally to prevent it'
                         'from going to powersave mode.')

parser.add_argument('--remote', type=str, nargs=2, help='Instead of launching a local audio player, this will make'
                                                        'the process connect to a trigs server on a remote machine.'
                                                        'You need to give the host name and port number for that machine!')

parser.add_argument('--check_sink', type=str, help='Makes sure that the audio from this process is sent to an audio sink with the given device description.')
parser.add_argument('--check_volume', type=str, help='Makes sure that the sink input used by this process is at the specified volume.')

# endregion


def log(msg):
    print("{} {}".format(time.ctime(), msg))


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
        log("Waiting for at least 2 trigger devices to be connected...")

        if display is not None:
            display.set_color(0, (0, 0, 255))
            display.set_color(1, (0, 0, 255))

        while len(triggers) < 2:
            triggers.clear()

            await asyncio.sleep(0.2)

            try:
                triggers = list(BluetoothTrigger.discover())
            except TriggerError as te:
                log("FAILED TO DISCOVER TRIGGERS: {}. Trying again...".format(str(te)))
                pass


        log("Triggers connected!")

        uniq2trig = {t.uniq: t for t in triggers}

        while True:

            if display is not None:
                display.set_color(0, (0, 0, 255))
                display.set_color(0, (0, 0, 255))

            log("\tPlease trigger 'forward' once!")
            loss = True
            try:
                forward = uniq2trig[forward_uniq]
                await forward.next()
                loss = False
            except KeyError:
                try:
                    forward = (await first((t.next() for t in triggers))).source
                    loss = False
                except TriggerError:
                    pass
            except TriggerError:
                pass

            if loss:
                log("LOST CONNECTION TO A TRIGGER DURING CALIBRATION!")
                break

            log("\tForward triggered.")

            if display is not None:
                display.set_color(1, (255, 255, 255))

            log("\tPlease trigger 'backward' once!")
            loss = True
            try:
                backward = uniq2trig[backward_uniq]
                await backward.next()
                loss = False
            except KeyError:
                try:
                    loss = True
                    backward = (await first((t.next() for t in triggers))).source
                    loss = False
                except TriggerError:
                    pass
            except TriggerError:
                pass

            if loss:
                log("LOST CONNECTION TO A TRIGGER DURING CALIBRATION!")
                break

            log("\tBackward triggered.")

            if display is not None:
                display.set_color(0, (255, 255, 255))

            if forward is backward:
                log("Cannot use the same trigger for forward and backward! Please try again!")
                continue

            log("CALIBRATION COMPLETE.")
            return forward, backward


async def measure_latency(awaitable):
    t0 = time.monotonic_ns()
    try:
        return await awaitable
    finally:
        l = (time.monotonic_ns() - t0) / 10 ** 6
        if l < 1:
            log("Latency: <1ms")
        else:
            log("Latency: {:.1f}ms".format(l))


async def main():

    args = parser.parse_args()

    def on_window_closed():
        for t in asyncio.all_tasks():
            if t is not asyncio.current_task():
                t.cancel()

    window = None
    player = None
    connection = None

    backward_time = None

    try:
        begin("Reading audio sequences")
        sequences = [load_wav(path) for path in resolve_playlist([args.playlist])]
        if len(sequences) == 0:
            raise TrigsError("No usable *.wav files found!")
        else:
            sw, nc, fr = sequences[0][:3]
        done()

        if args.remote is None:
            player = PyAudioPlayer(sw, nc, fr)
        else:
            host, port = args.remote
            begin("Connecting to {}:{}", host, port)
            connection = await TCPConnection.open_outgoing(host, int(port))
            player = RemotePlayer(PlayerClient(connection))
            done()

        begin("Initializing playlist")
        await player.clear_sequences()
        for wav in sequences:
            await player.append_sequence(wav)
        done()

        if not args.virtual and not args.remote:

            d = pacmdlist()

            sink_id = None

            if args.check_sink is not None:
                sinks = next(iter(v for k, v in d.items() if "sink(s)" in k))

                for s in sinks:
                    if s["properties"]["device.description"] == "\"{}\"".format(args.check_sink):
                        # assert s["properties"]["device.bus"] == "\"bluetooth\""
                        if not (s["state"] == "RUNNING"):
                            print("Audio sink is not running!")
                            return
                        if not (s["muted"] == "no"):
                            print("Audio sink is muted!")
                            return
                        _, volume_left, _, volume_right, _ = s["volume"].split("/")
                        if not (volume_left.strip() == volume_right.strip() == "100%"):
                            print("Audio sink should be at volume 100%, but is not!")
                            return
                        sink_id = int(s["index"])
                        break
                if sink_id is None:
                    print("FAILED TO FIND THE AUDIO SINK WITH THE DEVICE DESCRIPTION '{}'".format(args.check_sink))
                    return

            sink_inputs = next(iter(v for k, v in d.items() if "sink input(s)" in k))

            pid = os.getpid()
            found_sink_input = False
            for s in sink_inputs:
                if s["properties"]["application.process.id"] == "\"{}\"".format(pid):
                    if not (s["state"] == "RUNNING"):
                        print("Audio sink input is not running!")
                        return
                    if not (s["muted"] == "no"):
                        print("Audio sink input is muted!")
                        return
                    if sink_id is not None:
                        if not s["sink"].startswith("{} ".format(sink_id)):
                            print("This process is sending audio to a sink other than the requested {}!!!".format(args.check_sink))
                            return
                    _, volume_left, _, volume_right, _ = s["volume"].split("/")
                    if args.check_volume and not (volume_left.strip() == volume_right.strip() == "{}%".format(args.check_volume)):
                        print("Audio sink should be at volume {}%, but is not!".format(args.check_volume))
                        return
                    found_sink_input = True
                    break

            if not found_sink_input:
                print("Did not find a PulseAudio sink input for my process!")
                return

        if args.virtual:
            window = VirtualTriggerWindow([("Stop (Key: s)", "s"), ("Next (Key: k)", "k")], on_close=on_window_closed)
        else:
            window = Display(2, on_close=on_window_closed)

        if args.virtual:
            backward, forward = window.triggers
        else:
            forward, backward = await calibrate(display=window)

        while True:

            try:
                event = await first((forward.next(), backward.next()))
            except TriggerError as te:
                if args.virtual:
                    raise
                else:
                    log("LOST CONNECTION TO THE '{}' TRIGGER!".format("FORWARD" if te.trigger is forward else "BACKWARD"))
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
                    log("IGNORED FORWARD, because sequence still playing!")
                    continue
                # Begin with the next sequence:
                await measure_latency(player.play())

                if not args.virtual:
                    d = await player.duration
                    window.flash(0, (0, 255, 0), duration=d)
                    window.flash(1, (0, 255, 0), duration=d)

                log("FORWARD!")
            elif event.source is backward:
                now = time.monotonic_ns()
                delta = None if backward_time is None else (now - backward_time) / 10 ** 9
                backward_time = now

                if args.backward_double:
                    if delta is None or delta > 0.5:
                        continue

                if await player.status != PlayerStatus.PLAYING:
                    # If this happens while we are NOT playing a sequence, it happens while we are sitting in-between two
                    # sequences. We then want to jump back to the predecessor sequence:
                    await measure_latency(player.previous())

                    if not args.virtual:
                        window.flash(0, (255, 0, 0))
                        window.flash(1, (255, 0, 0))

                    log("BACKWARD!")
                else:
                    # The previous FORWARD was a mistake and should be undone. Since the only FORWARDs that ever take
                    # effect are those that we receive while we are paused in-between sequences, we just have to stop
                    # playback:
                    await measure_latency(player.stop())

                    if not args.virtual:
                        window.flash(0, (255, 0, 0))
                        window.flash(1, (255, 0, 0))

                    log("UNDO!")
            else:
                log("UNKNOWN EVENT:", event)

    except TrigsError as te:
        log(str(te))
    except asyncio.exceptions.CancelledError:
        log("Exiting.")
    finally:
        if window is not None:
            window.close()
        if player is not None:
            await player.terminate()
        if connection is not None:
            connection.close()


if __name__ == '__main__':
    asyncio.run(main())

