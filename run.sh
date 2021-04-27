#!/bin/bash
#
# Runs Pigeon
# 
# Usage: `./run.sh`
#
# Inital Creation by Ryan Sandoval

DIR=$(cd $(dirname $0) && pwd)

# Find station and go to it!
STATION_LOCATION=$(find -name station.py)
STATION_DIR=$(dirname ${STATION_LOCATION})
cd ${STATION_DIR} && ${DIR}/venv3/bin/python3 station.py
exit 0
