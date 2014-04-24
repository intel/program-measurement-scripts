#!/bin/bash

source ./const.sh

bin_path="$1"
loop_id="$2"

rm -f *.csv
for mode in MEM_VEC COMPUTE_VEC FULLY_VEC VECTOR_ISET FP FP_ARITH
do
	for option in none force_sse
	do
		if [[ "$option" != "none" ]]
		then
			option_arg="imo=$option"
		else
			option_arg=""
		fi

		echo "Mode: $mode, option arg: $option_arg"
		echo "\"$MAQAO\" module=cqa bin=\"$bin_path\" loop=\"$loop_id\" uarch=SANDY_BRIDGE of=csv -ext im=$mode $option_arg"
		"$MAQAO" module=cqa bin="$bin_path" loop="$loop_id" uarch=SANDY_BRIDGE of=csv -ext im=$mode $option_arg
		mv loops.csv "if_vec_${mode}_$option.csv"

		echo
	done
done
