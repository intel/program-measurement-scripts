#!/bin/bash

rm -rf container/rose-utils
mkdir -p container/rose-utils
pushd container/rose-utils
# User the image builder's .ssh
git clone git@gitlab.com:Wingpad/rose-utils.git
popd

#docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --pull --rm -f "container\Dockerfile" -t capeexperimentscripts:latest "container"
# Below assums proxy servers are needed to access the network
docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --pull --rm -f "container\Dockerfile" -t capeexperimentscripts:latest "container"

# Also build the image to Gitlab
# login only need to be done once for password entering
docker login registry.gitlab.com

docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --pull --rm -f "container\Dockerfile" -t registry.gitlab.com/davidwong/cape-experiment-scripts  "container"
docker push registry.gitlab.com/davidwong/cape-experiment-scripts