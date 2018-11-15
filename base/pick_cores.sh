#!/bin/bash -l

# Assume const.sh under same directory as this script
source $(dirname $0)/const.sh

if [[ "$1" == "" ]]; then
  echo "ERROR! Invalid arguments (need: res_path)."
  exit -1
fi

NUM_CORES=$(echo "$1" | sed "s|.*/numcores_\([^/]*\).*|\1|g")

NC_ALL_CORES=()
for ((i=(${#XP_ALL_CORES[@]}-1);i>=(${#XP_ALL_CORES[@]}-$NUM_CORES);i--)); do
  NC_ALL_CORES+=(${XP_ALL_CORES[$i]})
done

CORES_TO_USE=$(echo ${NC_ALL_CORES[@]} | sed 's/\ /,/g')

echo "Running codelets with $NUM_CORES core(s). Chose core(s): $CORES_TO_USE"
