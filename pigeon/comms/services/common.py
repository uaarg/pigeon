from typing import Callable

from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink2
import time
import queue
import math

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

        self.gsc_device = "tcpin:127.0.0.1:14551"
        self.uav_device = "tcpout:127.0.0.1:14550"
        self.gsc_conn = mavutil.mavlink_connection(self.gsc_device, source_system=1, source_component=3)
        self.uav_conn = mavutil.mavlink_connection(self.uav_device, source_system=1, source_component=2)
        print("Server has started")

    def recv_message(self, message: mavlink2.MAVLink_message):
        """forward message to mission planner (mock gsc)"""

        data_bytes = message.pack(self.gsc_conn.mav)

        data_bytes = bytearray(data_bytes)

        ENCAPSULATED_DATA_LEN = 253

        handshake_msg = mavutil.mavlink.MAVLink_data_transmission_handshake_message(
            type=0,
            size=len(data_bytes),
            width=0,
            height=0,
            packets=math.ceil(len(data_bytes) / ENCAPSULATED_DATA_LEN),
            payload=ENCAPSULATED_DATA_LEN,
            jpg_quality=0,
        )
        self.gsc_conn.mav.send(handshake_msg)

        for seqnr, start in enumerate(range(0, len(data_bytes), ENCAPSULATED_DATA_LEN)):
            data_seg = data_bytes[start:start + ENCAPSULATED_DATA_LEN]
            if len(data_seg) < ENCAPSULATED_DATA_LEN:
                data_seg += bytearray(ENCAPSULATED_DATA_LEN - len(data_seg))
            encapsulated_data_msg = mavutil.mavlink.MAVLink_encapsulated_data_message(
                seqnr, list(data_seg))
            self.gsc_conn.mav.send(encapsulated_data_msg)
        
        handshake_msg = mavutil.mavlink.MAVLink_data_transmission_handshake_message(
            type=0,
            size=len(data_bytes),
            width=0,
            height=0,
            packets=math.ceil(len(data_bytes) / ENCAPSULATED_DATA_LEN),
            payload=ENCAPSULATED_DATA_LEN,
            jpg_quality=0,
        )
        self.gsc_conn.mav.send(handshake_msg)

    
    def tick(self):
        """
        Checks if server from mission planner (mock gsc) has sent a message.
        If so, forward it to the drone.
        """
        message = self.gsc_conn.recv_match(blocking=False)
        if message:
            data_bytes = message.pack(self.uav_conn.mav)

            data_bytes = bytearray(data_bytes)

            ENCAPSULATED_DATA_LEN = 253

            handshake_msg = mavutil.mavlink.MAVLink_data_transmission_handshake_message(
                type=0,
                size=len(data_bytes),
                width=0,
                height=0,
                packets=math.ceil(len(data_bytes) / ENCAPSULATED_DATA_LEN),
                payload=ENCAPSULATED_DATA_LEN,
                jpg_quality=0,
            )
            self.uav_conn.mav.send(handshake_msg)

            for seqnr, start in enumerate(range(0, len(data_bytes), ENCAPSULATED_DATA_LEN)):
                data_seg = data_bytes[start:start + ENCAPSULATED_DATA_LEN]
                if len(data_seg) < ENCAPSULATED_DATA_LEN:
                    data_seg += bytearray(ENCAPSULATED_DATA_LEN - len(data_seg))
                encapsulated_data_msg = mavutil.mavlink.MAVLink_encapsulated_data_message(
                    seqnr, list(data_seg))
                self.uav_conn.mav.send(encapsulated_data_msg)
            
            handshake_msg = mavutil.mavlink.MAVLink_data_transmission_handshake_message(
                type=0,
                size=len(data_bytes),
                width=0,
                height=0,
                packets=math.ceil(len(data_bytes) / ENCAPSULATED_DATA_LEN),
                payload=ENCAPSULATED_DATA_LEN,
                jpg_quality=0,
            )
            self.uav_conn.mav.send(handshake_msg) 



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
