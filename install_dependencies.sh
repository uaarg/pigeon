#!/bin/bash
#
# Installs the dependencies for Pigeon
#
# Also installs interop client library
# See Readme for specific dependencies
#
# Usage: `./install_dependencies.sh [-p]`
# Flags:
#   [-p] Run in pipeline mode, disables user prompts.
#


# Variables
DIR=$(cd $(dirname $0) && pwd)

# Run in pipeline mode.
PIPELINE_MODE=0

# Parse flags
while getopts "p" opt; do
    case "$opt" in
    p)  PIPELINE_MODE=1
        ;;
    esac
done


# Test Sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# Setup out submodules
echo "Setting up Submodules..."
git submodule init && git submodule update

if [ $? -ne 0 ]; then
    echo "Submodule failed to clone. Aborting."
    exit 1
fi

printf "\n\n"

# Install Pigeon specific apt-gets
echo "Installing Pigeon Packages..."
apt-get -y install \
    qtdeclarative5-dev qtmultimedia5-dev python3-pyqt5 \
    python3-shapely \
    libxml2-dev libxslt1-dev \

if [ $? -ne 0 ]; then
    echo "Failed to Install Pigeon Apt-get Dependencies"
    exit 1
fi

printf "\n\n"

# Set up Python virtualenv
# Used to allow different version installation of dependencies
echo "Setting up packages..."

bash -c "python3 -m venv --system-site-packages venv3  && \
    source ${DIR}/venv3/bin/activate && \
    pip install wheel && \
    pip3 install -r ${DIR}/modules/interop/client/requirements.txt && \
    deactivate"

if [[ $? -ne 0 ]]; then 
    echo -e "Failed"
    exit 1
else
    echo -e "Done"    
fi

# Install Interop Client Lib
echo "Installing Interop Client Libraries..."

if [[ $PIPELINE_MODE -ne 1 ]]; then
    cd modules && ./install_interop_export.sh
else
    cd modules && ./install_interop_export.sh -p
fi

if [ $? -ne 0 ]; then
    echo "Failed to Install Interop Client Libraries"
    exit 1
fi

printf "\n\n"

# Pigeon pip modules
echo "Installing Pigeon specific Python Libraries"
bash -c "
    source ${DIR}/venv3/bin/activate && \
    pip3 install pyinotify pyproj pykml==0.1.0 && \
    pip3 install git+https://github.com/camlee/ivy-python && \
    pip3 install requests && \
    deactivate"

if [ $? -ne 0 ]; then
    echo "Failed to Install Pigeon pip Modules"
    exit 1
fi

echo "Installation Complete."

exit 0
