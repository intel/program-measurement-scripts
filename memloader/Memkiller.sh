#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "1" ]]
then
	echo "ERROR! Invalid arguments (need: Memloader's folder)."
	exit -1
fi

memloader_path="$1"

echo "Killing all Memloaders..."
killall -2 Memloader
sleep 3


echo "Computing globally consumed BW..."
cat "$memloader_path/"tmp_res_${HOSTNAME}_* | grep "Global average bandwidth:" $i | awk 'BEGIN { FS="\t"; IFS="\t"; OFS="\t"; } {  print $5; }' | cut -f1 -d' ' | awk 'BEGIN {res = 0;} {res += $1;} END {print res / (1024 * 1024) " MB/s";}'
rm -f "$memloader_path/"tmp_res_${HOSTNAME}_*
