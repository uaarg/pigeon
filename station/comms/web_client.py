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
        
        if webImg:
            webImgPath = webImg.file_path
            #webDataPath = webImg.data_file_path
            webDataPath = "/../tests/data/images/1.txt"
            cliImg = Image(webImgPath, webDataPath) 
        else:
            raise(Exception("Queue empty"))
