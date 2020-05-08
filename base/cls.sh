#!/bin/bash
##!/bin/bash -l

source $CLS_FOLDER/const.sh

#if [ -f /opt/intel/sep/sep_vars.sh ]; then
#	source /opt/intel/sep/sep_vars.sh > /dev/null
#fi

if [[ "$nb_args" != "14" ]]; then
	echo "ERROR! Invalid arguments (need: codelet's folder, variants, data sizes, memory loads, unc_frequncies, frequencies, run id, start codelet loop run time, num codelet, current codelet run index, num cores, prefetchers, counter list override), current compiler."
	exit -1
fi

codelet_folder=$( readlink -f "$1" )
variants="$2"
data_sizes="$3"
memory_loads="$4"
unc_frequencies="$5"
frequencies="$6"
runid="$7"
start_codelet_loop_time="$8"
num_codelets="$9"
cnt_codelet_idx="${10}"
num_cores="${11}"
prefetchers="${12}"
counter_list_override="${13}"
curr_compiler="${14}"

# Assume to be successful in the beginning
loop_detection_success=1

find_num_repetitions_and_iterations () {
	local codelet_folder="$1"
	local codelet_name="$2"
	local data_size="$3"
	local variant="$4"
	function_name="$5"
	local loop_id="$6"
	local repetitions_history_file="$7"
	local iteration_file="$8"
	local iterations_for_file="$9"
	local num_core=${10}

	echo "history file" 1>&2
	echo ${repetitions_history_file} 1>&2
	echo "Adjusting codelet parameters for the $variant variant ...${codelet_folder}" 1>&2

	if [[ "${variant}" == "ORG" ]]; then
		#env -i ./w_adjust.sh "$codelet_folder" "${codelet_name}" "$data_size" $MIN_REPETITIONS $MAX_REPETITIONS $CODELET_LENGTH
		$CLS_FOLDER/w_adjust.sh "$codelet_folder" "${codelet_name}" "$data_size" $MIN_REPETITIONS $MAX_REPETITIONS $CODELET_LENGTH ${num_core} 1>&2
	else
		#echo env -i ./w_adjust.sh "$codelet_folder" "${codelet_name}_${variant}_hwc" "$data_size" $MIN_REPETITIONS $MAX_REPETITIONS $CODELET_LENGTH
		#env -i ./w_adjust.sh "$codelet_folder" "${codelet_name}_${variant}_hwc" "$data_size" $MIN_REPETITIONS $MAX_REPETITIONS $CODELET_LENGTH
		$CLS_FOLDER/w_adjust.sh "$codelet_folder" "${codelet_name}_${variant}_hwc" "$data_size" $MIN_REPETITIONS $MAX_REPETITIONS $CODELET_LENGTH ${num_core} 1>&2
	fi

	echo "history file" 1>&2
	echo ${repetitions_history_file} 1>&2

	tail -n 1 "$codelet_folder/repetitions_history" >> "${repetitions_history_file}"
	sed -i '$ d' "$codelet_folder/repetitions_history"

	repetitions=$(cat "${repetitions_history_file}" | grep "^$data_size" | tail -n 1 | cut -d' ' -f2)
	echo "Repetitions is " 1>&2
	echo $repetitions 1>&2
	echo "$repetitions $data_size" > "$codelet_folder/codelet.data"

	if [[ ${DISABLE_CQA} == 0 ]]; then
	    echo "Re-counting loop iterations for ($codelet_folder/$codelet_name", "$function_name, "${data_size}")..." 1>&2
	    #loop_info=$( env -i ./count_loop_iterations.sh "$codelet_folder/$codelet_name" "$function_name" "${data_size}" "${repetitions}" | grep ${DELIM})
	    echo CMD:     $CLS_FOLDER/count_loop_iterations.sh "$codelet_folder/$codelet_name" "$function_name" "${data_size}" "${repetitions}" "${num_core}" "|" grep ${DELIM} 1>&2
	    loop_info=$( $CLS_FOLDER/count_loop_iterations.sh "$codelet_folder/$codelet_name" "$function_name" "${data_size}" "${repetitions}" "${num_core}" | grep ${DELIM})
	    res=$?
	    
	    if [[ "$res" != "0" ]]; then
		if [[ "$IGNORE_LOOP_DETECTION_ERROR" == "0" ]]; then
		    echo "Cancelling CLS." 1>&2
		    exit -1
		else
		    loop_detection_success=0
		fi
	    fi
	    all_loop_info="$loop_info"
	    echo $loop_info > /tmp/loop_info.txt
	else
	    # Disabled CQA, just handle it like loop detection failed
	    echo "CQA disabled: No need to re-count loop iterations for ($codelet_folder/$codelet_name", "$function_name, "${data_size}")..." 1>&2
	    loop_detection_success=0
	fi

	if [[ "$loop_detection_success" == "1" ]]; then
		wanted_loop_info=$( echo "$loop_info" | grep "^$loop_id${DELIM}" )
		most_important_loop=$( echo "$loop_info" | grep ${DELIM} | head -n 1)

		# WARNING: note the loop_id was obtained from "first data size".  The following
		# check implies other data size will use the same main loop, which is not always the case and can fail.
		if [[ "$wanted_loop_info" != "$most_important_loop" ]]; then
			echo "Loop mismatch!"
			tmp_id=$( echo "$wanted_loop_info" | cut -f1 -d${DELIM} )
			tmp_loop_iterations=$( echo "$wanted_loop_info" | cut -f2 -d${DELIM} )
			echo "Wanted loop info: $tmp_id, $tmp_loop_iterations iterations." 1>&2

			tmp_id=$( echo "$most_important_loop" | cut -f1 -d${DELIM} )
			tmp_loop_iterations=$( echo "$most_important_loop" | cut -f2 -d${DELIM} )
			echo "Most important loop info: $tmp_id, $tmp_loop_iterations iterations." 1>&2

			if [[ "$IGNORE_LOOP_DETECTION_ERROR" == "0" ]]; then
				echo "Cancelling CLS." 1>&2
				exit -1
			else
				echo "LOOP MISMATCH ERROR IGNORED" 1>&2
				loop_detection_success=0
			fi
		fi
	fi

	# Check again because loop detection might have failed and should skip to setting loop id to -1, etc.
	if [[ "$loop_detection_success" == "1" ]]; then
		echo "$variant:Loop Id"${DELIM}"Iterations"${DELIM} >> "${iterations_for_file}"
		echo "$loop_info" | tr ' ' '\n' | sed "s/\(.*\)/$variant:\1/" >> "${iterations_for_file}"

		num_loop_exe=$( echo "$loop_info" | grep ${DELIM} | wc -l)
		#echo "num loop exe  is " ${num_loop_exe}
		#echo -e "LOOP INFO BEGIN\n${loop_info}\nLOOP INFO END"

		if [[ "${STRICT_SINGLE_LOOP}" != "0" ]]
		then
			if [[ "$num_loop_exe" != "1" ]]
			then
				echo "Multiple loops executed. Cancelling CLS." 1>&2
				exit -1
			else
				echo "Single loop executed. Acceptable for strict runs." 1>&2
			fi
		else
			if [[ "$num_loop_exe" != "1" ]]
			then
				echo "Multiple loops executed but proceed for non-strict runs" 1>&2
			else
				echo "Single loop executed." 1>&2
			fi
		fi
		# Old calculation based on wanted loop below (commented out)
		# loop_iterations=$( echo "$wanted_loop_info" | cut -f2 -d${DELIM} )
		all_loop_iterations=$( echo -e "$all_loop_info" | cut -f2 -d${DELIM} )
		loop_iterations=$( echo "$all_loop_iterations" |awk '{total+=$1}END{print total}' )
	else
		loop_info=""
		loop_id=-1
		echo "$variant:Loop Id"${DELIM}"Iterations"${DELIM} >> "${iterations_for_file}"
		echo "$variant:$loop_id"${DELIM}${repetitions}${DELIM} >> "${iterations_for_file}"
		loop_iterations=${repetitions}
	fi
	echo -e "Iterations \t'$loop_iterations'" 1>&2
	echo "$variant"${DELIM}"${loop_iterations}" >> ${iteration_file}
	echo "$all_loop_info"
}


