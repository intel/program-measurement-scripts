#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "2" ]]
then
	echo "ERROR! Invalid arguments (need: run id, message)."
	exit -1
fi

runid="$1"
msg="$2"

if [ ! -d ${LOG_FOLDER} ]; then
    mkdir ${LOG_FOLDER}
fi

echo ${msg}
echo "[${runid}] ${msg}" >> ${LOG_FILE}
