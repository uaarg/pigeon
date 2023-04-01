from pymavlink.dialects.v20 import common as mavlink2
import time
import queue

from .common import MavlinkService
from image import Image

class ImageService(MavlinkService):
    """
    Image Transfer Protocol
    =======================

    We are using a bare-bones variation of the Image
    Transmission Protocol [0].

    The setup right now is as follows:

    1) The drone will send ENCAPSULATED_DATA messages
       containing portions of a JPEG formatted image.
    2) The ground control station (GCS -- that's us!) will
       concatenate these partial images into a list of chunks
    3) The drone will send a DATA_TRANSMISSION_HANDSHAKE
       message to note that the image has been fully sent.
    4) On the DATA_TRANSMISSION_HANDSHAKE, the GCS will build
       an image from the buffer and then clear the buffer for
       the next image.

    [0]: https://mavlink.io/en/services/image_transmission.html
    """
    image_packets: dict
    i: int
    commands: queue.Queue
    im_queue: queue.Queue

    def __init__(self, commands: queue.Queue, im_queue: queue.Queue):
        self.i = 0
        self.image_packets = dict()
        self.commands = commands
        self.im_queue = im_queue

    def recv_message(self, message):
        match message.get_type():
            case 'ENCAPSULATED_DATA':
                print('ENCAPSULATED_DATA')
                self.image_packets[message.seqnr] = message

            case 'DATA_TRANSMISSION_HANDSHAKE':
                print('DATA_TRANSMISSION_HANDSHAKE')
                packet_nos = self.image_packets.keys()
                packet_count = max(packet_nos) if len(packet_nos) > 0 else 0

                if packet_count == 0:
                    return

                if message.packets != packet_count:
                    print("WARN: Failed to receive image. "
                        f"Expected {message.packets} packets but "
                        f"received {packet_count} packets")

                # image transmission is complete, collect chunks into an image
                image = bytes()
                for i in range(packet_count):
                    packet = self.image_packets.get(i)
                    if packet is None: return
                    image += bytes(packet.data)

                file = f"data/images/image{self.i}.jpg"
                with open(file, "bw") as image_file:
                    image_file.write(image)
                print(f"Image saved to {file}")
                time.sleep(0.01)
                try:
                    self.im_queue.put(Image(file, "image.txt"))
                except Exception as err:
                    print(f"ERROR: Failed to parse image\n{err}")

                self.i += 1
                self.image_packets.clear()
