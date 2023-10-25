#!/usr/bin/env

import sys
import time
import queue

from pymavlink import mavutil

from pigeon.comms.services.common import HearbeatService, StatusEchoService, Command


def disconnect():
    print("Error! Disconnected from server. Exiting", file=sys.stderr)
    sys.exit(1)


def main(device: str, timeout: int):
    # Uses a similar struture to pigeon.comms.uav

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
    ]

    commands.put(Command.statustext("Started UAV Mocker (from %s)" % device))

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
