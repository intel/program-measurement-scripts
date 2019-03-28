#!/bin/bash -l

source $(dirname $0)/const.sh


if [[ "$nb_args" > "1" ]]
then
	echo "ERROR! Invalid arguments (need: run description (optional))."
	exit -1
fi

if [[ "$nb_args" < "1" ]]
then
	read -p "Enter a brief desc for this run: " rundesc
else
	rundesc="$1"
fi


START_VRUN_SH=$(date '+%s')
