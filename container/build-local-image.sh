#!/bin/bash

# Ensure user logged in

echo "Logging into registry.gitlab.com... (it may ask for gitlab.com password if not done before)"
docker login registry.gitlab.com
# Fetch latest image
docker pull registry.gitlab.com/davidwong/cape-experiment-scripts:latest

docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --build-arg LOCAL_UID=$(id -u ${USER}) --build-arg LOCAL_GID=$(id -g ${USER}) --pull --rm -f ./LocalDockerfile -t local_image .