START_CLS_SH=$(date '+%s')
${LOGGER_SH} ${runid} "cls.sh begins at $(date --date=@${START_CLS_SH})"

echo "-------------------------------------------------------------------------"

echo "CLS"
echo -e "Hostname \t'$HOSTNAME' [$UARCH]"
echo -e "Codelet \t'$codelet_folder'"
echo -e "Variants \t'$variants'"
echo -e "Data sizes \t'$data_sizes'"
echo -e "Memory loads \t'$memory_loads'"
echo -e "Number of cores \t'$num_cores'"
echo -e "Prefetchers \t'$prefetchers'"
echo -e "Frequencies \t'$frequencies'"
echo -e "Uncore Frequencies \t'$unc_frequencies'"
echo -e "Meta repets\t'$META_REPETITIONS'"

# Print out some version info
${MAQAO} -v
${DECAN} -v

################################################################################
# Conf file reading
################################################################################

echo "------------------------------------------------------------"
echo "Reading codelet.conf"
codelet_name=$( grep "label name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )

function_name=$( grep "function name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )
if [[ "$function_name" == "codelet" ]]; then
	function_name="$function_name"_
fi
#function_name=$( grep "function name" "$codelet_folder/codelet.conf" | sed -e 's/.*"\(.*\)".*/\1/g' )

echo -e "Codelet name \t'$codelet_name'"

echo -e "Function name \t'$function_name'"

################################################################################
# Directory creation
################################################################################

echo "------------------------------------------------------------"

echo "Removing older results (if any)..."
rm -R -f "$codelet_folder/$CLS_RES_FOLDER"
echo "Recreating results folder..."
mkdir "$codelet_folder/$CLS_RES_FOLDER" &> /dev/null
build_folder=$codelet_folder/$CLS_RES_FOLDER/build

# TO DELETE.  Handled in run_codelet.sh
# move created arguments csv to folder if it exists
#if [ -a "${codelet_folder}/arguments.csv" ]; then
#    mv "${codelet_folder}/arguments.csv" "$codelet_folder/$CLS_RES_FOLDER/"
#fi


echo "$codelet_name" > "$codelet_folder/$CLS_RES_FOLDER/codelet_name"
echo "$META_REPETITIONS" > "$codelet_folder/$CLS_RES_FOLDER/meta_repetitions"
echo "$PRETTY_UARCH" > "$codelet_folder/$CLS_RES_FOLDER/uarch"
echo MSR_POWER_UNIT is $MSR_POWER_UNIT
energy_unit_msr_value=$(emon --read-msr $MSR_POWER_UNIT|grep =|cut -f2 -d=|uniq|tr -d "\r")

if [[ $(echo "$energy_unit_msr_value" | wc -l) != "1" ]]; then
	echo "Unexpected corrupted MSR POWER UNIT counter, exiting"
	exit -1
else
	echo energy_unit_msr_value is \"$energy_unit_msr_value\"
	energy_units=$((( ($energy_unit_msr_value>>8)&0x1f )))
	energy_units=$(echo 0.5^$energy_units|bc -l)
	echo $energy_units > "$codelet_folder/$CLS_RES_FOLDER/energy_units"
fi

nominal_freq_kHz=$(printf "%.0f\n" $(echo $(emon -v |grep "TSC Freq.*MHz"|cut -f4 -d' ')*1000|bc -l))
echo $nominal_freq_kHz > "$codelet_folder/$CLS_RES_FOLDER/nominal_freq_kHz"


################################################################################
# Building of codelet
################################################################################

echo "------------------------------------------------------------"
echo "Compiling the codelet..."
echo $CLS_FOLDER/generate_original.sh $codelet_folder $codelet_name ${build_folder} ${curr_compiler}
$CLS_FOLDER/generate_original.sh $codelet_folder $codelet_name ${build_folder} ${curr_compiler}
res=$?
if [[ "$res" != "0" ]]; then
	echo "Cancelling CLS."
	exit -1
fi
echo "Contents of build folder:"
ls $build_folder

# codelet.o if exist will be stored under cls_res_folder
# program executable file is at ${build_folder}/${codelet_name}
codelet_exe=${build_folder}/${codelet_name}

first_data_size=$( echo ${data_sizes} | awk '{print $1;}' )

################################################################################
# Main loop identification (using count_loop_iterations.sh)
################################################################################

echo "------------------------------------------------------------"
echo "DISABLE CQA: ${DISABLE_CQA}"
if [[ ${DISABLE_CQA} == 0 ]]; then
    echo "Identifying the main loop for (${codelet_exe}", "$function_name, ${first_data_size})..."
    #echo "Identifying the main loop for ($codelet_folder/$codelet_name", "$function_name, ${first_data_size})..."
    #echo "Identifying the main loop for (${codelet_exe}", "$function_name, ${first_data_size})..."
    # Get the target loop with low repetition to save time.
    if [[ ${LOOP_ITER_COUNTER} == "SEP" ]]; then
	# Need bigger repetition for sep/sampling base counting
	try_repetitions=100
    else
	try_repetitions=2
    fi
    try_num_core=1
    echo CMD: $CLS_FOLDER/count_loop_iterations.sh "$codelet_exe" "$function_name" "${first_data_size}" ${try_repetitions} ${try_num_core}
    all_loop_info=$( $CLS_FOLDER/count_loop_iterations.sh "$codelet_exe" "$function_name" "${first_data_size}" ${try_repetitions} ${try_num_core} )
    res=$?
    
    if [[ "$res" != "0" || "X${all_loop_info}" == "X" ]]; then
	if [[ "$IGNORE_LOOP_DETECTION_ERROR" == "0" ]]; then
	    echo "Cancelling CLS."
	    exit -1
	else
	    loop_detection_success=0
	fi
    fi
    
    if [[ "$loop_detection_success" == "1" ]]; then
	#    echo env -i ./count_loop_iterations.sh "$codelet_exe" "$function_name" "${first_data_size}" ${try_repetitions}
	loop_info=$( echo -e "$all_loop_info" | grep ${DELIM} | head -n 1 )
	loop_id=$( echo "$loop_info" | cut -f1 -d${DELIM} )
	all_loop_ids=$( echo -e "$all_loop_info" | cut -f1 -d${DELIM} )
	all_loop_iterations=$( echo -e "$all_loop_info" | cut -f2 -d${DELIM} )
	#	loop_iterations=$( echo "$loop_info" | cut -f2 -d${DELIM} )
	loop_iterations=$( echo "$all_loop_iterations" |awk '{total+=$1}END{print total}' )
	if [[ "$loop_iterations" == "0" ]]; then
	    # Just make it a failed case
	    loop_detection_success=0
	fi
    fi
else
    # Disabled CQA, just handle it like loop detection failed
    loop_detection_success=0
fi

if [[ "$loop_detection_success" == "0" ]]; then
	echo "LOOP DETECTION ERROR IGNORED"
	loop_info=""
	loop_id=-1
	loop_iterations=${try_repetitions}
fi

echo -e "Loop id \t'$loop_id'"
echo -e "Iterations \t'$loop_iterations'"
echo "$loop_id" > "$codelet_folder/$CLS_RES_FOLDER/loop_id"

################################################################################
# Loop assembly extraction (using assembly_extraction.sh)
################################################################################

if [[ "$loop_detection_success" == "1" ]]; then
	echo "------------------------------------------------------------"
	echo "Creating DECAN variants..."
	#./generate_variants.sh "$codelet_folder/$codelet_name" "$function_name" "$loop_id" "$variants"
	#echo ./generate_variants.sh "$codelet_exe" "$function_name" "$loop_id" "$variants" "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"
	#$CLS_FOLDER/generate_variants.sh "$codelet_exe" "$function_name" "$loop_id" "$variants" "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"

	res=$?
	if [[ "$res" != "0" ]]; then
		echo "Cancelling CLS."
		exit -1
	fi

	if [[ "$ACTIVATE_DYNAMIC_GROUPING" != "0" ]]; then
		echo
		echo "Creating dynamic groups..."
		res_generate=$( $CLS_FOLDER/generate_dynamic_groups.sh "$codelet_folder/$codelet_name" "$function_name" "$loop_id" )
		res=$?
		echo "$res_generate"
		if [[ "$res" != "0" ]]; then
			echo "Cancelling CLS."
			exit -1
		fi
		add_variants=$( echo "$res_generate" | tail -n 1 | cut -f2 -d':' )
		variants="$variants $add_variants"
	fi

	echo "------------------------------------------------------------"
	echo "Extracting assemblies..."
	echo CMD : $CLS_FOLDER/assembly_extraction.sh \""$codelet_name"\" \""$variants"\" \""$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER"\" \
		\""$loop_id"\" \""$all_loop_ids"\" \""$all_loop_iterations"\"
	$CLS_FOLDER/assembly_extraction.sh "$codelet_name" "$variants" "$codelet_folder/$CLS_RES_FOLDER/$BINARIES_FOLDER" \
		"$loop_id" "$all_loop_ids" "$all_loop_iterations"
	res=$?
	if [[ "$res" != "0" ]]; then
		echo "Cancelling CLS."
		exit -1
	fi
fi

if [[ "$HOSTNAME" == "massenet" ]]; then
	echo "------------------------------------------------------------"
	echo "Activating recipe..."
	~/recipe.sh 1
fi

#exit 0

################################################################################
# Experiment running (uses run_codelet.sh)
################################################################################

if [[ ${ACTIVATE_EXPERIMENTS} != "0" ]]; then
	echo "------------------------------------------------------------"
	echo "Starting experiments..."

	old_settings=$(${CLS_FOLDER}/save_system_settings.sh)
	if [[ $? != "0" ]]; then
		echo "Failure saving system settings.  Cancelling CLS."
		exit -1
	fi

	# Change Huge page settings
	set_thp ${THP_SETTING}
	for prefetcher in $prefetchers; do
		# Change prefetcher settings
		#	set_prefetcher_bits ${PREFETCHER_DISABLE_BITS}
		set_prefetcher_bits ${prefetcher}
		prefetcher_path="$codelet_folder/$CLS_RES_FOLDER/prefetchers_$prefetcher"
		mkdir "$prefetcher_path" &> /dev/null
		# TODO: Currently vrun launcher passes data in 1 at a time but may change in future for folder reuse
		# anyways?
		for data_size in $data_sizes; do
			echo
			echo
			data_size_str=${data_size//[![:alnum:]]/-}
			data_path="$prefetcher_path/data_$data_size_str"
			mkdir "$data_path" &> /dev/null

			echo "Setting highest CPU frequency to adjust codelet parameters..."
			$CLS_FOLDER/set_frequency.sh -c $XP_HIGH_FREQ -m $XP_HIGH_FREQ -M $XP_HIGH_FREQ

			# if [[ "$UARCH" == "HASWELL" ]]; then
			# 	dec2hex=$(printf "%02x" $(echo $XP_HIGH_FREQ | sed 's:0::g'))
			# 	emon --write-msr 0x620="0x${dec2hex}${dec2hex}"
			# fi

			#	    if [[ "${REPETITION_PER_DATASIZE}" != "0" ]]; then
			#		for variant in $variants; do
			#		    #find_num_repetitions_and_iterations ${codelet_folder} ${codelet_name} ${data_size} ${variant} ${function_name} ${loop_id} "$codelet_folder/repetitions_history_${variant}"  "$codelet_folder/$CLS_RES_FOLDER/data_$data_size/${LOOP_ITERATION_COUNT_FILE}" "$codelet_folder/$CLS_RES_FOLDER/iterations_for_${data_size}"
			#		    find_num_repetitions_and_iterations ${build_folder} ${codelet_name} ${data_size} ${variant} ${function_name} ${loop_id} "$build_folder/repetitions_history_${variant}"  "${data_path}/${LOOP_ITERATION_COUNT_FILE}" "$codelet_folder/$CLS_RES_FOLDER/iterations_for_${data_size}"
			#		done
			#	    fi
			for memory_load in $memory_loads; do
				memory_load_path="${data_path}/memload_$memory_load"
				mkdir "$memory_load_path" &> /dev/null
				killall -9 memloader --quiet &> /dev/null
				if [[ "$memory_load" != "0" ]]; then
					echo "Starting a memloader for '$memory_load' MB/s ($MEMLOAD_ARGS_LIST)"
					$MEMLOADER --target_bw=$memory_load $MEMLOAD_ARGS_LIST > "$memory_load_path/memloader.log" &
					memload_pid=$!
					sleep 5
					kill -0 $memload_pid &> /dev/null
					res=$?

					if [[ "$res" != "0" ]]; then
						echo "Cancelling CLS."
						exit -1
					else
						disown $memload_pid
					fi
				else
					echo "No memory load."
				fi
				for unc_frequency in $unc_frequencies; do
					unc_frequency_path="$memory_load_path/uncfreq_$unc_frequency"
					mkdir "$unc_frequency_path" &> /dev/null
					for frequency in $frequencies; do
						frequency_path="$unc_frequency_path/freq_$frequency"
						mkdir "$frequency_path" &> /dev/null
						# if [[ "$UARCH" == "HASWELL" ]]; then
						#     dec2hex=$(printf "%02x" $(echo $frequency | sed 's:0::g'))
						#     emon --write-msr 0x620="0x${dec2hex}${dec2hex}"
						# fi
						$CLS_FOLDER/set_frequency.sh -c $frequency -m $unc_frequency -M $unc_frequency
						#                   $CLS_FOLDER/set_frequency.sh -c $frequency -m 100000 -M 100000
						#                   $CLS_FOLDER/set_frequency.sh -c $frequency -m 2100000 -M 2100000
						res=$?
						if [[ "$res" != "0" ]]; then
							echo "Cancelling run_codelet.sh."
							exit -1
						fi

						for variant in $variants; do
							variant_path="$frequency_path/variant_$variant"
							mkdir ${variant_path} &> /dev/null

							for num_core in $num_cores; do
								res_path="$variant_path/numcores_$num_core"
								mkdir ${res_path} &> /dev/null

								if [[ "${REPETITION_PER_DATASIZE}" == "0" ]]; then
									#find_num_repetitions_and_iterations ${codelet_folder} ${codelet_name} ${data_size} ${variant} ${function_name} ${loop_id} \
										#"${res_path}/repetitions_history_${variant}" \
										#"${res_path}/${LOOP_ITERATION_COUNT_FILE}" "${res_path}/iterations_for_${data_size}"
									all_loop_info=$(find_num_repetitions_and_iterations ${build_folder} ${codelet_name} \
										${data_size} ${variant} ${function_name} ${loop_id} \
										"${res_path}/repetitions_history_${variant}" \
										"${res_path}/${LOOP_ITERATION_COUNT_FILE}" "${res_path}/iterations_for_${data_size_str}" ${num_core})

									all_loop_ids=$( echo -e "$all_loop_info" | cut -f1 -d${DELIM}  | tr '\n' ';' | sed 's/;$//g')
									all_loop_iterations=$( echo -e "$all_loop_info" | cut -f2 -d${DELIM} | tr '\n' ';' | sed 's/;$//g')
									#									loop_iterations=$( echo "$all_loop_iterations" |awk '{total+=$1}END{print total}' )
									repetitions=$(cat "${res_path}/repetitions_history_${variant}" | grep "^$data_size" | tail -n 1 | cut -d' ' -f2)
									loop_iterations=$(cat ${res_path}/${LOOP_ITERATION_COUNT_FILE} | grep $variant | cut -d${DELIM} -f2)
								else
									echo "Not supported currently"
									exit -1
									#			repetitions=$(cat "$codelet_folder/repetitions_history_${variant}" | grep "^$data_size" | tail -n 1 | cut -d' ' -f2)
									repetitions=$(cat "$build_folder/repetitions_history_${variant}" | grep "^$data_size" | tail -n 1 | cut -d' ' -f2)
									loop_iterations=$(cat $codelet_folder/$CLS_RES_FOLDER/data_$data_size_str/${LOOP_ITERATION_COUNT_FILE} | grep $variant | cut -d${DELIM} -f2)
								fi

								# Generate the codelet data file for measurment.  Need to compute iteration count.
								#echo "$repetitions $data_size" > "$codelet_folder/codelet.data"
								echo "$repetitions $data_size" > "${build_folder}/codelet.data"
								pushd $build_folder
								# Run this at the build folder
								command_line_args=$(parameter_set_decoding "$build_folder/$codelet_name" "$data_size" "$repetitions" "$res_path" "$num_core" )
								popd

								#./run_coelet.sh "$codelet_folder" "$codelet_name" $data_size $memory_load $frequency "$variant" "$loop_iterations" "$repetitions"
								((cnt_codelet_idx++))
								echo Executing run_codelet.sh: $CLS_FOLDER/run_codelet.sh \"$build_folder\" \"$codelet_name\" \"$loop_iterations\" \"$repetitions\" "$all_loop_ids" "$all_loop_iterations" ${start_codelet_loop_time} ${num_codelets} ${cnt_codelet_idx} ${res_path} \"${counter_list_override}\" \"${command_line_args}\"
								$CLS_FOLDER/run_codelet.sh "$build_folder" "$codelet_name" "$loop_iterations" "$repetitions" "$all_loop_ids" "$all_loop_iterations" ${start_codelet_loop_time} ${num_codelets} ${cnt_codelet_idx} ${res_path} "${counter_list_override}" "${command_line_args}"

								res=$?
								if [[ "$res" != "0" ]]; then
									echo "Cancelling CLS."
									exit -1
								fi
							done # num cores for
						done # variants for
					done # frequencies for
				done # unc_frequencies for

				if [[ "$memory_load" != "0" ]]; then
					killall -9 memloader --quiet &> /dev/null
				else
					echo "No memory load (=> nothing to kill)."
				fi
			done # memory load for
		done # data size for
	done # prefretcher for

	${CLS_FOLDER}/restore_system_settings.sh ${old_settings}
fi

echo "------------------------------------------------------------"
echo "Generating results using following inputs..."
echo -e "Codelet \t'$codelet_folder'"
echo -e "Variants \t'$variants'"
echo -e "Data sizes \t'$data_sizes'"
echo -e "Memory loads \t'$memory_loads'"
echo -e "Number of cores \t'$num_cores'"
echo -e "Prefetchers \t'$prefetchers'"
echo -e "Frequencies \t'$frequencies'"
echo -e "Uncore Frequencies \t'$unc_frequencies'"

END_CLS_SH=$(date '+%s')
new_cls_folder=${codelet_folder}/${CLS_RES_FOLDER}_${END_CLS_SH}_${runid}
# At the end, rename the result folder by appending timestamp
${LOGGER_SH} ${runid} "Renamed cls directory to ${new_cls_folder}"
mv "${codelet_folder}/${CLS_RES_FOLDER}"  "${new_cls_folder}"
ln -s "${new_cls_folder}" ${RUN_FOLDER}/${runid}

shopt -s extglob
# copy the source and make file for record
cp ${codelet_folder}/codelet*.@(c|h|cpp|hpp|cc|f90|s) "${new_cls_folder}"
cp ${codelet_folder}/Makefile "${new_cls_folder}"

#echo ./gather_results.sh ${new_cls_folder} "$variants" "$data_sizes" "$memory_loads" "$frequencies" "$num_cores" "$prefetchers"
#./gather_results.sh ${new_cls_folder} "$variants" "$data_sizes" "$memory_loads" "$frequencies" "$num_cores" "$prefetchers"
echo $CLS_FOLDER/gather_results.sh ${new_cls_folder}
$CLS_FOLDER/gather_results.sh ${new_cls_folder}

res=$?
if [[ "$res" != "0" ]]
then
	echo "Cancelling CLS."
	exit -1
fi


ELAPSED_CLS_SH=$((${END_CLS_SH} - ${START_CLS_SH}))

${LOGGER_SH} ${runid} "cls.sh finished in $(${SEC_TO_DHMS_SH} ${ELAPSED_CLS_SH})."


# echo "------------------------------------------------------------"
# echo "Cleaning up..."
# ./cleanup_codelet_folder.sh "$codelet_folder" "$codelet_name" "$variants"
# res=$?
# if [[ "$res" != "0" ]]
# then
# 	echo "Cancelling CLS."
# 	exit -1
# fi


if [[ "$HOSTNAME" == "massenet" ]]; then
	echo "------------------------------------------------------------"
	echo "Deactivating recipe..."
	~/recipe.sh 0
fi

echo "------------------------------------------------------------"


exit 0
