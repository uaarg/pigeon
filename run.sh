#!/bin/bash
#
# Runs Pigeon
# 
# Usage: `./run.sh`
#
# Inital Creation by Ryan Sandoval

DIR=$(cd $(dirname $0) && pwd)

if ! [ -d ${DIR}/modules/interop/client ]; then
    echo "Could not find ${DIR}/modules/interop/client containing interop client library. Aborting."
    exit 1
fi

# Attach interop client to PYTHONPATH
CLIENT=${DIR}/modules/interop/client
export PYTHONPATH=${PYTHONPATH}:$CLIENT

# Find station and go to it!
STATION_LOCATION=$(find -name station.py)
STATION_DIR=$(dirname ${STATION_LOCATION})
cd ${STATION_DIR} && ${DIR}/venv3/bin/python3 station.py
exit 0
