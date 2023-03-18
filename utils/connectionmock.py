"""
A simple dev server over mavlink for testing the UAVMavLink class.

Can be run normally with `python ./utils/connectionmock.py`. Then the dev
server will be started on tcp:localhost:1234 and all output will be printed to
stdout.

This can be run in conjunction with the pigeon GUI to view all data being sent
as part of the mavlink protocol.
"""

from pymavlink import mavutil
import time

# must follow: tcp:<host>:<port>
DEVICE = 'tcpin:localhost:1234'
conn: mavutil.mavfile = mavutil.mavlink_connection(DEVICE)

i = 0
while True:
    msg = conn.recv_match()

    if msg:
        print(msg)

        if msg.get_type() == 'HEARTBEAT':
            print("\n\n*****Got message: %s*****" % msg.get_type())
            print("Message: %s" % msg)
            print("\nAs dictionary: %s" % msg.to_dict())
            # Armed = MAV_STATE_STANDBY (4), Disarmed = MAV_STATE_ACTIVE (3)
            print("\nSystem status: %s" % msg.system_status)

            conn.mav.heartbeat_send(
                type=mavutil.mavlink.MAV_TYPE_GENERIC,
                autopilot=mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                base_mode=0,
                custom_mode=0,
                system_status=0)

    i += 1
    time.sleep(0.01)

    if i % 1000:
        conn.mav.heartbeat_send(
            type=mavutil.mavlink.MAV_TYPE_GENERIC,
            autopilot=mavutil.mavlink.MAV_AUTOPILOT_INVALID,
            base_mode=0,
            custom_mode=0,
            system_status=0)

