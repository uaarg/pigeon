import logging

from ivy.ivy import IvyServer, ivylogger, IvyApplicationDisconnected

import log

logger = logging.getLogger(__name__)

def noop():
    pass

def configure_ivy_logging():
    ivylogger.handlers = [] # Wipping out the existing handlers since we don't want anything going to them (ex. one might be stdout)
    for handler in log.handlers:
        ivylogger.addHandler(handler)


class Command:
    def __init__(self, name, value):
        int(float(value)) # To ensure it's a number
        value = str(value)
        if " " in name:
            raise(ValueError("Command name '%s' contains spaces" % name))
        if " " in value:
            raise(ValueError("Command value '%s' contains spaces" % value))

        self.name = name
        self.value = str(value)

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value

class UAV:
    """
    Handles interfacing with the UAV by creating an ivybus connection
    and communicating over it.
    """
    command_format = "UAV-{command_type} {command_name} {command_value}" # for use with Python's str.format()
    uav_name = "uavImaging"

    def __init__(self, bus=None):
        self.bus = bus

        self.uav_connected = False
        self.on_uav_connected_changed_cbs = []
        self.command_ack_cbs = []

        configure_ivy_logging()
        self.ivy_server = IvyServer("pigeon", "", self._onConnectionChange)
        command_response_regex = "^%s$" % self.command_format.format(command_type="(ACK|UNKN)", command_name="([^ ]*)", command_value="(.*)")
        self.ivy_server.bind_msg(self._handleCommandResponse, command_response_regex)

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

    def sendCommand(self, *args, **kwargs):
        """
        Send a command to the UAV. Arguments are passed directly to
        the constructor of the Command class. Command won't be sent
        to the UAV if the same command hasn't been acknowledged yet.
        """
        command = Command(*args, **kwargs)

        if not self._sendCommand(command):
            logger.warning("Failed to send command: UAV not connected.")

    def addUAVConnectedChangedCb(self, cb):
        """
        Add a function to be called when the UAV is connected or
        disconnected. Will be called with True or False, indicating
        whether the UAV is connected or not (respectively).

        Will also be called immediately with the current connection
        status.
        """
        self.on_uav_connected_changed_cbs.append(cb)
        cb(self.uav_connected)

    def addCommandAckedCb(self, cb):
        """
        Add a function to be called when the UAV acknowledges a command.
        Will be called with the command name and command value.
        """
        self.command_ack_cbs.append(cb)

    def _callUAVConnectedChangedCbs(self):
        for cb in self.on_uav_connected_changed_cbs:
            cb(self.uav_connected)

    def _onConnectionChange(self, agent, event):
        if agent.agent_name == self.uav_name:
            if event == IvyApplicationDisconnected:
                self.uav_connected = False
            else:
                self.uav_connected = True

            self._callUAVConnectedChangedCbs()

    def _callCommandAckCbs(self, command_name, command_value):
        for cb in self.command_ack_cbs:
            cb(command_name, command_value)

    def _handleCommandResponse(self, agent, response_type, name, value):
        logger.info("Received from UAV: %s" % self.command_format.format(command_type=response_type, command_name=name, command_value=value))
        try:
            command = Command(name, value)
        except ValueError:
            logger.error("Invalid command response from UAV: %s" % self.command_format.format(command_type=response_type, command_name=name, command_value=value))
            return

        logger.info("Received response for %s command" % name)
        if response_type == "ACK":
            self._callCommandAckCbs(name, value)
        elif response_type == "UNKN":
            logger.warning("UAV doesn't recognize %s command." % name)
        else:
            raise(Exception("Unexpected UAV response type: %s" % response_type))

    def _sendCommand(self, command):
        return self.ivy_server.send_msg(self.command_format.format(command_type="DO", command_name=command.name, command_value=command.value)) and self.uav_connected
