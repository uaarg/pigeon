from concurrent.futures.thread import ThreadPoolExecutor
from dataclasses import field, dataclass
from threading import Lock
from typing import Callable
from concurrent.futures import Future

import logging
import socket
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
class UAVSocket(UAV):
    host: str
    port: int

    # NOTE: A socket only allows us one active transaction at a time, so this
    #       parallelism is overkill. This is just a POC for the mavproxy impl.
    executor = ThreadPoolExecutor(max_workers=1)
    socket_lock: 'Lock | None' = None
    socket: 'socket.socket | None' = None

    conn_changed_cbs: list[Callable] = field(default_factory=list)
    command_acks_cbs: list[Callable] = field(default_factory=list)
    status_cbs: list[Callable] = field(default_factory=list)

    def connect(self):
        if self.socket is not None:
            raise ConnectionError("Connection already exists")

        try:
            sock = socket.socket()
            sock.connect((self.host, self.port))
            sock.setblocking(False)
        except ConnectionRefusedError as err:
            raise ConnectionError(f"Connection refused: {err}")
        except ConnectionResetError as err:
            raise ConnectionError(f"Connection reset: {err}")
        except ConnectionAbortedError as err:
            raise ConnectionError(f"Connection aborted: {err}")
        else:
            self.socket_lock = Lock()
            self.socket = sock
            self._connectionChanged()

    def disconnect(self):
        if self.socket is None: return
        assert self.socket_lock is not None

        self.socket_lock.acquire(blocking=True)

        self.socket.close()
        self.socket = None
        self.socket_lock = None

        self._connectionChanged()

    def addUAVConnectedChangedCb(self, cb):
        self.conn_changed_cbs.append(cb)
        cb(self.connected)

    def addUAVStatusCb(self, cb):
        self.status_cbs.append(cb)

    def addCommandAckedCb(self, cb):
        self.command_acks_cbs.append(cb)


    def sendCommand(self, *args, **kwargs):
        assert self.socket is not None

        command = Command(*args, *kwargs)
        task = self.executor.submit(lambda: self._doSendCommand(command))
        task.add_done_callback(self._commandAcked)


    @property
    def connected(self) -> bool:
        """
        Returns true if there is an active connection on the socket.
        """
        return self.socket is not None

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
        Preform the actual send the command over a socket step. (This will run
        in another thread.)
        """
        assert self.socket is not None
        assert self.socket_lock is not None

        with self.socket_lock:
            self.socket.sendall(command.encode())
            data = self.socket.recv(255)

    # stubbed out for compat. with the UAVMavProxy class
    def setBus(self, _): pass
