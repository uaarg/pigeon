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

cd station && ${DIR}/venv3/bin/python3 test.py "${ARGS}"
exit $?
