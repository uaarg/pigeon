from dataclasses import dataclass
import queue
import datetime

from pigeon.comms.services.common import MavlinkService


@dataclass
class MavlinkMessage:
    type: str
    data: list
    name: str
    time: datetime.datetime


class MessageCollectorService(MavlinkService):
    """
    Repeats all messages received into a message queue.
    """
    message_queue: queue.Queue

    def __init__(self, message_queue: queue.Queue):
        self.message_queue = message_queue

    def recv_message(self, message):
        if message.get_type() == 'DEBUG_VECT':
            message_details = MavlinkMessage(type=message.get_type(), data= [message.x, message.y, message.z], name = message.name,
                                             time=datetime.datetime.now())
        else:
            message_details = MavlinkMessage(type=message.get_type(), data=None, name=None,
                                             time=datetime.datetime.now())
        self.message_queue.put(message_details)
