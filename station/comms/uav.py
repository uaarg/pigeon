from dataclasses import field, dataclass
from typing import Any, Callable

from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink2
from threading import Lock, Thread
import time
import logging
import queue

from .services.common import StatusEchoService, HearbeatService
from .services.imagesservice import ImageService
from .services.command import Command

logger = logging.getLogger(__name__)

class ConnectionError(Exception):
    """
    An error which may occur when constructing or communicating with a socket
    via the UAVSocket class.
    """
    def __init__(self, message):
        super().__init__(message)

@dataclass
class UAV:
    device: str
    im_queue: queue.Queue
    feature_queue: Any

    event_loop: Thread | None = None
    conn_lock: 'Lock | None' = None
    conn: 'mavutil.mavfile | None' = None

    commands: queue.Queue = queue.Queue()

    conn_changed_cbs: list[Callable] = field(default_factory=list)
    command_acks_cbs: list[Callable] = field(default_factory=list)
    status_cbs: list[Callable] = field(default_factory=list)

    def connect(self):
        """
        Attempt to start a connection with the drone.

        This will either complete sucessfully or raise a `ConnectionError`.
        This error may occur if:
         - The connection has already been made
         - The drone could not be contacted
        """
        if self.conn is not None:
            raise ConnectionError("Connection already exists")

        try:
            serial_device = "usb" in self.device.lower()
            if serial_device:
                # set the baud rate for serial connections
                conn: mavutil.mavfile = mavutil.mavlink_connection(self.device, 57600)
            else:
                conn: mavutil.mavfile = mavutil.mavlink_connection(self.device)
        except ConnectionRefusedError as err:
            raise ConnectionError(f"Connection refused: {err}")
        except ConnectionResetError as err:
            raise ConnectionError(f"Connection reset: {err}")
        except ConnectionAbortedError as err:
            raise ConnectionError(f"Connection aborted: {err}")
        else:
            self.conn_lock = Lock()
            self.conn = conn
            self._connectionChanged()

            self.thread = Thread(target=lambda: self._runEventLoop(), args=[])
            self.thread.start()

    def disconnect(self):
        """
        If there is an active connection with the drone, close it.
        Otherwise this function is a no-op.

        This should be non-destructive
        """
        if self.conn is None: return
        assert self.conn_lock is not None

        self.conn_lock.acquire(blocking=True)

        self.conn.close()
        self.conn = None
        self.conn_lock = None

        self._connectionChanged()

    def addUAVConnectedChangedCb(self, cb):
        """
        Add a function to be called when the UAV is connected or
        disconnected. Will be called with True or False, indicating
        whether the UAV is connected or not (respectively).

        Will also be called immediately with the current connection
        status.
        """
        self.conn_changed_cbs.append(cb)
        cb(self.connected)

    def addUAVStatusCb(self, cb):
        """
        Add a function to be called when the UAV sends a status message.
        Will be called with a dictionary of the fields and values.
        """
        self.status_cbs.append(cb)

    def addCommandAckedCb(self, cb):
        """
        Add a function to be called when the UAV acknowledges a command.
        Will be called with the command name and command value.
        """
        self.command_acks_cbs.append(cb)

    def sendCommand(self, *args, **kwargs):
        """
        Send a command to the UAV. Arguments are passed directly to
        the constructor of the Command class. Command won't be sent
        to the UAV if the same command hasn't been acknowledged yet.
        """
        assert self.conn is not None

        command = Command(*args, *kwargs)
        self.commands.put(command)

    @property
    def connected(self) -> bool:
        """
        Returns true if there is an active connection open.
        """
        return self.conn is not None

    def _connectionChanged(self):
        """
        Notify all listeners via the connection changed callback about a
        connection changed event.
        """
        connected = self.connected
        for cb in self.conn_changed_cbs:
            cb(connected)

    def _commandAcked(self):
        """
        Notify all listeners via the command ACKed callback about a command
        ACKed event.
        """
        for cb in self.command_acks_cbs:
            cb()

    def _recvStatus(self, status):
        """
        Notify all listeners via the command ACKed callback about a command
        ACKed event.
        """
        for cb in self.status_cbs:
            cb(status)

    def _runEventLoop(self):
        assert self.conn is not None

        # The UAV protocols are quite complex. We have many independent tasks
        # which must share and operate according to changes in the mavlink
        # connection. We split each of these tasks into services which can plug
        # into the event loop via their `recv_message` and `tick` methods.

        # The UI may also send commands from various locations. We make sure to
        # forward those commands as they come in through the `command` queue.

        services = [
            HearbeatService(self.commands, self.disconnect),
            ImageService(self.commands, self.im_queue),
            StatusEchoService(self._recvStatus),
        ]

        while self.connected:
            for service in services:
                service.tick()

            msg = self.conn.recv_match(blocking=False)
            if msg:
                for service in services:
                    service.recv_message(msg)

            try:
                command = self.commands.get(block=False)
                self.conn.write(command.encode(self.conn))
            except queue.Empty:
                pass

            time.sleep(0.0001) # s = 100us
