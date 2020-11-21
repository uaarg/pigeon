#!/bin/bash
#
# Runs Pigeon Tests
# 
# Usage: `./run_tests.sh` <args..>
#
# Examples: `./run_tests.sh`
#           `./run_tests.sh textexport`
#
# Inital Creation by Ryan Sandoval

#############
# Variables #
#############

ARGS=( "${@}" )
DIR=$(cd $(dirname $0) && pwd)

#############

# Allows access to the interop client module
if ! [ -d ${DIR}/modules/interop/client ]; then
    echo "Could not find ${DIR}/modules/interop/client containing interop client library. Aborting."
    exit 1
fi

CLIENT=${DIR}/modules/interop/client
export PYTHONPATH=${PYTHONPATH}:$CLIENT

cd station && ${DIR}/venv3/bin/python3 test.py "${ARGS}"
exit $?
