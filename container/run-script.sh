#!/bin/bash

# Fetch latest image
docker pull registry.gitlab.com/davidwong/cape-experiment-scripts:latest

script_dir=$(dirname $0)
root_dir=$(readlink -f ${script_dir}/..)
#docker run --rm  -v ${root_dir}:/home/appuser/cape-experiment-scripts -it registry.gitlab.com/davidwong/cape-experiment-scripts:latest
docker run --rm  -v ${root_dir}:/home/appuser/cape-experiment-scripts -it local_image:latest
