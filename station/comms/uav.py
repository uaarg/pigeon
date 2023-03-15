from abc import ABC, abstractmethod
from dataclasses import field, dataclass
import logging
from typing import Callable

logger = logging.getLogger(__name__)

def noop():
    pass

@dataclass
class Command:
    name: str
    value: int

    def __post_init__(self):
        if " " in self.name: raise ValueError(f"Command name '{self.name}' contains spaces")

    def encode(self) -> bytes:
        return f"{self.name} {self.value}".encode()

class Command_:
    def __init__(self, name, value):
        int(float(value)) # To ensure it's a number
        value = str(value)
        if " " in name:
            raise(ValueError("Command name '%s' contains spaces" % name))
        if " " in value:
            raise(ValueError("Command value '%s' contains spaces" % value))

        self.name = name
        self.value = str(value)

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value

class UAV(ABC):
    """
    UAV abstract class (interface) which represents a communication stream with
    a UAV.

    You probably don't want to construct this class directly, but instead
    should construct the UAVMav class which actually implements the required
    methods. Calling the methods of this.

    If you do not care about the protocol being used, prefer to interact with
    a UAV object which conforms to this abstract class. (You may preform duck
    typing by checking the UAV.is_uav() method).
    """

    @abstractmethod
    def connect(self):
        """
        Attempt to start a connection with the drone.

        This will either complete sucessfully or raise a `ConnectionError`.
        This error may occur if:
         - The connection has already been made
         - The drone could not be contacted
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        If there is an active connection with the drone, close it.
        Otherwise this function is a no-op.

        This should be non-destructive
        """
        pass

    @abstractmethod
    def sendCommand(self, *args, **kwargs):
        """
        Send a command to the UAV. Arguments are passed directly to
        the constructor of the Command class. Command won't be sent
        to the UAV if the same command hasn't been acknowledged yet.
        """
        pass

    @abstractmethod
    def addUAVConnectedChangedCb(self, cb):
        """
        Add a function to be called when the UAV is connected or
        disconnected. Will be called with True or False, indicating
        whether the UAV is connected or not (respectively).

        Will also be called immediately with the current connection
        status.
        """
        pass

    @abstractmethod
    def addCommandAckedCb(self, cb):
        """
        Add a function to be called when the UAV acknowledges a command.
        Will be called with the command name and command value.
        """
        pass

    @abstractmethod
    def addUAVStatusCb(self, cb):
        """
        Add a function to be called when the UAV sends a status message.
        Will be called with a dictionary of the fields and values.
        """
        pass
