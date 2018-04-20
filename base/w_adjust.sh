#!/bin/bash

source $CLS_FOLDER/const.sh

if [ -f /opt/intel/sep/sep_vars.sh ]; then
    source /opt/intel/sep/sep_vars.sh > /dev/null
fi

if [[ "$nb_args" != "6" ]]; then
	echo "ERROR! Invalid arguments (need: codelet's folder, binary's name, desired size, minimum number of repetitions, max number of repetition, desired length)."
	exit -1
fi

codelet_folder="$1"
binary_name="$2"
desired_size="$3"
min_repet="$4"
max_repet="$5"
desired_length="$6"

echo "W_adjust: Going to assess the right number of repetitions (to reach $desired_length hundredths of second) for codelet '$codelet_folder' with a data set of '$desired_size'"
cd "$codelet_folder"

current_repetitions=$min_repet
saved_repetitions=$min_repet
res=0

cd $codelet_folder

while [ $res -lt $desired_length  -a $current_repetitions -le ${HARD_MAX_REPETITIONS} -a $current_repetitions -ge 0 ]
do
  	if [[ $current_repetitions -ge ${MAX_REPETITIONS} ]]; then
	    echo "max repetitions reached, setting repetition to ${MAX_REPETITIONS}"
	    saved_repetitions=${MAX_REPETITIONS}
	    break
	fi

	echo "Trying number of repetitions = $current_repetitions"
	echo "$current_repetitions $desired_size" > codelet.data
	saved_repetitions=$current_repetitions

	res=$(LD_LIBRARY_PATH=${BASE_PROBE_FOLDER}:${LD_LIBRARY_PATH} /usr/bin/time -f %e ./${binary_name} 2>&1 )
	val_res=$?

	if [[ "$val_res" != "0" ]]; then
		echo "Error while running the codelet. Aborting."
		echo "Res: '$res'"
		exit -1
	fi

	res=$( echo -e "$res" | tail -n 1 )

	#echo "Res time: $res"
	res=$( echo $res | sed "s/\.//g" )
	#echo "Res without dot: $res"
	res=$( echo $res | sed 's/^[0]*//' )
	#echo "Res without 0s: $res"
	echo "Got: ${res} while targeting to ${desired_length}"

	if [[ "$res" == "" ]]; then
		#echo "Took 0.0s => multiplying by 10"
		let "current_repetitions = $current_repetitions * 10"
		#echo "Forced repetitions = $current_repetitions"
		res=0
	else
		if [ $res -lt $desired_length  ]; then
#			let "current_repetitions = $current_repetitions * (($desired_length  / $res) + 1)"
#			let "current_repetitions = $current_repetitions * (($desired_length  / $res) + 1)"
                        current_repetitions=$(echo ${current_repetitions} ${res} ${desired_length} |awk '{x=$1*(($3/$2)); print (x-int(x) > 0)?int(x)+1:int(x)}')
			#echo "Deduced repetitions = $current_repetitions"
		fi
	fi
done

echo "Done: saved_repetitions = $saved_repetitions"
echo "$desired_size $saved_repetitions" >> repetitions_history

exit 0
