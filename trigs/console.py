import sys


def begin(msg, *fargs):
    """
    Writes the given message to the console, without a line break.
    :param msg: The message to write. This may be a format string.
    :param fargs: The arguments that should be inserted into the msg format string.
    """
    sys.stdout.write(msg.format(*fargs))
    sys.stdout.write("...")


def done():
    """
    Writes 'Done.\n' to the console.
    """
    sys.stdout.write("Done.\n")
