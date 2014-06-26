#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "2" ]]
then
	echo "ERROR! Invalid arguments (need the binary's path and the function's name)."
	exit -1
fi


binary_path=$( readlink -f "$1" )
binary_folder=$( dirname "$binary_path" )
function_name="$2"


declare -A count_values


#echo "Generation of splitncount for '$binary_path' ('$function_name')"


cd $binary_folder
$DECAN_CONFIGURATOR "$DECAN_FOLDER/" "$binary_path" "$function_name" "splitncount" "$UARCH" &>/dev/null
$DECAN "$DECAN_CONFIGURATION" &>/dev/null


decan_variants=$( grep generated $PWD/$DECAN_REPORT | cut -f2 -d' ' )
if [[ "$decan_variants" == "" ]]
then
	echo "ERROR! No loop could be identified!" 1>&2
	exit -1
fi
rm -f $PWD/$DECAN_REPORT


loop_ids=$( echo "$decan_variants" | sed -e "s/.*_L\([[:digit:]]*\).*/\1/g" )


#echo "$decan_variants" &>blabla
#for loop_id in $loop_ids
#do
#	echo "Found loop '$loop_id'" &> blabli
#done


for decan_variant in $decan_variants
do
	#"./$decan_variant"
	"./$decan_variant" &> "$decan_variant.dprof"
	count_values[$decan_variant]=$( cat "$decan_variant.dprof" | grep TOTAL_LOOP_CALLS -A 1 | sed -n "2p" | cut -f 2 -d ',' )
#	cat "$decan_variant.dprof" 1>&2
#	echo "COUNT: " ${count_values[$decan_variant]} 1>&2
	rm -f "$decan_variant" "$decan_variant.dprof"
done

cd $CLS_FOLDER


final_res=""
for decan_variant in $decan_variants
do
	tmp_iter=$( echo "${count_values[$decan_variant]}" )
	if [[ "$tmp_iter" != "" ]]
	then
		loop_id=$( echo "$decan_variant" | sed -e "s/.*_L\([[:digit:]]*\).*/\1/g" )
		final_res=$( echo -e "$loop_id;$tmp_iter;\n$final_res" )
	fi
done

echo "$final_res" | sort -k2nr,2nr -t ";"


exit 0
