#!/bin/bash

source $CLS_FOLDER/const.sh

if [[ "$nb_args" != "2" ]]
then
	echo "ERROR! Invalid arguments (need: run id, message)."
	exit -1
fi

runid="$1"
msg="$2"

LOG_FILE=${LOG_FOLDER}/log.${HOSTNAME}.txt


if [ ! -d ${LOG_FOLDER} ]; then
	mkdir ${LOG_FOLDER}
fi

echo ${msg}
echo "[${runid}] ${msg}" >> ${LOG_FILE}
