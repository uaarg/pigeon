import logging
from ivy.ivy import IvyServer, ivylogger, IvyApplicationDisconnected
from threading import Thread
import queue

from features import BaseFeature

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
    capabilities.
    """
    feature_sync_regex = "^feature-change (.*)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.thread = None
        self.feature_io_queue = IOQueue()
        self._bindMsg(self._handleFeatureSync, self.feature_sync_regex)

    def start(self):
        super().start()
        self.thread = Thread(target=self._sendQueue, daemon=True)
        self.thread.start()

    def stop(self):
        self.feature_io_queue.out_queue.put(None) # Signal for thread to terminate
        self.thread.join()
        super().stop()

    def _sendQueue(self):
        while True:
            feature = self.feature_io_queue.out_queue.get()
            if not feature:
                return
            else:
                peer_count = self.ivy_server.send_msg("feature-change %s" % feature.serialize())
                logger.info("Sent a feature to %s peer%s." % (peer_count, "" if peer_count == 1 else "s"))

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
        feature = BaseFeature.deserialize(data)
        self.feature_io_queue.in_queue.put(feature)

