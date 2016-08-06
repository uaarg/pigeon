import queue
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
    # HTTP server built into Python. A bit lower level than we want but frameworks like Flask
    # don't seem to provide reliable ways of stopping the server programatically.
import json
import os.path
import logging
import requests
import os.path

logger = logging.getLogger(__name__)

class ImageReplicatorHTTPHandler(BaseHTTPRequestHandler):
    """
    Main code for the HTTP server that makes image and info
    files available for other Pigeon's to download.

    Handles GETs to two urls:
    * /        : returns a json array of the files available.
    * /1.jpg   : where "1.jpg" should be replaced with the actual
                 name of the file.

    Returns HTTP 404 and 500 responses with HTML as appropriate.
    """
    def write_headers(self, status, headers):
        self.send_response(status)
        for header in headers:
            self.send_header(*header)
        self.end_headers()

    def send_json(self, status, data):
        self.write_headers(status, [("Content-type", "application/json")])
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def send_html(self, status, data):
        self.write_headers(status, [('Content-type', 'text/html')])
        self.wfile.write(data.encode("utf-8"))

    def send_file(self, status, file_path):
        head, tail = os.path.split(file_path)
        filename, extension = os.path.splitext(tail)

        self.write_headers(200, [("Content-type", "application/%s" % extension)])
        with open(file_path, "rb") as f:
            while True:
                buf = f.read(1024)
                if buf:
                    self.wfile.write(buf)
                else:
                    break

    def do_GET(self):
        try:
            path = self.path.strip("/") # Allowing trailing slashes or not
            if path == "":
                self.send_json(200, list(self.files.keys()))
            elif path == "easter-egg":
                self.send_html(200, "<img src='https://cdn2.iconfinder.com/data/icons/vector-easter-eggs/220/easter_egg_yellow_red_blue-512.png'</img>")
            else:
                file_path = self.files.get(path)
                if file_path:
                    logger.info("%s downloading image file: %s" % (self.client_address[0], path))
                    self.send_file(200, file_path)
                else:
                    logger.info("HTTP 404: %s" % self.path)
                    self.send_html(404, "Not found")
        except Exception as e:
            logger.error("Error while processing request in HTTP Server: %s: %s" % (e.__class__.__name__, e))
            self.send_html(500, "Unhandled Exception: %s: %s" % (e.__class__.__name__, e))

    def log_message(self, format, *args):
        pass # Disabling logging of each request.

class ImageReplicator:
    """
    Replicates images this Pigeon instance found to other Pigeons.

    Listens for images added to the image_in_queue. Adds them to
    self.image_out_queue so that something else can use them too.
    For each image that passes through, makes the image and info
    files available over HTTP (forever: clients can request anytime).
    Puts a string with the URL into self.image_replicate_out_queue.
    This is what can be sent to other Pigeon instances. The URL
    includes port but has "%s" in place of the host/ip address:
    the client should populate that based on how it knows to talk
    to this Pigeon instance.
    """
    def __init__(self, image_in_queue, replicate_io_queue, settings_data={}):
        self.image_in_queue = image_in_queue
        self.image_out_queue = queue.Queue()
        self.replicate_io_queue = replicate_io_queue

        self.settings_data = settings_data

        self.files = {}
        self.url_number = 0
        self.url = "http://%s:%s/%s"

        # Setting up the HTTP server:
        def make_request_handler(**kwargs): # Closure to let these arguments be locally accessed by the Handler class
            cls = ImageReplicatorHTTPHandler
            for key, value in kwargs.items():
                setattr(cls, key, value)
            return cls

        for port in range(8000, 8100): # Looking for a free port in this range
            try:
                self.server = HTTPServer(("", port), make_request_handler(files=self.files, url=self.url))
            except OSError as e:
                if e.errno == 98: # Address already in use
                    continue
                else:
                    raise
            else:
                self.port = port
                break
        else:
            raise(Exception("Unable to find free port."))

    def start(self):
        logger.info("Starting queue replicator.")
        self.image_in_queue_thread = Thread(target=self._handleImageInQueue, daemon=True)
        self.image_in_queue_thread.start()
        self.replicate_queue_thread = Thread(target=self._handleReplicateQueue, daemon=True)
        self.replicate_queue_thread.start()

        logger.info("Starting HTTP Server on port %s." % self.port)
        self.server_thread = Thread(target=self.runServer, daemon=True)
        self.server_thread.start()

    def stop(self):
        logger.info("Stopping queue replicator.")
        self.image_in_queue.put(None) # Signal for thread to terminate
        self.image_in_queue_thread.join()

        self.replicate_io_queue.in_queue.put(None) # Signal for thread to terminate
        self.replicate_queue_thread.join()

        logger.info("Stopping HTTP Server.")
        self.server.socket.close() # Not using self.server.shutdown() because it seems to
                                   # wait until all clients are disconnected and browsers
                                   # (ex. Chrome) seems to stay connected. This forces
                                   # shutdown now.

    def runServer(self):
        try:
            self.server.serve_forever()
        except ValueError as e:
            logger.info("Server stoped with %s: %s" % (e.__class__.__name__, e))

    def _makeUrl(self, filename):
        return self.url % ("%s", self.port, filename)

    def _handleImageInQueue(self):
        while True:
            image = self.image_in_queue.get()
            if not image:
                return
            else:
                self.image_out_queue.put(image)

                self.files[image.filename] = image.path
                self.replicate_io_queue.out_queue.put(self._makeUrl(image.filename))

                self.files[image.info_filename] = image.info_path
                self.replicate_io_queue.out_queue.put(self._makeUrl(image.info_filename))

    def _handleReplicateQueue(self):
        while True:
            url = self.replicate_io_queue.in_queue.get()
            if not url:
                return
            else:
                head, filename = os.path.split(url)
                self._downloadFile(url, os.path.join(self.settings_data["Monitor Folder"], filename))

    def _downloadFile(self, url, path):
        if not os.path.isfile(path): # Don't need to download files we already have
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.error("Failed to download file from '%s': %s" % (url, e))
                return # Silently ignoring

            with open(path, "wb") as f:
                for block in response.iter_content(1024):
                    f.write(block)

            logger.info("Successfully downloaded file from '%s' to '%s'." % (url, path))