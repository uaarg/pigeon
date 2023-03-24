from pymavlink import mavutil
import time

conn = mavutil.mavlink_connection("/dev/cu.usbserial-DN007320")

while True:
    msg = conn.recv_match(blocking=False)
    if msg:
        if msg.get_type() == 'BAD_DATA':
            #print("WARN: Recv bad message: ", msg)
            continue

        print("GOT MESSAGE: of type", msg.get_type())
        print("DATA:", msg.to_dict())

    time.sleep(0.01) # s = 10ms
