#!/bin/bash

push_image=false
while getopts ":p" opt; do
  case ${opt} in
  p)
    push_image=true
    ;;
  \?)
    echo "Usage: $0 [-p]"
    exit
    ;;
  esac
done

rm -rf rose-utils
#mkdir -p rose-utils
#pushd rose-utils
# User the image builder's .ssh
git clone https://gitlab.com/Wingpad/rose-utils.git --config core.autocrlf=input
#popd

git clone https://bitbucket.org/thiagotei/ice-locus-dev.git  --config core.autocrlf=input

#docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --pull --rm -f "container\Dockerfile" -t capeexperimentscripts:latest "container"
# Below assums proxy servers are needed to access the network
#docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --pull --rm -f ".\Dockerfile" -t capeexperimentscripts:latest "."

# login only need to be done once for password entering
docker login registry.gitlab.com
# Also build the image to Gitlab
docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --pull --rm -f ".\Dockerfile" -t registry.gitlab.com/davidwong/cape-experiment-scripts  "."

if [[ $push_image = true ]]; then
  docker push registry.gitlab.com/davidwong/cape-experiment-scripts
fi