#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "4" ]]
then
	echo "ERROR! Invalid arguments (need the binary's folder path, the generated binary's name, the function's name and build path)."
	exit -1
fi


binary_folder=$( readlink -f "$1" )
binary_name="$2"
codelet_name="$3"
build_folder=$( readlink -f "$4" )

echo mkdir "$binary_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"
mkdir "$binary_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER" &> /dev/null

echo "Generating codelet '$binary_folder/$codelet_name'..."

build_files=$(find ${binary_folder} -maxdepth 1 -type f -o -type l)
cp ${build_files} ${build_folder}

cd ${build_folder}
#cd "$binary_folder"


if [[ "$ENABLE_SEP" == "1" ]]
then
    make clean ENABLE_SEP=sep ${emon_api_flags} all
else
    if [[ "$ACTIVATE_EMON_API" == "1" ]]
	then
	make clean LIBS="-lmeasure_emon_api -lprog_api -L/opt/intel/sep/bin64" all
	if [[ "$?" != "0" ]]
	    then
	    echo "ERROR! Make did not succeed in creating EMON API instrumented codelet."
	    exit -1
	fi
	mv "$binary_name" "$codelet_name"_emon_api
	cp "$codelet_name"_emon_api "$binary_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"
    fi
    # This will regenerate original binary without EMON API
    make clean all
fi

# &> /dev/null
res=$?

if [[ "$res" != "0" ]]
then
	echo "ERROR! Make did not succeed."
	exit -1
fi

mv "$binary_name" "$codelet_name"
res=$?

if [[ "$res" != "0" ]]
then
	echo "ERROR! Move did not succeed."
	exit -1
fi

cp "$codelet_name" "$binary_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"

if [[ -e "codelet.o" ]]
then
	cp "codelet.o" "$binary_folder/$CLS_RES_FOLDER/"	
fi

make clean &> /dev/null

echo "Codelet generation was successful."

exit 0
