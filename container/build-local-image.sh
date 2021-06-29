#!/bin/bash

docker build --build-arg LOCAL_UID=$(id -u ${USER}) --build-arg LOCAL_GID=$(id -g ${USER}) --pull --rm -f ./LocalDockerfile -t local_image .
