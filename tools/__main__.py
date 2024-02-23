import argparse
import sys

sys.path.append("..")  # Allow importing pigeon from tools/ modules

from tools.mock_uav import main as mock_uav_main
from tools.mock_ground_station import main as mock_ground_station_main

root = argparse.ArgumentParser()
tools = root.add_subparsers(help="Tools")

mock_uav = tools.add_parser("mock-uav", help="Utility to mock the UAV locally")
mock_uav.add_argument("--device", type=str, default="tcpin:127.0.0.1:14550")
mock_uav.add_argument("-timeout", "--timeout_value", type=int, default=-1)
mock_uav.set_defaults(_command="mock-uav")

mock_gsc = tools.add_parser("mock-gsc", help="Utility to mock the ground station locally")
mock_gsc.add_argument("--device", type=str, default="tcp:127.0.0.1:14551")
mock_gsc.add_argument("-timeout", "--timeout_value", type=int, default=-1)
mock_gsc.set_defaults(_command="mock-gsc")

args = root.parse_args()

if '_command' not in args:
    # Usage error
    root.print_usage()
    sys.exit(2)

match args._command:
    case "mock-uav":
        mock_uav_main(args.device, args.timeout_value)
    case "mock-gsc":
        mock_ground_station_main(args.device, args.timeout_value)
    case _:  # Unknown _command
        raise NotImplementedError("Unknown command: %r" % args._command)
