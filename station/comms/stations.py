import logging
from ivy.ivy import IvyServer, ivylogger, IvyApplicationDisconnected
from threading import Thread
import queue
import time

from features import BaseFeature, FeatureDeserializeSecurityError

from .common import CommonIvyComms

logger = logging.getLogger(__name__)

def noop():
    pass

def configure_ivy_logging():
    ivylogger.handlers = [] # Wipping out the existing handlers since we don't want anything going to them (ex. one might be stdout)


class IOQueue():
    def __init__(self):
        self.in_queue = queue.Queue()
        self.out_queue = queue.Queue()

class Stations(CommonIvyComms):
    """
    Handles interfacing and syncing with other station instances by creating
    an ivybus connection and communicating over it. Provides multi-operator
    capabilities. Syncs features and images.

    Images to send are taken from the image_queue argument. Images received
    are saved directly to the folder being monitored.

    self.feature_io_queue is a an IOQueue for inbound and outbound features.
    Features to send should be put in self.feature_io_queue.out_queue().
    Features received are put in self.feature_io_queue.in_queue().
    """
    feature_sync_regex = "^feature-change (.*)"
    image_file_sync_regex = "^image-file (.*)"

    def __init__(self, *args, **kwargs):
        self.settings_data = kwargs.pop("settings_data")
        super().__init__(*args, **kwargs)

        self.image_io_queue = IOQueue()
        self.feature_io_queue = IOQueue()
        self._bindMsg(self._handleFeatureSync, self.feature_sync_regex)
        self._bindMsg(self._handleImageFileSync, self.image_file_sync_regex)

    def start(self):
        super().start()
        self.feature_queue_thread = Thread(target=self._sendFeatureQueue, daemon=True)
        self.feature_queue_thread.start()

        self.image_queue_thread = Thread(target=self._sendImageQueue, daemon=True)
        self.image_queue_thread.start()

    def stop(self):
        self.feature_io_queue.out_queue.put(None) # Signal for thread to terminate
        self.image_io_queue.out_queue.put(None) # Signal for thread to terminate

        self.feature_queue_thread.join()
        self.image_queue_thread.join()
        super().stop()

    def _sendFeatureQueue(self):
        self.waitOnIvyInit()
        while True:
            feature = self.feature_io_queue.out_queue.get()
            if not feature: # Signal to stop this thread
                return
            else:
                peer_count = self.ivy_server.send_msg("feature-change %s" % feature.serialize())
                logger.info("Sent a feature to %s." % (self._peerCountText(peer_count)))


    def _sendImageQueue(self):
        self.waitOnIvyInit()
        while True:
            url = self.image_io_queue.out_queue.get()
            if not url: # Signal to stop this thread
                return
            else:
                peer_count = self.ivy_server.send_msg("image-file %s" % url)
                logger.info("Sent an image file to %s." % self._peerCountText(peer_count))

    def _bindMsg(self, cb, regex):
        logger.debug("Listening on ivybus for regex: %s" % regex)
        self.ivy_server.bind_msg(cb, regex)

    def _onConnectionChange(self, agent, event):
        if agent.agent_name.find("pigeon") == 0:
            if event == IvyApplicationDisconnected:
                pass
            else:
                pass

    def _handleFeatureSync(self, agent, data):
        logger.info("Received a feature from %s." % agent)
        try:
            feature = BaseFeature.deserialize(data)
        except FeatureDeserializeSecurityError as e:
            logger.error("Failed to deserialize feature from %s for potential security reasons: %s Raw data:\n '%s'" % (agent, e, data))
        else:
            self.feature_io_queue.in_queue.put(feature)

    def _handleImageFileSync(self, agent, url):
        logger.info("Received an image url from %s: %s" % (agent, url))
        self.image_io_queue.in_queue.put(url % agent.ip)

    def _peerCountText(self, peer_count):
        return "%s peer%s" % (peer_count, "" if peer_count == 1 else "s")

    def waitOnIvyInit(self):
        time.sleep(3) # Give the ivybus some time to establish connections before we start sending stuff over the bus
                      # Hardocded delays like this suck byt ivy doesn't seem to have a way to tell us when it's ready.
                      # And really: how could it. It doesn't know if it's going to find any peers. This gives three
                      # seconds for them to connect to get our initial load of images.