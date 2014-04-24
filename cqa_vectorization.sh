#!/bin/bash

source ./const.sh

bin_path="$1"
loop_id="$2"

mega_header=""
mega_content=""
#for mode in MEM_VEC COMPUTE_VEC FULLY_VEC VECTOR_ISET FP FP_ARITH
for mode in MEM_VEC FULLY_VEC VECTOR_ISET FP FP_ARITH
do
#	for option in none force_sse
	for option in force_sse
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
		header=$( head -n 1 loops.csv | sed 's/;$//g' | sed "s/;/;V($mode)($option)_/g" | sed "s/^/V($mode)($option)_/g" )
		content=$( tail -n 1 loops.csv | sed 's/;$//g' )

		rm -f loops.csv

		if [[ "$header" != "" && "$content" != "" ]]
		then
			if [[ "$mega_header" == "" ]]
			then
				mega_header="$header"
				mega_content="$content"
			else
				mega_header="$mega_header;$header"
				mega_content="$mega_content;$content"
			fi
		fi

		echo
	done
done

echo "$mega_header"
echo "$mega_content"
