#!/bin/bash

# Fetch latest image
docker pull registry.gitlab.com/davidwong/cape-experiment-scripts:latest

script_dir=$(dirname $0)
root_dir=$(readlink -f ${script_dir}/..)
docker run --rm  -v ${root_dir}/cape-experiment-scripts:/home/appuser/cape-experiment-scripts -it registry.gitlab.com/davidwong/cape-experiment-scripts:latest