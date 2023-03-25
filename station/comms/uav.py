from dataclasses import field, dataclass
from typing import Any, Callable

from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink2
from threading import Lock, Thread
import time
import logging
import queue

from image import Image

logger = logging.getLogger(__name__)

class Command:
    """
    Preferred application command interface. Use this to construct commands
    which are to be send over MavLink.

    This interface exists due to the redundant and difficult nature of the
    mavlink api bindings. They are difficult to use as they are often generated
    at runtime. This means that most development tools are unable to
    autocomplete these commands. Furthermore, many commands are missing
    defaults which make their construction painful. Finally, we often abuse
    some commands by adding semantics onto them beyond their original use.

    This command class solves all those issues by offering an improved
    interface for constructing MavLink commands.
    """
    def __init__(self, message: mavlink2.MAVLink_message):
        self.message = message

    @staticmethod
    def heartbeat() -> 'Command':
        msg = mavlink2.MAVLink_heartbeat_message(
                type=mavlink2.MAV_TYPE_GCS,
                autopilot=mavlink2.MAV_AUTOPILOT_INVALID,
                base_mode=0,
                custom_mode=0,
                system_status=0,
                mavlink_version=2)
        return Command(msg)

    def encode(self, conn: mavutil.mavfile) -> bytes:
        return self.message.pack(conn.mav)

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

        image_packets = dict()
        last_heartbeat = time.time()
        heartbeat_interval = 5 # 1 / (5 s) = 0.2 Hz
        i = 0

        while self.connected:
            msg = self.conn.recv_match(blocking=False)
            if msg:
                match msg.get_type():
                    # TODO: log bad data to a debug console
                    case 'BAD_DATA': continue

                    # Re-emit status text messages to status listeners
                    case 'STATUSTEXT':
                        self._recvStatus(msg.text)
                        continue

                    # Image Transfer Protocol
                    # =======================
                    #
                    # We are using a bare-bones variation of the Image
                    # Transmission Protocol [0].
                    #
                    # The setup right now is as follows:
                    #
                    # 1) The drone will send ENCAPSULATED_DATA messages
                    #    containing portions of a JPEG formatted image.
                    # 2) The ground control station (GCS -- that's us!) will
                    #    concatenate these partial images into a list of chunks
                    # 3) The drone will send a DATA_TRANSMISSION_HANDSHAKE
                    #    message to note that the image has been fully sent.
                    # 4) On the DATA_TRANSMISSION_HANDSHAKE, the GCS will build
                    #    an image from the buffer and then clear the buffer for
                    #    the next image.
                    #
                    # [0]: https://mavlink.io/en/services/image_transmission.html
                    case 'ENCAPSULATED_DATA':
                        print('ENCAPSULATED_DATA')
                        image_packets[msg.seqnr] = msg
                        continue
                    case 'DATA_TRANSMISSION_HANDSHAKE':
                        print('DATA_TRANSMISSION_HANDSHAKE')
                        packet_nos = image_packets.keys()
                        packet_count = max(packet_nos) if len(packet_nos) > 0 else 0

                        if packet_count == 0:
                            continue

                        if msg.packets != packet_count:
                            print("WARN: Failed to receive image. "
                                f"Expected {msg.packets} packets but "
                                f"received {packet_count} packets")

                        # image transmission is complete, collect chunks into an image
                        image = bytes()
                        for i in range(packet_count):
                            packet = image_packets.get(i)
                            if packet is None: continue
                            image += bytes(packet.data)

                        file = f"data/images/image{i}.jpg"
                        with open(file, "bw") as image_file:
                            image_file.write(image)
                        print(f"Image saved to {file}")
                        time.sleep(0.01)
                        try:
                            self.im_queue.put(Image(file, "image.txt"))
                        except Exception as err:
                            print(f"ERROR: Failed to parse image\n{err}")

                        i += 1
                        image_packets.clear()
                        continue

            # Heartbeat Service
            #
            # We send a heartbeat at the interval given by
            # `heartbeat_interval`. We also make sure that we have received a
            # heartbeat within at least 5*`heartbeat_interval`. If it takes
            # longer, then we consider the drone to have disconnected.
            now = time.time()
            if now - last_heartbeat < heartbeat_interval:
                last_heartbeat = now
                heartbeat = Command.heartbeat()
                self.conn.write(heartbeat.encode(self.conn))
            last_recv_heartbeat = self.conn.time_since('HEARTBEAT')
            if last_recv_heartbeat > 15 * heartbeat_interval:
                print(f"WARN: Lost connection to drone, last received a heartbeat {last_recv_heartbeat}s ago")
                self.disconnect()

            try:
                command = self.commands.get(block=False)
                self.conn.write(command.encode(self.conn))
                print(command)
            except queue.Empty:
                pass

            time.sleep(0.0001) # s = 100us
