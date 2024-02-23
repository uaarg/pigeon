from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink2



# NEED to edit so that mock_gsc can send and receive messages


def disconnect():
    print("Error! Disconnected from server. Exiting", file=sys.stderr)
    sys.exit(1)

def main(device: str, timeout: int):
    print("Mocking GSC on %s" % device)
    if timeout > 0:
        print("Mock GSC will timeout in %d seconds" % timeout)
    else:
        print("Mock GSC will run forever")
    
    conn = mavutil.mavlink_connection(device,
                                      source_system=255,
                                      source_component=255)
    connected = True
    
    while connected:
        msg = conn.recv_match(blocking=False)