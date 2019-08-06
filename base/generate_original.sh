#!/bin/bash
##!/bin/bash -l

source $CLS_FOLDER/const.sh

if [[ "$nb_args" != "4" ]]; then
	echo "ERROR! Invalid arguments (need the binary's folder path, the generated binary's name, the function's name and build path)."
	exit -1
fi


codelet_folder=$( readlink -f "$1" )
codelet_name="$2"
build_folder=$( readlink -f "$3" )
curr_compiler="$4"

echo mkdir "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"
mkdir "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER" &> /dev/null

build_codelet ${codelet_folder} ${codelet_name} ${build_folder} ${curr_compiler}

# The contract of this function is: In all cases, $codelet_name is under ${build_folder}

cp ${build_folder}/"$codelet_name" "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"
res=$?
if [[ "$res" != "0" ]]; then
	echo "ERROR! Copy of binary to binary folder failed"
	exit -1
fi

exit 0
