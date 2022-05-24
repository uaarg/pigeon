from uaarg_client import ImageClient
from queue import Queue
from image import Image

# Pigeon client creates instance of imageclient and connects to server.
# Pops queue when image is being requested and gets image class returned.
#


class WebClient:

    def __init__(self, mainQueue:Queue):
        self.imgClient = ImageClient()
        self.mainQueue = mainQueue

    def add_queue(self):
        webImg = self.imgClient.pop_queue()
        print(f"{webImg.image_id}, {webImg.file_path}")
        if webImg:
            webImgPath = webImg.file_path
            print(webImgPath)
            webDataPath = webImg.info_file_path
            print(webImgPath)
            # webImgPath = "tests/data/images/1.jpg"
            # webDataPath = "tests/data/images/1.txt"
            cliImg = Image(webImgPath, webDataPath)
            self.mainQueue.put(cliImg)
        else:
            raise Exception("Queue empty")
