#!/bin/bash
#
# Runs Pigeon
# 
# Usage: `./run.sh`
#
# Inital Creation by Ryan Sandoval

DIR=$(cd $(dirname $0) && pwd)

cd station && ${DIR}/env/venv3/bin/python3 station.py