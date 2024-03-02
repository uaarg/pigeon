from typing import Callable

from pymavlink.dialects.v20 import common as mavlink2
import time
import queue

from .command import Command


class MavlinkService:

    def recv_message(self, message: mavlink2.MAVLink_message):
        """
        This runs whenever a message is received and the service can then be
        allowed to (conditionally) handle that message.
        """
        pass

    def tick(self):
        """
        This item runs at least once every 10ms. This can be used by services
        which may want to implement timeouts or regular message sending.
        """
        pass


class HearbeatService(MavlinkService):
    """
    Heartbeat Service
    =================

    We send a heartbeat at the interval given by `1/heartbeat_freq`. We also
    make sure that we have received a heartbeat within at least
    15/`heartbeat_freq`. If it takes longer, then we consider the drone to have
    disconnected.
    """
    last_sent_heartbeat: float
    last_recv_heartbeat: float
    heartbeat_interval: float
    disconnect: Callable
    commands: queue.Queue

    def __init__(self,
                 commands: queue.Queue,
                 disconnect: Callable,
                 timeout: int = 15,
                 heartbeat_freq: float = 1):
        self.commands = commands
        self.disconnect = disconnect
        self.heartbeat_interval = 1 / heartbeat_freq
        self.last_sent_heartbeat = time.time()
        self.last_recv_heartbeat = time.time()
        self.timeout = timeout

    def recv_message(self, message: mavlink2.MAVLink_message):
        if message.get_type() == "HEARTBEAT":
            self.last_recv_heartbeat = time.time()

    def tick(self):
        now = time.time()

        if now - self.last_sent_heartbeat > self.heartbeat_interval:
            heartbeat = Command.heartbeat()
            self.commands.put(heartbeat)
            self.last_sent_heartbeat = time.time()

        if self.timeout > 0:
            if now - self.last_recv_heartbeat > self.timeout * self.heartbeat_interval:
                print(
                    f"WARN: Lost connection to drone, last received a heartbeat {now - self.last_recv_heartbeat}s ago"
                )
                self.disconnect()


class StatusEchoService(MavlinkService):
    """
    Status Echo Service
    ===================

    This forwards all STATUS_TEXT messages to the UAV status messages queue for
    use in the UI.
    """
    recv_status: Callable

    def __init__(self, recv_status: Callable):
        self.recv_status = recv_status

    def recv_message(self, message: mavlink2.MAVLink_message):
        if message.get_type() == "STATUSTEXT":
            self.recv_status(message.text)


class DebugService(MavlinkService):
    """
    Debug Service
    =================

    Recieves a debugging message from the uav, unpacks and displays it on the GUI.
    """
    def __init__(self):
        self.flag = True

    def recv_message(self, message: mavlink2.MAVLink_message):
        if message.get_type() == 'DEBUG_FLOAT_ARRAY':
            if message.name == "dbg_box":
                self.get_bounding_box(message)

    def get_bounding_box(self, message):
        data: list = message.data  # format: [x_position, y_position, width, height,..,..,..] len=58 (only first 4 indices valuable)
        if self.flag:
            self.mock_debugging(data)

        """
        TODO: Display value on GUI

        """

    def mock_debugging(self, data):
        check = True
        values = []
        for i in range(58):
            if i % 2 == 0:
                values.append(0.0)
            else:
                values.append(1.0)
        for i in range(58):
            if data[i] != values[i]:
                check = False
        if check:
            print("mock debugging successful")
        else:
            print("mock debugging failed")
