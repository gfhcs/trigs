import time


def unix2mono(ns):
    """
    Converts a UNIX time stamp into a time stamp that is relative to the reference time of time.monotonic_ns.
    The conversion is subject to minor errors.
    :param ns: A number of nanoseconds since the epoch.
    :return: A number of nanoseconds since the reference of time.monotonic_ns.
    """
    t0 = time.perf_counter_ns()
    time_since_epoch = time.time_ns()
    time_since_reference = time.monotonic_ns()
    t1 = time.perf_counter_ns()

    shift = time_since_reference - time_since_epoch - (t1 - t0) // 2

    return ns + shift


class Event:
    """
    An event that occurred asynchronously.
    """

    def __init__(self, source, time_ns=None):
        """
        Creates a new event object.
        :param source: The Object that is the source of this event.
        :param time_ns: The time at which the event has occurred, as a nanosecond integer. The reference point is that of
                     time.monotonic_ns, as that is the function that will be called to obtain this value should it be
                     omitted.
        """

        if time_ns is None:
            time_ns = time.monotonic_ns()

        super().__init__()
        self._source = source
        self._time_ns = time_ns

    @property
    def source(self):
        """
        The Object that is the source of this event.
        """
        return self._source

    @property
    def time_ns(self):
        """
        The time at which the event has occurred, as a nanosecond integer. The reference point is that of
        time.monotonic_ns.
        """
        return self._time_ns

    def __str__(self):
        return "Event from {}".format(self._source)