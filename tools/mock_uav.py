#!/usr/bin/env

import sys
import time
import queue
from PIL import Image
from math import ceil

from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink2
import pymavlink.dialects.v20.all as dialect
from pigeon.comms.services.common import HearbeatService, StatusEchoService, Command, DebugService


def disconnect():
    print("Error! Disconnected from server. Exiting", file=sys.stderr)
    sys.exit(1)


def send_image(conn):
    """Sends a test image to the GUI"""

    image_path = "data/images/test_image.JPG"

    # Compress image
    im = Image.open(image_path)
    im = im.resize((200, 150), Image.Resampling.LANCZOS)
    im.save(f"{image_path}_cmp.jpg", quality=75)

    # Open image
    with open(f"{image_path}_cmp.jpg", "rb") as f:
        image_data = bytearray(f.read())

    message = mavlink2.MAVLink_camera_image_captured_message(
        time_boot_ms=int(time.time()),
        time_utc=0,
        camera_id=0,
        lat=0,
        lon=0,
        alt=0,
        relative_alt=0,
        q=(1, 0, 0, 0),
        image_index=-1,
        capture_result=1,
        file_url="".encode())
    conn.write(message.pack(conn.mav))

    ENCAPSULATED_DATA_LEN = 253

    handshake_msg = mavlink2.MAVLink_data_transmission_handshake_message(
        0,
        len(image_data),
        0,
        0,
        ceil(len(image_data) / ENCAPSULATED_DATA_LEN),
        ENCAPSULATED_DATA_LEN,
        0,
    )
    conn.write(handshake_msg.pack(conn.mav))

    data = []
    for start in range(0, len(image_data), ENCAPSULATED_DATA_LEN):
        data_seg = image_data[start:start + ENCAPSULATED_DATA_LEN]
        data.append(data_seg)

    for msg_index, data_seg in enumerate(data):
        if len(data_seg) < ENCAPSULATED_DATA_LEN:
            data_seg.extend(bytearray(ENCAPSULATED_DATA_LEN - len(data_seg)))
        encapsulated_data_msg = mavlink2.MAVLink_encapsulated_data_message(
            msg_index + 1, data_seg)
        conn.write(encapsulated_data_msg.pack(conn.mav))

    handshake_msg = mavlink2.MAVLink_data_transmission_handshake_message(
        0,
        len(image_data),
        0,
        0,
        ceil(len(image_data) / ENCAPSULATED_DATA_LEN),
        ENCAPSULATED_DATA_LEN,
        0,
    )
    conn.write(handshake_msg.pack(conn.mav))


def mock_debug(conn):
    """Sends a debugging message to the GUI"""
    values = []
    for i in range(58):
        if i % 2 == 0:
            values.append(0.0)
        else:
            values.append(1.0)
    message = dialect.MAVLink_debug_float_array_message(name=bytes("dbg_box", 'utf-8'),
                                                        time_usec=int(time.time()),
                                                        array_id=0,
                                                        data=values)
    conn.mav.send(message)


def main(device: str, timeout: int):
    # Uses a similar struture to pigeon.comms.uav

    start_time = time.time()

    print("Mocking UAV on %s" % device)
    if timeout > 0:
        print("Mock UAV will timeout in %d seconds" % timeout)
    else:
        print("Mock UAV will run forever")

    conn = mavutil.mavlink_connection(device,
                                      source_system=1,
                                      source_component=2)
    connected = True

    commands = queue.Queue()
    services = [
        HearbeatService(commands, disconnect, timeout),
        StatusEchoService(recv_status=print),
        DebugService()
    ]

    commands.put(Command.statustext("Started UAV Mocker (from %s)" % device))

    image_count = 0
    flag = True
    while connected:
        for service in services:
            service.tick()

        msg = conn.recv_match(blocking=False)
        if msg:
            for service in services:
                service.recv_message(msg)

        try:
            command = commands.get(block=False)
            conn.write(command.encode(conn))
        except queue.Empty:
            pass

        current_time = time.time()
        if ((current_time - start_time) > 10) and image_count < 1:
            print("sending an image")
            send_image(conn)
            image_count += 1

        if ((current_time - start_time) > 12) and flag:
            print("testing debugging service")
            mock_debug(conn)
            flag = False

        # TODO: we should be using some type of select utlity to avoid burning a CPU core
        time.sleep(0.0001)  # s = 100us
