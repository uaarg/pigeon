from dataclasses import field, dataclass
from typing import Callable

from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from pymavlink import mavutil
from threading import Lock
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
    executor = ThreadPoolExecutor(max_workers=1)
    conn_lock: 'Lock | None' = None
    conn: 'mavutil.mavfile | None' = None

    conn_changed_cbs: list[Callable] = field(default_factory=list)
    command_acks_cbs: list[Callable] = field(default_factory=list)
    status_cbs: list[Callable] = field(default_factory=list)

    def connect(self):
        if self.conn is not None:
            raise ConnectionError("Connection already exists")

        try:
            conn: mavutil.mavfile = mavutil.mavlink_connection(self.device)
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
        task = self.executor.submit(lambda: self._doSendCommand(command))
        task.add_done_callback(self._commandAcked)

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

    def _commandAcked(self, _future: Future[None]):
        """
        Notify all listeners via the command ACKed callback about a command
        ACKed event.
        """
        for cb in self.command_acks_cbs:
            cb()

    def _doSendCommand(self, command: Command):
        """
        Preform the actual send the command over the mavlink connection. (This will run
        in another thread.)
        """
        assert self.conn is not None
        assert self.conn_lock is not None

        with self.conn_lock:
            self.conn.write(command.encode())
            data = self.conn.recv(255)

            # Transmit outgoing messages
            self.conn.send_message(command.encode())

            # Block waiting for incoming message
            msg = conn.recv_match(type='CUSTOM')
            if msg and msg.get_type() != 'BAD_TYPE':
                print(msg)

    # stubbed out for compat. with the UAVMavProxy class
    def setBus(self, _): pass
