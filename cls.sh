#!/bin/bash -l

source ./const.sh
source /opt/intel/sep/sep_vars.sh

if [[ "$nb_args" != "6" ]]
then
	echo "ERROR! Invalid arguments (need: codelet's folder, variants, data sizes, memory loads, frequencies, run id)."
	exit -1
fi

codelet_folder=$( readlink -f "$1" )
variants="$2"
data_sizes="$3"
memory_loads="$4"
frequencies="$5"
runid="$6"

set_prefetcher_bits() {
    bits="$1"
    hex_prefetcher_bits=$(printf "0x%x" ${bits})
    echo "Writing ${hex_prefetcher_bits} to MSR 0x1a4 to change prefetcher settings."
    emon --write-msr 0x1a4=${hex_prefetcher_bits}
}

find_num_repetitions_and_iterations () {
    codelet_folder="$1"
    codelet_name="$2"
    data_size="$3"
    variant="$4"
    function_name="$5"
    loop_id="$6"
    repetitions_history_file="$7"
    iteration_file="$8"
    iterations_for_file="$9"

    echo "Adjusting codelet parametres for the $variant variant ..."
    if [[ "${variant}" == "ORG" ]]; then
	env -i ./w_adjust.sh "$codelet_folder" "${codelet_name}" "$data_size" $MIN_REPETITIONS $CODELET_LENGTH
    else
	env -i ./w_adjust.sh "$codelet_folder" "${codelet_name}_${variant}_hwc" "$data_size" $MIN_REPETITIONS $CODELET_LENGTH
    fi
    tail -n 1 "$codelet_folder/repetitions_history" >> "${repetitions_history_file}"
    sed -i '$ d' "$codelet_folder/repetitions_history" 

    repetitions=$(cat "${repetitions_history_file}" | grep "^$data_size" | tail -n 1 | cut -d' ' -f2)
    echo "$repetitions $data_size" > "$codelet_folder/codelet.data"
    
    echo "Re-counting loop iterations for ($codelet_folder/$codelet_name", "$function_name)..."
    loop_info=$( env -i ./count_loop_iterations.sh "$codelet_folder/$codelet_name" "$function_name"  | grep ${DELIM})
    res=$?
    if [[ "$res" != "0" ]]
	then
	echo "Cancelling CLS."
	exit -1
    fi
    
    wanted_loop_info=$( echo "$loop_info" | grep "^$loop_id${DELIM}" )
    most_important_loop=$( echo "$loop_info" | grep ${DELIM} | head -n 1)
    
    if [[ "$wanted_loop_info" != "$most_important_loop" ]]
	then
	echo "Loop mismatch!"
	tmp_id=$( echo "$wanted_loop_info" | cut -f1 -d${DELIM} )
	tmp_loop_iterations=$( echo "$wanted_loop_info" | cut -f2 -d${DELIM} )
	echo "Wanted loop info: $tmp_id, $tmp_loop_iterations iterations."
	
	tmp_id=$( echo "$most_important_loop" | cut -f1 -d${DELIM} )
	tmp_loop_iterations=$( echo "$most_important_loop" | cut -f2 -d${DELIM} )
	echo "Most important loop info: $tmp_id, $tmp_loop_iterations iterations."
	
	echo "Cancelling CLS."
	exit -1
    fi
    
    echo "$variant:Loop Id"${DELIM}"Iterations"${DELIM} >> "${iterations_for_file}"
    echo "$loop_info" | tr ' ' '\n' | sed "s/\(.*\)/$variant:\1/" >> "${iterations_for_file}"
    
    loop_iterations=$( echo "$wanted_loop_info" | cut -f2 -d${DELIM} )
    echo -e "Iterations \t'$loop_iterations'"
    echo "$variant"${DELIM}"${loop_iterations}" >> ${iteration_file}
}


START_CLS_SH=$(date '+%s')

