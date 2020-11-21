#!/bin/bash
#
# AUVSI Client Library Installer
#
# Installs the Interop Library provided from competition organizers
# https://github.com/auvsi-suas
#
# Usage: `./install_interop_export.sh [-p]` 
# Flags:
#   [-p]: Pipelinemode. No user prompts.
#
# Note that these commands are the same that would be run when Docker is
# is setting up the client container. See the wiki of github repo.

PIPELINE_MODE=0
# Parse flags
while getopts "p" opt; do
    case "$opt" in
    p)  PIPELINE_MODE=1
        ;;
    esac
done


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

if [[ ${PIPELINE_MODE} -ne 1 ]]; then

    echo "Change Time Zone to competition location? (Y/N)"
    read ans

    if [[ "_${ans}" == "_Y" ]]; then
ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime
        echo "Time zone has been changed"
    fi
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
apt-get update && apt-get install -y \
        libxml2-dev \
        libxslt-dev \
        protobuf-compiler \
        python3-nose \
        python3-pip \
        python3-pyproj \
            python3-lxml
        
if [[ $? -ne 0 ]]; then 
    echo -e "Failed"
    exit 1
else
    echo -e "Done"    
fi

# Set up Python virtualenv
# Used to allow different version installation of dependencies
echo "Setting up packages..."

bash -c "cd ${DIR}/interop/client && \
    virtualenv --system-site-packages -p /usr/bin/python2 ${DIR}/../env/venv2 && \
    source ${DIR}/../env/venv2/bin/activate && \
    pip install -r requirements.txt && \
    deactivate" && \
bash -c "cd interop/client && \
    virtualenv --system-site-packages -p /usr/bin/python3 ${DIR}/../env/venv3 && \
    source ${DIR}/../env/venv3/bin/activate && \
    pip3 install -r requirements.txt && \
    deactivate"

if [[ $? -ne 0 ]]; then 
    echo -e "Failed"
    exit 1
else
    echo -e "Done"    
fi

# Set up Protos for API
echo -n "Running setup.py"

bash -c "cd interop/client && \
    source ${DIR}/../env/venv2/bin/activate && \
    python setup.py install && \
    deactivate" && \
bash -c "cd interop/client && \
    source ${DIR}/../env/venv3/bin/activate && \
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
