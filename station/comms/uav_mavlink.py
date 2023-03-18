from dataclasses import field, dataclass
from time import sleep
from typing import Callable

from pymavlink import mavutil
from threading import Lock, Thread
import logging
import queue

from .uav import UAV, Command

logger = logging.getLogger(__name__)

class ConnectionError(Exception):
    """
    An error which may occur when constructing or communicating with a socket
    via the UAVSocket class.
    """
    def __init__(self, message):
        super().__init__(message)

@dataclass
class UAVMavLink(UAV):
    device: str
    event_loop: Thread | None = None
    conn_lock: 'Lock | None' = None
    conn: 'mavutil.mavfile | None' = None

    commands: queue.Queue = queue.Queue()

    conn_changed_cbs: list[Callable] = field(default_factory=list)
    command_acks_cbs: list[Callable] = field(default_factory=list)
    status_cbs: list[Callable] = field(default_factory=list)

    def connect(self):
        if self.conn is not None:
            raise ConnectionError("Connection already exists")

        try:
            conn: mavutil.mavfile = mavutil.mavlink_connection(self.device)

            # The protocol mandates that the client send the first heartbeat
            # and then listens for a heartbeat response from the drone.
            conn.mav.heartbeat_send(
                type=mavutil.mavlink.MAV_TYPE_GENERIC,
                autopilot=mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                base_mode=0,
                custom_mode=0,
                system_status=0)
            conn.wait_heartbeat()
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
        if self.conn is None: return
        assert self.conn_lock is not None

        self.conn_lock.acquire(blocking=True)

        self.conn.close()
        self.conn = None
        self.conn_lock = None

        self._connectionChanged()

    def addUAVConnectedChangedCb(self, cb):
        self.conn_changed_cbs.append(cb)
        cb(self.connected)

    def addUAVStatusCb(self, cb):
        self.status_cbs.append(cb)

    def addCommandAckedCb(self, cb):
        self.command_acks_cbs.append(cb)


    def sendCommand(self, *args, **kwargs):
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

    def _runEventLoop(self):
        assert self.conn is not None

        while True:
            msg = self.conn.recv_match(blocking=False)
            if msg:
                if msg.get_type() == 'BAD_TYPE':
                    print("WARN: Recv bad message: ", msg)
                    continue

                print("GOT MESSAGE: of type", msg.get_type())
                print("DATA:", msg.to_dict())

            try:
                command = self.commands.get(block=False)
                self.conn.write(command.encode()) # TODO: actually send the command properly
                print(command)
            except queue.Empty:
                pass

            sleep(0.01) # s = 10ms

    # stubbed out for compat. with the UAVMavProxy class
    def setBus(self, _): pass
