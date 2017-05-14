#!/bin/bash 

source ./const.sh


if [[ "$nb_args" != "4" ]]
then
	echo "ERROR! Invalid arguments (need the binary's path, the function's name, the data size and repetition)."
	exit -1
fi


set -x
binary_path=$( readlink -f "$1" )
binary_folder=$( dirname "$binary_path" )
function_name="$2"
data_size="$3"
repetition="$4"
set +x


declare -A count_values

#echo "Generation of splitncount for '$binary_path' ('$function_name')"


cd $binary_folder

# Create the datasize file for codelet run
echo "${repetition} ${data_size}" > ./codelet.data
$DECAN_CONFIGURATOR "$DECAN_FOLDER/" "$binary_path" "$function_name" "splitncount" "$UARCH" &>/dev/null
$DECAN "$DECAN_CONFIGURATION" &>/dev/null


echo HERE > /tmp/count.out.txt
echo ${LD_LIBRARY_PATH} >> /tmp/count.out.txt
cat $PWD/$DECAN_REPORT >> /tmp/count.out.txt
decan_variants=$( grep generated $PWD/$DECAN_REPORT | cut -f2 -d' ' )
if [[ "$decan_variants" == "" ]]
then
	echo "ERROR! No loop could be identified!" 1>&2
	exit -1
fi
rm -f $PWD/$DECAN_REPORT
echo DONE >> /tmp/count.out.txt

loop_ids=$( echo "$decan_variants" | sed -e "s/.*_L\([[:digit:]]*\).*/\1/g" )


#echo "$decan_variants" &>blabla
#for loop_id in $loop_ids
#do
#	echo "Found loop '$loop_id'" &> /tmp/blabli
#done

for decan_variant in $decan_variants
do
	#"./$decan_variant"
	"./$decan_variant" &> "$decan_variant.dprof"
	count_values[$decan_variant]=$( cat "$decan_variant.dprof" | grep TOTAL_LOOP_CALLS -A 1 | sed -n "2p" | cut -f 2 -d ',' )
	cat "$decan_variant.dprof" 1>&2
	echo "COUNT: " ${count_values[$decan_variant]} 1>&2
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
		final_res=$( echo -e "$loop_id"${DELIM}"$tmp_iter"${DELIM}"\n$final_res" )
	fi
done

echo "$final_res" | sort -k2nr,2nr -t ${DELIM}


exit 0
