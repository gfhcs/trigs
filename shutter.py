#!/usr/bin/python3
# coding=utf8

from evdev import InputDevice, ecodes

if __name__ == '__main__':

    shutter = InputDevice('/dev/input/event17')

    EV_VAL_PRESSED = 1
    EV_VAL_RELEASED = 0
    BTN_SHUTTER = 115

    print(shutter)

    for event in shutter.read_loop():
        if (event.type, event.value, event.code) == (ecodes.EV_KEY, EV_VAL_PRESSED, BTN_SHUTTER):
            print('---')
            print("Shutter pressed!")
            print(event)
