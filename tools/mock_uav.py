#!/usr/bin/env

import sys
import time
import queue

from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink2

from pigeon.comms.services.common import HearbeatService, StatusEchoService, Command


def disconnect():
    print("Error! Disconnected from server. Exiting", file=sys.stderr)
    sys.exit(1)

def send_image(conn):
    """Sends a test image to the GUI"""
    with open("tools/test_image.JPG", "rb") as f:
        image_data = f.read()
    
    # Define the MAVLink payload size for ENCAPSULATED_DATA (253 bytes)
    chunk_size = 253
    total_packets = (len(image_data) + chunk_size - 1) // chunk_size

    # Send each chunk in an ENCAPSULATED_DATA message
    for i in range(total_packets):
        chunk = image_data[i * chunk_size: (i+1) * chunk_size]
        msg = mavlink2.MAVLink_encapsulated_data_message(i, chunk)
        conn.write(msg)

    # Send the DATA_TRANSMISSION_HANDSHAKE message
    handshake_msg = mavlink2.MAVLink_data_transmission_handshake_message(
        mavlink2.MAVLINK_DATA_STREAM_IMG_JPEG,  # type of data stream, use JPEG
        #len(image_data),  # total size of the image
        0,  # width (0 for unknown)
        0,  # height (0 for unknown)
        0,  # packets (0 for unknown)
        0,  # payload size per packet (0 for unknown)
        total_packets,  # total packets
        0,  # jpg quality (0 for unknown)
    )
    conn.write(handshake_msg)

def main(device: str):
    # Uses a similar struture to pigeon.comms.uav

    print("Mocking UAV on %s" % device)

    conn = mavutil.mavlink_connection(device,
                                      source_system=1,
                                      source_component=2)
    connected = True

    commands = queue.Queue()
    services = [
        HearbeatService(commands, disconnect),
        StatusEchoService(recv_status=print),
    ]

    commands.put(Command.statustext("Started UAV Mocker (from %s)" % device))

    send_image(conn)

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

        # TODO: we should be using some type of select utlity to avoid burning a CPU core
        time.sleep(0.0001)  # s = 100us
