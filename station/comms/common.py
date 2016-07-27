import uuid
from ivy.ivy import IvyServer, ivylogger


def configure_ivy_logging():
    ivylogger.handlers = [] # Wipping out the existing handlers since we don't want anything going to them (ex. one might be stdout)

class CommonIvyComms:
    def __init__(self, bus=None, instance_name=None):
        self.bus = bus
        self.instance_name = instance_name or "unnamed %s" % str(uuid.uuid4())[:4]

        configure_ivy_logging()

        instance_name = "pigeon-%s" % self.instance_name
        instance_name.replace(" ", "_") # Ivy seems to do weird things when there's a space. Ex. receiving it's own messages.
        self.ivy_server = IvyServer(instance_name, "", self._onConnectionChange)

    def _onConnectionChange(self, *args, **kwargs):
        pass

    def setBus(self, bus):
        old_bus = self.bus
        self.bus = bus
        # Need to restart the server if the bus has changed and the server is already running:
        if self.bus != old_bus and self.ivy_server._thread:
            self.stop()
            self.start()

    def start(self):
        """
        Starts listening for ivy bus messages and enables sending of
        messages.
        """
        self.ivy_server.start(self.bus)

    def stop(self):
        """
        Stops the ivy bus server.
        """
        self.ivy_server.stop()