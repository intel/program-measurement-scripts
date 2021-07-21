#!/bin/bash

# Ensure user logged in
local_gids=$(id -G)
local_gnames=$(id -Gn)

echo "Logging into registry.gitlab.com... (it may ask for gitlab.com password if not done before)"
docker login registry.gitlab.com
# Fetch latest image
docker pull registry.gitlab.com/davidwong/cape-experiment-scripts:latest

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

docker build --build-arg http_proxy=$http_proxy_arg --build-arg https_proxy=$https_proxy_arg --build-arg LOCAL_UID=$(id -u ${USER}) --build-arg LOCAL_GID=$(id -g ${USER}) --build-arg LOCAL_GIDS="$local_gids" --build-arg LOCAL_GNAMES="$local_gnames" --pull --rm -f ./LocalDockerfile -t local_image .
