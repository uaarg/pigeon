#!/bin/bash
#
# AUVSI Client Library Installer
#
# Installs the Interop Library provided from competition organizers
# https://github.com/auvsi-suas
#
# Usage: `./install.sh`
#
# Note that these commands are the same that would be run when Docker is
# is setting up the client container. See the wiki of github repo.

# Vars
DIR=$(cd $(dirname $0) && pwd)

# Test Sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi


# First make sure interop folder is here
if [ ! -d "interop" ]; then
    echo -e "Error: 'interop' folder could not be found. Aborting Installation."
    exit 1
fi

# Set the time zone to the competition time zone.
echo -n "Setting TimeZone to 'NewYork'..."
ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime
if [[ $? -ne 0 ]]; then 
    echo -e "Failed"
    exit 1
else
    echo -e "Done"    
fi

# Install dependencies
echo -n "Updating apt-get... "
apt-get -qq update

if [[ $? -ne 0 ]]; then 
    echo -e "Failed"
else
    echo -e "Done"    
fi

echo -n "Installing Dependencies..."
apt-get -qq install -y \
        libxml2-dev \
        libxslt-dev \
        protobuf-compiler \
        python3 \
        python3-dev \
        python3-nose \
        python3-pip \
        python3-pyproj \
        python3-lxml \
        sudo 
        
if [[ $? -ne 0 ]]; then 
    echo -e "Failed"
    exit 1
else
    echo -e "Done"    
fi

# Set up Protos for API
echo -n "Running setup.py"

bash -c "cd interop/client && \
    source ${DIR}/../venv3/bin/activate && \
    python3 setup.py install && \
    deactivate"

if [[ $? -ne 0 ]]; then 
    echo -e "Failed"
    exit 1
else
    echo -e "Done"    
fi

echo -e "Client API Installation Complete."

exit 0  
