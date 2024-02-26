from typing import Callable

from pymavlink import mavutil
from pymavlink.dialects.v20 import all as mavlink2
from pigeon.settings import settings_data
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


class ForwardingService(MavlinkService):
    """
    Forwarding Service
    ==================

    This service forwards all MAVlink messages between Mission Planner and Pigeon.
    """
    commands: queue.Queue

    def __init__(self, commands: queue.Queue):
        self.commands = commands

        self.gcs_device = settings_data["GCS Device"]

        self.gcs_conn = mavutil.mavlink_connection(self.gcs_device,
                                                   source_system=1,
                                                   source_component=1)

    def recv_message(self, message: mavlink2.MAVLink_message):
        """
        Forward message to mission planner (mock gcs)
        """
        try:
            data_bytes = message.pack(self.gcs_conn.mav)
            data_bytes = bytearray(data_bytes)
            self.gcs_conn.write(data_bytes)
        except NotImplementedError:
            # Sometimes message is a BAD_DATA type. In that case, message.pack
            # will fail. We should just ignore BAD_DATA, it's a fact of radio
            # noise/interference
            pass

    def tick(self):
        """
        Checks if server from mission planner (mock gcs) has sent a message.
        If so, forward it to the drone.
        """
        while message := self.gcs_conn.recv_match(blocking=False):
            self.commands.put(Command(message))


class HeartbeatService(MavlinkService):
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
