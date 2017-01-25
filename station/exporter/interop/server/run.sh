#!/bin/bash
# Runs the Interop Server in a container.

docker run -d --restart=unless-stopped --interactive --tty --publish 8000:80 --name interop-server auvsisuas/interop-server
