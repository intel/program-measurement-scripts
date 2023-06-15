#!/bin/bash

# Run this script once to get needed components built

# First built the local container (with SEP included)
# the image is called local_image
pushd container
./build-local-image.sh
popd

# Build the codeet probe using the container.
# This assumes EMON API has been installed at /opt/intel/sep already
docker run -v /:/host local_image:latest /bin/bash -c \
	"source /opt/intel/sep/sep_vars.sh emon_api; pushd /host/"$(pwd)"/utils/codeletProbe; make clean; make"

#pushd utils/codeletProbe/
#make
#popd

# Build PrOMPT if ICC is available
icc_path=$(which icc)
if [[ ${icc_path} != "" ]]; then
  echo "Building PrOMPT using ${icc_path}"
  icc_folder=$(dirname ${icc_path})
  docker run -v /:/host local_image:latest /bin/bash -c \
	"export PATH=/host/${icc_folder}:${PATH}; if [[ -d /host/"$(pwd)"/utils/PrOMPT ]]; then  pushd /host/"$(pwd)"/utils/PrOMPT; make clean; make; fi"

fi
