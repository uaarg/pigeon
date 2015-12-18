import logging

from ivy.ivy import IvyServer, ivylogger, IvyApplicationDisconnected

import log

logger = logging.getLogger(__name__)

def noop():
    pass

def configure_ivy_logging():
    ivylogger.handlers = [] # Wipping out the existing handlers since we don't want anything going to them (ex. one might be stdout)


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
    command_name_regex = "[^ ]+"
    command_value_regex = "[^ ]+"
    status_name_regex = "[^ ]+"
    status_value_regex = "[^ ]+"
    command_format = "UAV-{command_type} {command_name} {command_value}" # for use with Python's str.format()

    command_response_regex = "^UAV-(ACK|UNKN) (%s) (%s)$" % (command_name_regex, command_value_regex)
    command_summary_regex = "^UAV-CMD ((?:%s %s ?)+)$" % (command_name_regex, command_value_regex)
    uav_status_regex = "^UAV-STATUS ((?:%s %s ?)+)$" % (status_name_regex, status_value_regex)

    uav_name = "uavImaging"

    def __init__(self, bus=None):
        self.bus = bus

        self.uav_connected = False
        self.on_uav_connected_changed_cbs = []
        self.command_ack_cbs = []
        self.uav_status_cbs = []

        configure_ivy_logging()
        self.ivy_server = IvyServer("pigeon", "", self._onConnectionChange)
        self._bindMsg(self._handleCommandResponse, self.command_response_regex)
        self._bindMsg(self._handleCommandSummary, self.command_summary_regex)
        self._bindMsg(self._handleUAVStatus, self.uav_status_regex)

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

    def addUAVStatusCb(self, cb):
        """
        Add a function to be called when the UAV sends a status message.
        Will be called with a dictionary of the fields and values.
        """
        self.uav_status_cbs.append(cb)

    def _bindMsg(self, cb, regex):
        logger.debug("Listening on ivybus for regex: %s" % regex)
        self.ivy_server.bind_msg(cb, regex)

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

    def _callUAVStatusCbs(self, status):
        for cb in self.uav_status_cbs:
            cb(status)

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

    def _handleCommandSummary(self, agent, data):
        commands = self._dataFieldsToDict(data)
        for command_name, command_value in commands.items():
            self._callCommandAckCbs(command_name, command_value)

    def _handleUAVStatus(self, agent, data):
        status = self._dataFieldsToDict(data)
        self._callUAVStatusCbs(status)

    def _dataFieldsToDict(self, data):
        """
        Parses the data portion of the UAV-CMD and UAV-STATUS messages
        and returns a dictionary of name:value pairs.

        Example:
            In: "RUN 2 SHUTTER_SPEED 45"
            Out: {"RUN": 2, "SHUTTER_SPEED": 45}

        Raises ValueError on invalid input data.
        """
        out = {}
        parts = data.split(" ")
        for i in range(0, len(parts), 2):
            try:
                out[parts[i]] = parts[i+1]
            except IndexError:
                raise ValueError("Unable to convert '%s' data to dict." % (data))
        return out

    def _sendCommand(self, command):
        return self.ivy_server.send_msg(self.command_format.format(command_type="DO", command_name=command.name, command_value=command.value)) and self.uav_connected
