#!/bin/bash -l

source $(dirname $0)/const.sh

if [[ "$nb_args" != "1" ]]
then
	echo "ERROR! Invalid arguments (need: seconds)."
	exit -1
fi

total_seconds=$1

secs_per_min=60
secs_per_hour=$((60*${secs_per_min}))
secs_per_day=$((24*${secs_per_hour}))

days=$((${total_seconds}/${secs_per_day}))
sec_remainder=$((${total_seconds} % ${secs_per_day}))

hours=$((${sec_remainder}/${secs_per_hour}))
sec_remainder=$((${sec_remainder} % ${secs_per_hour}))

mins=$((${sec_remainder}/${secs_per_min}))
secs=$((${sec_remainder} % ${secs_per_min}))

if [[ "${days}" -gt "0" ]]
then
	printf "%02d days %02d:%02d:%02d\n" ${days} ${hours} ${mins} ${secs}
else
	printf "%02d:%02d:%02d\n" ${hours} ${mins} ${secs}
fi
