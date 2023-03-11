#!/bin/bash
#
# Installs the dependencies for Pigeon
#
# Also installs interop client library
# See Readme for specific dependencies
#
# Usage: `./install_dependencies.sh [-p]`
#
# Flags:
#   [-p] Run in pipeline mode (e.g. Bitbucket pipelines), disables user prompts.
#


# Variables
DIR=$(cd $(dirname $0) && pwd)
PIPELINE_MODE=0 # Run in pipeline (e.g. Bitbucket pipeline) mode.
CURRENT_USER=${SUDO_USER}

# Test Sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# Parse flags
while getopts "p" opt; do
    case "$opt" in
    p)  PIPELINE_MODE=1
        ;;
    esac
done

# Check that we can access original user name if not in bitbucket pipeline
if [[ PIPELINE_MODE -ne 1 && ${CURRENT_USER} == "" ]]; then
    echo "Error: Could not get user calling the script."
    exit 1
fi

# Need to set the timezone to New York when we go to the competition.
if [[ ${PIPELINE_MODE} -ne 1 ]]; then

    echo "Change Time Zone to competition location? (Y/N)"
    read ans

    if [[ "_${ans}" == "_Y" ]]; then
        ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime
        echo "Time zone has been changed"
    fi
fi
# If in pipeline mode, running on bitbucket. No need to change the timezone.

# Install Pigeon specific apt-gets
echo "Installing Apt Packages..."
apt-get -y install \
    libxml2-dev libxslt1-dev\
    libzbar0 \
    protobuf-compiler

if [ $? -ne 0 ]; then
    echo "Failed to Install Pigeon Apt-get Dependencies"
    exit 1
fi

# Set up Python virtualenv
# Decouples our dependencies from system packages.
echo "Setting up virtual environment..."
if [[ PIPELINE_MODE -eq 0 ]]; then 
    sudo -u "${CURRENT_USER}" python3 -m venv venv3
else
    python3 -m venv venv3
fi

if [[ $? -ne 0 ]]; then
    echo "Error: Could not create virtual environment."
    exit 1
fi

# Pigeon pip modules
echo "Installing Pigeon specific Python Libraries..."

# We have to use bash since sudo -u USER source venv/... doesn't work.
if [[ PIPELINE_MODE -eq 0 ]]; then
    sudo -u "${CURRENT_USER}" bash << EOF
        source ${DIR}/venv3/bin/activate && \
        pip3 install -r requirements.txt && \
        deactivate
EOF
else 
    source ${DIR}/venv3/bin/activate && \
    pip3 install -r requirements.txt && \
    deactivate
fi

if [ $? -ne 0 ]; then
    echo "Failed to Install Pigeon pip Modules"
    exit 1
fi

# AUVSI interop server is no longer used as of 2023

echo "Installing pyproj transformation grids..."
# Get pyproj transformation grids.
# https://pyproj4.github.io/pyproj/stable/transformation_grids.html#transformation-grids
source ${DIR}/venv3/bin/activate && \
    export PROJ_DOWNLOAD_DIR=$(python3 -c "import pyproj; print(pyproj.datadir.get_data_dir())") && \
    wget --mirror https://cdn.proj.org/ -P ${PROJ_DOWNLOAD_DIR}

err_code=$?
# For some reason... error code 8 is normal 
if [[ err_code -ne 0 && err_code -ne 8 ]]; then 
    echo "Failed to install pyproj transformation grids... Error code:${err_code}"
    exit 1
fi

if [[ PIPELINE_MODE -ne 1 ]]; then
    echo "Changing venv to be owned by current user..."
    chown -R "${CURRENT_USER}" venv3
fi

echo "Installation Complete."

exit 0
