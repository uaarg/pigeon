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
    10/`heartbeat_freq`. If it takes longer, then we consider the drone to have
    disconnected.
    """
    last_sent_heartbeat: float
    last_recv_heartbeat: float
    heartbeat_interval: float
    disconnect: Callable
    commands: queue.Queue

    def __init__(self, commands: queue.Queue, disconnect: Callable, heartbeat_freq: float = 1):
        self.commands = commands
        self.disconnect = disconnect
        self.heartbeat_interval = 1 / heartbeat_freq
        self.last_sent_heartbeat = time.time()
        self.last_recv_heartbeat = time.time()

    def recv_message(self, message: mavlink2.MAVLink_message):
        if message.get_type() == "HEARBEAT":
            self.last_recv_heartbeat = time.time()

    def tick(self):
        now = time.time()

        if now - self.last_sent_heartbeat < self.heartbeat_interval:
            last_heartbeat = now
            heartbeat = Command.heartbeat()
            self.commands.put(heartbeat)

        if self.last_recv_heartbeat > 10 * self.heartbeat_interval:
            print(f"WARN: Lost connection to drone, last received a heartbeat {self.last_recv_heartbeat}s ago")
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
