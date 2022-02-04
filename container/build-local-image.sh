#!/bin/bash
# Build a local image for CapeScript runs
# By default production image will be used but can specify other tags.

tag_img=production
if [[ $# == 1 ]]; then
	tag_img="${1}"
fi
img_name=registry.gitlab.com/davidwong/cape-experiment-scripts:${tag_img}
echo Base image name is: ${img_name}

# Ensure user logged in
local_gids=$(id -G)
local_gnames=$(id -Gn)

echo "Logging into registry.gitlab.com... (it may ask for gitlab.com password if not done before)"
docker login registry.gitlab.com
# Fetch latest image
docker pull ${img_name}

# Try to build EMON using host compiler 
sep_dir=sep_eng
id=$(docker create ${img_name})
# Copy out the sep files
docker cp $id:/opt/intel/${sep_dir} ./${sep_dir}
docker rm -v $id
pushd ./${sep_dir}/sepdk/src
./build-driver -ni
popd
# after building the driver, the local dockerfile will copy the results back to the local image.

if [[ $http_proxy != http* ]]; then
  http_proxy_arg=http://${http_proxy}
else
  http_proxy_arg=${http_proxy}
fi

if [[ $https_proxy != http* ]]; then
  https_proxy_arg=http://${https_proxy}
else
  https_proxy_arg=${https_proxy}
fi

docker build --build-arg IMG_NAME=${img_name} --build-arg SEP_DIR=${sep_dir} --build-arg http_proxy=$http_proxy_arg --build-arg https_proxy=$https_proxy_arg --build-arg LOCAL_UID=$(id -u ${USER}) --build-arg LOCAL_GID=$(id -g ${USER}) --build-arg LOCAL_GIDS="$local_gids" --build-arg LOCAL_GNAMES="$local_gnames" --pull --rm -f ./LocalDockerfile -t local_image .
