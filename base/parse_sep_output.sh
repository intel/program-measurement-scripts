#!/bin/bash  -l

source ./const.sh


if [[ "$1" == "" ]]; then
	echo "ERROR! Invalid arguments (need: codelet's output results folder)."
	exit -1
fi

res_path="$1"

rm -f "$res_path/emon_report"

emon_counters_core=$(cat $res_path/core_events_list)
emon_counters_uncore=$(cat $res_path/uncore_events_list)

	for i in $( seq $META_REPETITIONS )
	do
		for events in $(echo $emon_counters_core | tr ${DELIM} ' ')
		do
			events_code=$(echo $events | cut -d':' -f1)
			output=$res_path"/sep_report_"$events_code"_"$i".txt"
echo "Parsing $output ...!"
			for event in $(echo $events | cut -d':' -f2 | tr ',' ' ')
			do
				values=$(echo $(grep $event  $output | cut -d',' -f 3) | tr ' ' ${DELIM})
				echo "$event"${DELIM}${DELIM}"$values" >> "$res_path/emon_report" 
			done
		done

		for events in $(echo $emon_counters_uncore  | tr ${DELIM} ' ')
		do
			events_code=$(echo $events | cut -d':' -f1)
			events=$(echo $events | cut -d':' -f2)

			sfdump $res_path"/sep_report_"$events_code"_"$i".tb6" -samples -out
			tb6totsv=$res_path"/sep_report_"$events_code"_"$i"_s.tsv"
			sed -i "s:\t:,:g" $tb6totsv

			for event in $(echo $events | tr ',' ' ')
			do
				column=$(head -n 1 "$tb6totsv" | tr ',' '\n' | nl | grep "$event" | cut -f1)
				if [[ "$(echo $column | tr ' ' '\n' | wc -l)" == "1" ]];then
					begin=$(head -n 2 "$tb6totsv" | tail -n 1 | cut -d',' -f $column)
					end=$(tail -n 1 "$tb6totsv" | cut -d',' -f $column)
				else
					begin=$(head -n 2 "$tb6totsv" | tail -n 1 | cut -d',' -f $(echo $column | tr ' ' ',') | tr ',' ' ')
					let val=0
					for v in $begin
					do	
						val=$(( $val + $v))
					done
					begin=$val
					end=$(tail -n 1 "$tb6totsv" | cut -d',' -f $(echo $column | tr ' ' ',') | tr ',' ' ')
					val=0
					for v in $end
					do
						val=$(( $val + $v))
					done
					end=$val
				fi
				value=$(expr $end - $begin)
				echo "$event"${DELIM}${DELIM}"$value" >> "$res_path/emon_report"
			done
		done
	done

exit 0
