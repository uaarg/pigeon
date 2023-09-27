import argparse
import sys

sys.path.append("..")  # Allow importing pigeon from tools/ modules

from tools.mock_uav import main as mock_uav_main

root = argparse.ArgumentParser()
tools = root.add_subparsers(help="Tools")

mock_uav = tools.add_parser("mock-uav", help="Utility to mock the UAV locally")
mock_uav.add_argument("--device", type=str, default="udpin:127.0.0.1:5600")
mock_uav.set_defaults(_command="mock-uav")

args = root.parse_args()

if '_command' not in args:
    # Usage error
    root.print_usage()
    sys.exit(2)

match args._command:
    case "mock-uav":
        mock_uav_main(args.device)
    case _:  # Unknown _command
        raise NotImplementedError("Unknown command: %r" % args._command)
