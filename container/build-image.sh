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

#rm -rf rose-utils
#mkdir -p rose-utils
#pushd rose-utils
# User the image builder's .ssh
if [ ! -d rose-utils ]; then
  git clone https://gitlab.com/Wingpad/rose-utils.git --config core.autocrlf=input
#popd
fi

if [ ! -d ice-locus-dev ]; then
  git clone https://bitbucket.org/thiagotei/ice-locus-dev.git  --config core.autocrlf=input
fi

if [ ! -d pocc-1.1 ]; then
  curl -O http://web.cs.ucla.edu/~pouchet/software/pocc/download/pocc-1.1-full.tar.gz
  tar xvf pocc-1.1-full.tar.gz
  cd pocc-1.1
  curl -O https://bitbucket.org/thiagotei/uiuc-compiler-opts/raw/39556c88b86e6a7e727117183c93906ab89ffeb1/pocc-1.1-candl-0.6.2.patch
fi

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