#!/usr/bin/python3
# coding=utf8

import subprocess

# List input devices and their properties:
lines = subprocess.run(['cat', '/proc/bus/input/devices'],
                       encoding='utf8', stdout=subprocess.PIPE).stdout
lines = iter(lines.splitlines())

# Search for the shutter devices:
in_segment = False
while True:
    try:
        line = next(lines)
    except StopIteration:
        break

    if in_segment:
        if len(line.strip()) == 0 or line.startswith("I:"):
            in_segment = False
        elif line.startswith("H: "):
            path = "/dev/input/{}".format(line[line.index("event"):].strip())
            print(path)

            # Make the device available to all users:
            subprocess.run(['chgrp', 'users', path])
        else:
            pass
    else:
        if line.startswith("N: ") and "Shutter" in line and "Control" in line:
            in_segment = True
        else:
            pass







