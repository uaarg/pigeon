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

if [[ ${CURRENT_USER} == "" ]]; then
    echo "Error: Could not get user calling the script."
    exit 1
fi

# Parse flags
while getopts "p" opt; do
    case "$opt" in
    p)  PIPELINE_MODE=1
        ;;
    esac
done

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
    qtdeclarative5-dev qtmultimedia5-dev python3-pyqt5 \
    python3-shapely \
    libxml2-dev libxslt1-dev\
    libzbar0

if [ $? -ne 0 ]; then
    echo "Failed to Install Pigeon Apt-get Dependencies"
    exit 1
fi

# Set up Python virtualenv
# Decouples our dependencies from system packages.
echo "Setting up virtual environment..."
sudo -u "${CURRENT_USER}" python3 -m venv --system-site-packages venv3

if [[ $? -ne 0 ]]; then
    echo "Error: Could not create virtual environment."
    exit 1
fi

echo "Installing Interop Client Library... This may take a while!"

# Install Interop Client Lib from the AUVSI git repository
# Note: The client library is in a subdirectory, so we use #subdirectory=...
source ${DIR}/venv3/bin/activate && \
    pip3 install "git+https://github.com/auvsi-suas/interop.git#subdirectory=client"

if [[  $? -ne 0 ]]; then
    echo "Failed to Install Interop Client Library"
    exit 1
fi

# Pigeon pip modules
echo "Installing Pigeon specific Python Libraries..."
source ${DIR}/venv3/bin/activate && \
    pip3 install -r requirements.txt && \
    deactivate

if [ $? -ne 0 ]; then
    echo "Failed to Install Pigeon pip Modules"
    exit 1
fi

echo "Installation Complete."

exit 0
