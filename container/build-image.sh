#!/bin/bash

mkdir -p container/rose-utils
pushd container/rose-utils
# User the image builder's .ssh
#git clone git@gitlab.com:Wingpad/rose-utils.git
popd

#docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --pull --rm -f "container\Dockerfile" -t capeexperimentscripts:latest "container"
docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --pull --rm -f "container\Dockerfile" -t capeexperimentscripts:latest "container"
