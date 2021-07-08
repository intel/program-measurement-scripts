#!/bin/bash

# Run this script once to get needed components built

# Build the codeet probe.
# This assumes EMON API has been installed at /opt/intel/sep already
pushd utils/codeletProbe/
make
popd

pushd container
./build-local-image.sh


