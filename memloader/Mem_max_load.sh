#!/bin/bash

cores=$( cat /sys/devices/system/cpu/online )

echo "Cores: '$cores'"

if [[ "$cores" != "0" ]]
then
	cores=$( echo "$cores" | sed "s/\-/ /g" )
	cores=$( seq $cores | tr "\n" " " )
	echo "New cores: '$cores'"
fi


./Mempinner.sh 99999 "$cores"
sleep 30
./Memkiller.sh