echo "------------------------------------------------------------"
echo "CLS"
echo -e "Hostname \t'$HOSTNAME' [$UARCH]"
echo -e "Codelet \t'$codelet_folder'"
echo -e "Variants \t'$variants'"
echo -e "Data sizes \t'$data_sizes'"
echo -e "Memory loads \t'$memory_loads'"
echo -e "Frequencies \t'$frequencies'"
echo -e "Meta repets\t'$META_REPETITIONS'"

echo "------------------------------------------------------------"
echo "Reading codelet.conf"
codelet_name=$( grep "label name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
binary_name=$( grep "binary name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
function_name=$( grep "function name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
if [[ "$function_name" != "codelet_" ]]
then
	function_name="$function_name"_
fi
#function_name=$( grep "function name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
echo -e "Codelet name \t'$codelet_name'"
echo -e "Binary name \t'$binary_name'"
echo -e "Function name \t'$function_name'"

echo "------------------------------------------------------------"
echo "Removing older results (if any)..."
rm -R -f "$codelet_folder/$CLS_RES_FOLDER"
echo "Recreating results folder..."
mkdir "$codelet_folder/$CLS_RES_FOLDER" &> /dev/null
echo "$codelet_name" > "$codelet_folder/$CLS_RES_FOLDER/codelet_name"
echo "$META_REPETITIONS" > "$codelet_folder/$CLS_RES_FOLDER/meta_repetitions"
echo "$PRETTY_UARCH" > "$codelet_folder/$CLS_RES_FOLDER/uarch"

echo "------------------------------------------------------------"
echo "Compiling the codelet..."
./generate_original.sh $codelet_folder $binary_name $codelet_name
res=$?
if [[ "$res" != "0" ]]
then
	echo "Cancelling CLS."
	exit -1
fi

echo "------------------------------------------------------------"
echo "Identifying the main loop for ($codelet_folder/$codelet_name", "$function_name)..."
loop_info=$( env -i ./count_loop_iterations.sh "$codelet_folder/$codelet_name" "$function_name" )
res=$?
if [[ "$res" != "0" ]]
then
	echo "Cancelling CLS."
	exit -1
fi
loop_info=$( echo -e "$loop_info" | grep ${DELIM} | head -n 1 )
loop_id=$( echo "$loop_info" | cut -f1 -d${DELIM} )
loop_iterations=$( echo "$loop_info" | cut -f2 -d${DELIM} )
echo -e "Loop id \t'$loop_id'"
echo -e "Iterations \t'$loop_iterations'"
echo "$loop_id" > "$codelet_folder/$CLS_RES_FOLDER/loop_id"

echo "------------------------------------------------------------"
echo "Creating DECAN variants..."
./generate_variants.sh "$codelet_folder/$codelet_name" "$function_name" "$loop_id" "$variants"

res=$?
if [[ "$res" != "0" ]]
then
	echo "Cancelling CLS."
	exit -1
fi
if [[ "$ACTIVATE_DYNAMIC_GROUPING" != "0" ]]
then
	echo
	echo "Creating dynamic groups..."
	res_generate=$( ./generate_dynamic_groups.sh "$codelet_folder/$codelet_name" "$function_name" "$loop_id" )
	res=$?
	echo "$res_generate"
	if [[ "$res" != "0" ]]
	then
		echo "Cancelling CLS."
		exit -1
	fi
	add_variants=$( echo "$res_generate" | tail -n 1 | cut -f2 -d':' )
	variants="$variants $add_variants"
fi

echo "------------------------------------------------------------"
echo "Extracting assemblies..."
./assembly_extraction.sh "$codelet_name" "$variants" "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER" "$loop_id"
res=$?
if [[ "$res" != "0" ]]
then
	echo "Cancelling CLS."
	exit -1
fi

if [[ "$HOSTNAME" == "massenet" ]]
then
	echo "------------------------------------------------------------"
	echo "Activating recipe..."
	~/recipe.sh 1
fi

#exit 0

echo "------------------------------------------------------------"
echo "Starting experiments..."

#Saving old prefetcher settings
old_prefetcher_bits=($(emon --read-msr 0x1a4 | grep MSR | cut -f2 -d=|uniq ))

#Saving old uncore settings
old_uncore_bits=($(emon --read-msr 0x620 | grep MSR | cut -f2 -d=|uniq ))

if [[ "${#old_prefetcher_bits[@]}" -gt "1" ]]
then
# Different settings among processor - not supported.
	echo "Processors with different original prefetcher settings.  Cancelling CLS."
	exit -1
fi

# Change prefetcher settings
set_prefetcher_bits ${PREFETCHER_DISABLE_BITS}


for data_size in $data_sizes
do
	echo
	echo
	mkdir "$codelet_folder/$CLS_RES_FOLDER/data_$data_size" &> /dev/null

	echo "Setting highest CPU frequency to adjust codelet parametres..."
	./set_frequency.sh $XP_HIGH_FREQ 
	if [[ "$UARCH" == "HASWELL" ]]; then
		dec2hex=$(printf "%02x" $(echo $XP_HIGH_FREQ | sed 's:0::g'))
		emon --write-msr 0x620="0x${dec2hex}${dec2hex}"
	fi

	if [[ "${REPETITION_PER_DATASIZE}" != "0" ]]; then
	    for variant in $variants
	      do
	      
	      find_num_repetitions_and_iterations ${codelet_folder} ${codelet_name} ${data_size} ${variant} ${function_name} ${loop_id} "$codelet_folder/repetitions_history_${variant}"  "$codelet_folder/$CLS_RES_FOLDER/data_$data_size/${LOOP_ITERATION_COUNT_FILE}" "$codelet_folder/$CLS_RES_FOLDER/iterations_for_${data_size}"
	      
	    done
	fi
	
	for memory_load in $memory_loads
	do
		mkdir "$codelet_folder/$CLS_RES_FOLDER/data_$data_size/memload_$memory_load" &> /dev/null
		killall -9 memloader --quiet &> /dev/null
		if [[ "$memory_load" != "0" ]]
		then
			echo "Starting a memloader for '$memory_load' MB/s ($MEMLOAD_ARGS_LIST)"
			$MEMLOADER --target_bw=$memory_load $MEMLOAD_ARGS_LIST > "$codelet_folder/$CLS_RES_FOLDER/data_$data_size/memload_$memory_load/memloader.log" &
			memload_pid=$!
			sleep 5
			kill -0 $memload_pid &> /dev/null
			res=$?
			if [[ "$res" != "0" ]]
			then
				echo "Cancelling CLS."
				exit -1
			else
				disown $memload_pid
			fi
		else
			echo "No memory load."
		fi

		for frequency in $frequencies
		do
		  mkdir "$codelet_folder/$CLS_RES_FOLDER/data_$data_size/memload_$memory_load/freq_$frequency" &> /dev/null
		  if [[ "$UARCH" == "HASWELL" ]]; then
		      dec2hex=$(printf "%02x" $(echo $frequency | sed 's:0::g'))
		      emon --write-msr 0x620="0x${dec2hex}${dec2hex}"
		  fi
		  ./set_frequency.sh $frequency
		  res=$?
		  if [[ "$res" != "0" ]]
		      then
		      echo "Cancelling run_codelet.sh."
		      exit -1
		  fi
		  
		  for variant in $variants
		    do
		    res_path="$codelet_folder/$CLS_RES_FOLDER/data_$data_size/memload_$memory_load/freq_$frequency/variant_$variant"
		    mkdir ${res_path} &> /dev/null

		    if [[ "${REPETITION_PER_DATASIZE}" == "0" ]]; then
			find_num_repetitions_and_iterations ${codelet_folder} ${codelet_name} ${data_size} ${variant} ${function_name} ${loop_id} \
			    "${res_path}/repetitions_history_${variant}" \
			    "${res_path}/${LOOP_ITERATION_COUNT_FILE}" "${res_path}/iterations_for_${data_size}"
			repetitions=$(cat "${res_path}/repetitions_history_${variant}" | grep "^$data_size" | tail -n 1 | cut -d' ' -f2)
			loop_iterations=$(cat ${res_path}/${LOOP_ITERATION_COUNT_FILE} | grep $variant | cut -d${DELIM} -f2) 
		    else
			repetitions=$(cat "$codelet_folder/repetitions_history_${variant}" | grep "^$data_size" | tail -n 1 | cut -d' ' -f2)
			loop_iterations=$(cat $codelet_folder/$CLS_RES_FOLDER/data_$data_size/${LOOP_ITERATION_COUNT_FILE} | grep $variant | cut -d${DELIM} -f2) 
		    fi
		    
		    # Generate the codelet data file for measurment.  Need to compute iteration count.
		    echo "$repetitions $data_size" > "$codelet_folder/codelet.data"


		    ./run_codelet.sh "$codelet_folder" "$codelet_name" $data_size $memory_load $frequency "$variant" "$loop_iterations"
		    res=$?
		    if [[ "$res" != "0" ]]
			then
			echo "Cancelling CLS."
			exit -1
		    fi
		  done
		  
		done

		if [[ "$memory_load" != "0" ]]
		then
			killall -9 memloader --quiet &> /dev/null	
		else
			echo "No memory load (=> nothing to kill)."
		fi
	done



#	echo "Generating results..."


# 	./gather_results.sh "$codelet_folder" "$variants" "$data_sizes" "$memory_loads" "$frequencies" 
# 	res=$?
# 	if [[ "$res" != "0" ]]
# 	then
# 		echo "Cancelling CLS."
# 		exit -1
# 	fi
done

# Restore prefetcher settings.
echo "Writing ${old_prefetcher_bits} to MSR 0x1a4 to restore prefetcher settings."
#emon --write-msr 0x1a4=${old_prefetcher_bits}
set_prefetcher_bits ${old_prefetcher_bits}

if [[ "$UARCH" == "HASWELL" ]]; then
	emon --write-msr 0x620="$old_uncore_bits"
fi

echo "------------------------------------------------------------"
echo "Generating results using following inputs..."
echo -e "Codelet \t'$codelet_folder'"
echo -e "Variants \t'$variants'"
echo -e "Data sizes \t'$data_sizes'"
echo -e "Memory loads \t'$memory_loads'"
echo -e "Frequencies \t'$frequencies'"

END_CLS_SH=$(date '+%s')
new_cls_folder=${codelet_folder}/${CLS_RES_FOLDER}_${END_CLS_SH}_${runid}
# At the end, rename the result folder by appending timestamp
${LOGGER_SH} ${runid} "Renamed cls directory to ${new_cls_folder}"
mv "${codelet_folder}/${CLS_RES_FOLDER}"  "${new_cls_folder}"


./gather_results.sh ${new_cls_folder} "$variants" "$data_sizes" "$memory_loads" "$frequencies" 
res=$?
if [[ "$res" != "0" ]]
then
	echo "Cancelling CLS."
	exit -1
fi


ELAPSED_CLS_SH=$((${END_CLS_SH} - ${START_CLS_SH}))

${LOGGER_SH} ${runid} "cls.sh finished in $(${SEC_TO_DHMS_SH} ${ELAPSED_CLS_SH})."


echo "------------------------------------------------------------"
echo "Cleaning up..."
./cleanup_codelet_folder.sh "$codelet_folder" "$codelet_name" "$variants"
res=$?
if [[ "$res" != "0" ]]
then
	echo "Cancelling CLS."
	exit -1
fi


if [[ "$HOSTNAME" == "massenet" ]]
then
	echo "------------------------------------------------------------"
	echo "Deactivating recipe..."
	~/recipe.sh 0
fi

echo "------------------------------------------------------------"


exit 0
