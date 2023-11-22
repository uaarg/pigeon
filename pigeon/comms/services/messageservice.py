import queue
from dataclasses import dataclass

from pigeon.comms.services.common import MavlinkService


@dataclass
class MavlinkMessage:
    type: str
    # more params go here ...


class MessageCollectorService(MavlinkService):
    """
    Repeats all messages received into a message queue.
    """
    message_queue: queue.Queue

    def __init__(self, message_queue: queue.Queue):
        self.message_queue = message_queue

    def recv_message(self, message):
        message_details = MavlinkMessage(type=message.get_type())
        self.message_queue.put(message_details)
