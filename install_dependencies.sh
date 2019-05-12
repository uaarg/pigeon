#!/bin/bash
#
# Installs the dependencies for Pigeon
# Also installs interop client library
#
# Usage: `./install_dependencies.sh`
#
# Initially Creation by Ryan Sandoval

DIR=$(cd $(dirname $0) && pwd)

# Setup out submodules
echo "Setting up Submodules..."
git submodule init && git submodule update

if [ $? -ne 0 ]; then
    tput setaf 1
    echo "Submodule failed to clone. Aborting."
    tput setaf 9
    exit 1
fi

printf "\n\n"

# Install Pigeon specific apt-gets
echo "Installing Pigeon Packages..."
apt-get install python3 python3-dev \
    qtdeclarative5-dev qtmultimedia5-dev python3-pyqt5 \
    python3-shapely python3-pip \
    libxml2-dev libxslt1-dev

if [ $? -ne 0 ]; then
    tput setaf 1
    echo "Failed to Install Pigeon Apt-get Dependencies"
    tput setaf 9
    exit 1
fi

printf "\n\n"

# Install Interop Client Lib
echo "Installing Interop Client Libraries..."

cd modules && ./install_interop_export.sh

if [ $? -ne 0 ]; then
    tput setaf 1
    echo "Failed to Install Interop Client Libraries"
    tput setaf 9
    exit 1
fi

printf "\n\n"

# Pigeon pip modules
echo "Installing Pigeon specific Python Libraries"
bash -c "
    source ${DIR}/env/venv3/bin/activate && \
    pip3 install pyinotify pyproj pykml==0.1.0 && \
    pip3 install git+https://github.com/camlee/ivy-python && \
    pip3 install requests && \
    deactivate"

if [ $? -ne 0 ]; then
    tput setaf 1
    echo "Failed to Install Pigeon pip Modules"
    tput setaf 9
    exit 1
fi

tput setaf 2
echo "Installation Complete."
tput setaf 9

exit 0
