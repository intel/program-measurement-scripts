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
if lsmod |grep pax &> /dev/null; then
    echo "Driver loaded in host.  Please stop the driver before running this container."
    exit -1
fi

# Build arguments to mount host directories
mount_args=()
mount_dirs=(/opt /localdisk /nfs)
mount_dirs=(/localdisk /nfs)
for dir in ${mount_dirs[*]}; do
    mount_args+=( "-v $dir:$dir" )
done
mount_args+=( "-v $HOME:/home/runner" )

# Build arguments to pass environmental variables
env_args=()
vars=(http_proxy https_proxy)
for var in ${vars[*]}; do
  if [[ ! -z ${!var} ]]; then
    env_args+=("-e $var=${!var}")
  fi
done


# Start driver
docker run -u root -v /dev:/dev --pid=host --ipc=host --privileged local_image:latest /bin/bash -c "pushd /opt/intel/sep/sepdk/src; ./insmod-sep -g docker"

docker run --rm  ${mount_args[*]} ${env_args[*]} -v /:/host -v /usr/src/linux-headers-$(uname -r):/usr/src/linux-headers-$(uname -r) -v /lib/modules:/lib/modules -v /usr/src/linux-headers-4.4.0-62:/usr/src/linux-headers-4.4.0-62 -v /tmp/tmp:/tmp/tmp -v /dev:/dev -v /usr/include:/usr/include --pid=host --ipc=host -it --privileged local_image:latest 

# Stop driver
docker run -u root -v /dev:/dev --pid=host --ipc=host --privileged local_image:latest /bin/bash -c "pushd /opt/intel/sep/sepdk/src; ./rmmod-sep" 
#container_id=$(docker run --rm  ${mount_args[*]} ${env_args[*]} -v /:/host -v /usr/src/linux-headers-$(uname -r):/usr/src/linux-headers-$(uname -r) -v /lib/modules:/lib/modules -v /usr/src/linux-headers-4.4.0-62:/usr/src/linux-headers-4.4.0-62 -v /tmp/tmp:/tmp/tmp -v /dev:/dev -v /usr/include:/usr/include --pid=host --ipc=host -d -it --privileged local_image:latest )
# Run as root to start EMON driver.  Simply give access to docker group
#docker exec -u 0 ${container_id} sh -c "/opt/intel/sep_eng/sepdk/src/insmod-sep -g docker"

#docker attach ${container_id}
#docker exec -u 0 ${container_id} sh -c "/opt/intel/sep_eng/sepdk/src/rmmod-sep"
