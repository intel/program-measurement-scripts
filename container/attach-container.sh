#!/bin/bash

id=$(docker ps  |grep local_image:latest |head -1|cut -f1 -d' ')
docker exec -it  $id /bin/bash

