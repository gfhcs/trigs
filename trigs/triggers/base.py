import abc

from trigs.events import Event


class TriggerEvent(Event):
    """
    Represent the event of a trigger being triggered.
    """
    def __init__(self, trigger, time_ns):
        """
        Creates a new trigger event.
        :param trigger: The Trigger that raised this event.
        :param time_ns: The time at which the event has occurred, as a nanosecond integer. The reference point is that of
                     time.monotonic_ns.
        """
        if not isinstance(trigger, Trigger):
            raise TypeError("TriggerEvents can only be raised by Triggers!")
        super().__init__(trigger, time_ns)


class TriggerError(Exception):
    """
    An error that occurs when a trigger device fails to wait for a new event.
    """
    pass


class Trigger(abc.ABC):
    """
    Represents a device that sends only one type of event.
    """

    def __init__(self, unique_identifier):
        """
        Creates a new Trigger object, representing a hardware device that serves as a 'trigger'.
        :param unique_identifier: A unique identifier for this device. Must be a string.
        """
        self._uniq = unique_identifier

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def uniq(self):
        """
        A unique and persistent identifier for the device that this Trigger represents.
        :return: A string.
        """
        return self._uniq

    @abc.abstractmethod
    async def next(self):
        """
        Waits for this trigger to be used one more time.
        :return: A TriggerEvent.
        :exception TriggerError: If the device causes any error.
        """
        pass

    @abc.abstractmethod
    def close(self):
        """
        Closes this instance.
        """
        pass
