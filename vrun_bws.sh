#!/bin/bash -l

codelets_path="/home/users/vpalomares/nfs/codelets/NR_format/NRs/bws/bws_quadruple_stream/"
variants="time_reference"
sizes="2048 16384 1310720 10485760"
memory_loads="0"
frequencies="1200000 2700000"


for codelet in "$codelets_path"/*
do
	echo "Launching CLS on '$codelet'..."
	./cls.sh "$codelet" "$variants" "$sizes" "$memory_loads" "$frequencies"	&> "$codelet/cls.log"
	res=$?
	if [[ "$res" != "0" ]]
	then
		echo -e "\tAn error occured! Check '$codelet/cls.log' for more information."
	fi
done
