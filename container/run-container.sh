#!/bin/bash

# Fetch latest image
#docker pull registry.gitlab.com/davidwong/cape-experiment-scripts:latest

#script_dir=$(dirname $0)
#root_dir=$(readlink -f ${script_dir}/..)
#docker run --rm  -v ${root_dir}:/home/appuser/cape-experiment-scripts -it registry.gitlab.com/davidwong/cape-experiment-scripts:latest
#docker run --rm  -v ${root_dir}:/home/appuser/cape-experiment-scripts -it local_image:latest
#docker run --rm  -v /nfs:/nfs -v /opt:/opt -v /localdisk:/localdisk -v /:/host -it local_image:latest
#docker run --rm  -v /nfs:/nfs -v /opt:/opt -v /localdisk:/localdisk -v /:/host -it --privileged local_image:latest
#docker run --rm  -v /opt:/opt -v /localdisk:/localdisk -v /:/host -it --privileged local_image:latest

# Build arguments to mount host directories
mount_args=()
mount_dirs=(/opt /localdisk /nfs)
for dir in ${mount_dirs[*]}; do
    mount_args+=( "-v $dir:$dir" )
done

# Build arguments to pass environmental variables
env_args=()
vars=(http_proxy https_proxy)
for var in ${vars[*]}; do
  if [[ ! -z ${!var} ]]; then
    env_args+=("-e $var=${!var}")
  fi
done

docker run --rm  ${mount_args[*]} ${env_args[*]} -v /:/host -it --privileged local_image:latest
