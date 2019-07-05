#!/bin/bash
#
# Runs Pigeon Tests
# 
# Usage: `./run_tests.sh`
#
# Inital Creation by Ryan Sandoval

DIR=$(cd $(dirname $0) && pwd)

if ! [ -d ${DIR}/modules/interop/client ]; then
    echo "Could not find ${DIR}/modules/interop/client containing interop client library. Aborting."
    exit 1
fi

CLIENT=${DIR}/modules/interop/client

export PYTHONPATH=${PYTHONPATH}:$CLIENT

cd station && ${DIR}/env/venv3/bin/python3 test.py
exit $?
