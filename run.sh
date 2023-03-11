#!/bin/bash
#
# Runs Pigeon
# 
# Usage: `./run.sh`
#
# Inital Creation by Ryan Sandoval

DIR=$(cd $(dirname $0) && pwd)

# Start Mavproxy instant to forward packets to our script and autopilot QGroundControl
# mavproxy.py --master=/dev/ttyUSB1 --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551 --non-interactive > /dev/null &

# Find station and go to it!
STATION_LOCATION=$(find -name station.py)
STATION_DIR=$(dirname ${STATION_LOCATION})
cd ${STATION_DIR} && ${DIR}/venv3/bin/python3 station.py
exit 0
