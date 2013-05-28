#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "3" ]]
then
	echo "ERROR! Invalid arguments (need: codelet's folder, codelet name, variants)."
	exit -1
fi

codelet_folder=$( readlink -f "$1" )
codelet_name="$2"
variants="$3"


echo "Cleaning up '$codelet_folder'"

cd "$codelet_folder"

rm -f *.dprof
rm -f "$codelet_name"

for variant in $variants
do
	rm -f "${codelet_name}_${variant}_cpi" "${codelet_name}_${variant}_hwc"
done


exit 0
