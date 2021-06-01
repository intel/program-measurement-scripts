#!/bin/bash

# Starting this script under container directory will also mount the tmp directory in container
docker run --rm -it -v "$(pwd -W)\workspace":/workspace  \
-e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 22:22/tcp capeexperimentscripts:latest