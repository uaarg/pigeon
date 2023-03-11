import logging
import queue

from pymavlink import mavutil
class UAV:
    """
    This class is designed to handle all Mavlink Communication to and from the UAV
    
    The class will listen in to a reciever (typically connected via USB)

    All data is forwarded to our autopilot ground station (typically QGroundControl)
    """
    def __init__(self, uav_port) -> None:
        self.outgoing_queue = queue.Queue()
        self.incoming_queue = queue.Queue()
    def sendCustomCommand(self, msg):
        """
        This method sends a command to the UAV
        """
        self.outgoing_queue.put(msg)

    async def _mavlinkLoop(self, uav_port):
        """
        This method is ran async to process incoming and outgoing 
        data from the UAV
        """
        conn = mavutil.mavlink_connection(uav_port)

        while True:
            # Block waiting for incoming message
            msg = conn.recv_match(type='CUSTOM', timeout=1)
            if msg and msg.get_type() != 'BAD_TYPE':
                print(msg)
            
            msg = self.outgoing_queue.get()
            # Transmit outgoing messages
            if msg:
                conn.send_message(msg)
            



