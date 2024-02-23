class MissionPlannerServer:
    """
    A server that forwards messages from the drone to pigeon to mission planner.
    [UAV] <--> [Pigeon] <--> [Mission Planner]
    """

    def __init__(self) -> None:
        self.udp_port = None

    def set_port(self, port: int) -> None:
        """
        Set the port that the server will listen on.
        """
        self.udp_port = port


