#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "3" ]]
then
	echo "ERROR! Invalid arguments (need the binary's folder path, the generated binary's name and the function's name)."
	exit -1
fi


binary_folder=$( readlink -f "$1" )
binary_name="$2"
codelet_name="$3"

mkdir "$binary_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER" &> /dev/null

echo "Generating codelet '$binary_folder/$codelet_name'..."

cd "$binary_folder"
if [[ "$ENABLE_SEP" == "1" ]]
then
	make clean ENABLE_SEP=sep all
else
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
