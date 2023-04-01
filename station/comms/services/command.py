from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink2

class Command:
    """
    Preferred application command interface. Use this to construct commands
    which are to be send over MavLink.

    This interface exists due to the redundant and difficult nature of the
    mavlink api bindings. They are difficult to use as they are often generated
    at runtime. This means that most development tools are unable to
    autocomplete these commands. Furthermore, many commands are missing
    defaults which make their construction painful. Finally, we often abuse
    some commands by adding semantics onto them beyond their original use.

    This command class solves all those issues by offering an improved
    interface for constructing MavLink commands.
    """
    def __init__(self, message: mavlink2.MAVLink_message):
        self.message = message

    @staticmethod
    def heartbeat() -> 'Command':
        msg = mavlink2.MAVLink_heartbeat_message(
                type=mavlink2.MAV_TYPE_GCS,
                autopilot=mavlink2.MAV_AUTOPILOT_INVALID,
                base_mode=0,
                custom_mode=0,
                system_status=0,
                mavlink_version=2)
        return Command(msg)

    @staticmethod
    def ack(message: mavlink2.MAVLink_message, result = mavlink2.MAV_RESULT_ACCEPTED) -> 'Command':
        print("ack")
        msg = mavlink2.MAVLink_command_ack_message(
                command=message.get_msgId(),
                result=result)
        return Command(msg)

    def encode(self, conn: mavutil.mavfile) -> bytes:
        return self.message.pack(conn.mav)
