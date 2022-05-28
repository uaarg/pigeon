from uaarg_client import ImageClient, Image as WebClientImage
from queue import Queue
from image import Image as PigeonImage

# Pigeon client creates instance of imageclient and connects to server.
# Pops queue when image is being requested and gets image class returned.
#

class WebImage(PigeonImage):
    """An adapter for images retrieved from the pigeon server."""

    def __new__(cls, image: WebClientImage):
        """This is used by image class to de-duplicate images."""
        return super().__new__(cls, image.file_path, image.info_file_path)

    
    def __init__(self, image: WebClientImage):
        super().__init__(image.file_path, image.info_file_path)
        self.web_image = image

        self.web_image_id = image.image_id

class WebClient:
    def __init__(self, mainQueue: Queue):
        self.imgClient = ImageClient(server_url="http://127.0.0.1:5000")
        self.mainQueue = mainQueue


    def close(self):
        self.imgClient.close()

    def add_queue(self):
        webImg = self.imgClient.pop_queue()
        if webImg:
            self.mainQueue.put(WebImage(webImg))
        else:
            raise Exception("Queue empty")
