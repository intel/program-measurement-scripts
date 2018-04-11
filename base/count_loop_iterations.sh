#!/bin/bash 

source $CLS_FOLDER/const.sh


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

#Ensure basic probe is used
LD_LIBRARY_PATH=${BASE_PROBE_FOLDER}:${LD_LIBRARY_PATH}

if [[ "$USE_OLD_DECAN" == "0" ]]
then
# Filling new MAQAO implementation
# Get a list of loop id for the codelet
    loop_ids=$( $MAQAO analyze  -ll   $binary_path  fct=$function_name loop=innermost|sed '/ '${function_name}'/,/^ [^ ]/!d;//d' | grep -v -- "----" | sed 's/.*| \([^ ]*\) .*/\1/' )
    echo CMD loop_ids="\$( $MAQAO analyze  -ll   $binary_path  fct=$function_name |sed '/ '${function_name}'/,/^ [^ ]/!d;//d' | grep -v -- \"----\" | sed 's/.*| \([^ ]*\) .*/\1/' )" 1>&2
#    echo ${loop_ids[*]}
else
    $DECAN_CONFIGURATOR "$DECAN_FOLDER/" "$binary_path" "$function_name" "splitncount" "$UARCH" &>/dev/null
    $DECAN "$DECAN_CONFIGURATION" &>/dev/null

    echo HERE > /tmp/count.out.txt
    echo $DECAN "$DECAN_CONFIGURATION" >> /tmp/count.out.txt
    echo ${LD_LIBRARY_PATH} >> /tmp/count.out.txt
    cat $PWD/$DECAN_REPORT >> /tmp/count.out.txt
    decan_variants=$( grep generated $PWD/$DECAN_REPORT | cut -f2 -d' ' )
    # Here decan_variants are the variants to count loop iterations , not DECAN varaint for CLS runs
    # Also the loop ids are encoded to the decan variant names
    if [[ "$decan_variants" == "" ]]
	then
	echo "ERROR! No loop could be identified!" 1>&2
	exit -1
    fi
    rm -f $PWD/$DECAN_REPORT
    echo DONE >> /tmp/count.out.txt
    # Not really used
    loop_ids=$( echo "$decan_variants" | sed -e "s/.*_L\([[:digit:]]*\).*/\1/g" )
    
#echo "$decan_variants" &>blabla
#for loop_id in $loop_ids
#do
#	echo "Found loop '$loop_id'" &> /tmp/blabli
#done

fi
# Get the count for each loop id



if [[ "$USE_OLD_DECAN" == "0" ]]
then
    for loop_id in $loop_ids
      do
#      $MAQAO vprof lid=$loop_id -- $binary_path  >/tmp/out.$loop_id
#      count_values[$loop_id]=$( grep Total /tmp/out.$loop_id |cut -f3 -d'|' |tr -d [:blank:] )
      count_values[$loop_id]=$( $MAQAO vprof lid=$loop_id i=iterations -- $binary_path  |grep Total|cut -f3 -d'|' |tr -d [:blank:] )
      echo count_values[$loop_id]="\$( $MAQAO vprof lid=$loop_id -- $binary_path  |grep Total|cut -f3 -d'|' |tr -d [:blank:] )" 1>&2
      echo "COUNT: " ${count_values[$loop_id]} 1>&2
      done
else
    for decan_variant in $decan_variants
      do
	#"./$decan_variant"
      "./$decan_variant" &> "$decan_variant.dprof"
      count_values[$decan_variant]=$( cat "$decan_variant.dprof" | grep TOTAL_LOOP_CALLS -A 1 | sed -n "2p" | cut -f 2 -d ',' )
      cat "$decan_variant.dprof" 1>&2
      echo "COUNT: " ${count_values[$decan_variant]} 1>&2
      rm -f "$decan_variant" "$decan_variant.dprof"
    done
fi

# Got all counts saved in ${count_values[*]}

cd $CLS_FOLDER


final_res=""

if [[ "$USE_OLD_DECAN" == "0" ]]
then
    for loop_id in $loop_ids
      do
      tmp_iter=$( echo "${count_values[$loop_id]}" )
      if [[ "$tmp_iter" != "" ]]
	  then
	  final_res=$( echo -e "$loop_id"${DELIM}"$tmp_iter"${DELIM}"\n$final_res" )
      fi
    done
else
    for decan_variant in $decan_variants
      do
      tmp_iter=$( echo "${count_values[$decan_variant]}" )
      if [[ "$tmp_iter" != "" ]]
	  then
	  loop_id=$( echo "$decan_variant" | sed -e "s/.*_L\([[:digit:]]*\).*/\1/g" )
	  final_res=$( echo -e "$loop_id"${DELIM}"$tmp_iter"${DELIM}"\n$final_res" )
      fi
    done
fi

echo "$final_res" | sort -k2nr,2nr -t ${DELIM}


exit 0
