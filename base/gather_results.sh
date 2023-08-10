#!/bin/bash

source $CLS_FOLDER/const.sh

if [[ "$nb_args" != "1" ]]
then
	echo "ERROR! Invalid arguments (need: res folder, variants, data sizes, memory loads, frequencies, num cores, prefetchers)."
	exit -1
fi

#codelet_folder=$( readlink -f "$1" )
res_folder=$( readlink -f "$1" )
#variants="$2"
#data_sizes="$3"
#memory_loads="$4"
#frequencies="$5"
#num_cores="$6"
#prefetchers="$7"


#res_folder="$codelet_folder/$CLS_RES_FOLDER"


#echo "Gathering results for '$codelet_folder'"
echo "Gathering results for '$res_folder'"
if [[ ${ACTIVATE_EXPERIMENTS} != "0" ]]
then

	if [[ "$ACTIVATE_COUNTERS" != "0" ]]
	then
		echo "Proceeding to formatting counter experiments."

		for path_to_emon_report in $(find $res_folder -name 'emon_report')
		do
			res_path=$(dirname $path_to_emon_report)

			run_info=${res_path#$res_folder}	# remove the prefix
			variant=$(echo $run_info|sed 's/.*\(variant_\)\([^/]\+\).*/\2/') # match after variant_
			if [[ "${REPETITION_PER_DATASIZE}" != "0" ]]; then
				datasize_path="${res_folder}/data_$data_size"
			else
				datasize_path=${res_path}
			fi
			emon_counters=$(cat "${res_path}/${EMON_COUNTER_NAMES_FILE}")
			loop_iterations=$(cat "${datasize_path}/${LOOP_ITERATION_COUNT_FILE}" | grep $variant | cut -d${DELIM} -f2 )
			#	codelet_name=$(cat "${res_folder}/codelet_name")
			echo Format counter cmd: ${FORMAT_COUNTERS_SH} \"\" \"\" \"\" \"\" \"\" "${loop_iterations}" "${emon_counters}" ${res_path}
			${FORMAT_COUNTERS_SH} "" "" "" "" "" "${loop_iterations}" "${emon_counters}" ${res_path}
		done

		# for data_size in $data_sizes
		#   do
		#   for memory_load in $memory_loads
		# 	do
		# 	for frequency in $frequencies
		# 	  do
		# 	  for variant in $variants
		# 	    do

		# 	      for num_core in $num_cores
		# 	      do

		# 		  #	    res_path="${res_folder}/data_$data_size/memload_$memory_load/freq_$frequency/variant_$variant"
		# 		  res_path="${res_folder}/data_$data_size/memload_$memory_load/freq_$frequency/variant_$variant/numcores_$num_core"
		# 		  #	    res_path="$codelet_folder/$CLS_RES_FOLDER/data_$data_size/memload_$memory_load/freq_$frequency/variant_$variant"

		# 		  if [[ "${REPETITION_PER_DATASIZE}" != "0" ]]; then
		# 		      datasize_path="${res_folder}/data_$data_size"
		# 		  else
		# 		      datasize_path=${res_path}
		# 		  fi
		# 		  emon_counters=$(cat "${res_path}/${EMON_COUNTER_NAMES_FILE}")
		# 		  loop_iterations=$(cat "${datasize_path}/${LOOP_ITERATION_COUNT_FILE}" | grep $variant | cut -d${DELIM} -f2 )
		# 		  codelet_name=$(cat "${res_folder}/codelet_name")
		# 		  echo ${FORMAT_COUNTERS_SH} "$codelet_name" $data_size $memory_load $frequency "$variant" "${loop_iterations}" "${emon_counters}" ${res_path}
		# 		  ${FORMAT_COUNTERS_SH} "$codelet_name" $data_size $memory_load $frequency "$variant" "${loop_iterations}" "${emon_counters}" ${res_path}
		# 	      done
		# 	  done
		# 	done
		#   done
		# done
	fi



	# for freq in "$res_folder"/data_*/memload_*/freq_*
	# do
	# 	freq=$( basename "$freq" )
	# 	freq_list=$( echo -e "$freq\n$freq_list" )
	# done
	# freq_list=$( echo "$freq_list" | sort --uniq | tr "\n" " " | sed "s/freq_//g" )
	# #echo "Freq_list: '$freq_list'"

	# for memload in "$res_folder"/data_*/memload_*
	# do
	# 	memload=$( basename "$memload" )
	# 	memload_list=$( echo -e "$memload\n$memload_list" )
	# done
	# memload_list=$( echo "$memload_list" | sort --uniq | tr "\n" " " | sed "s/memload_//g" )
	# echo "Memload_list: '$memload_list'"


	# echo "Gathering CPIs..."
	# mkdir "$res_folder/$CPIS_FOLDER/" &> /dev/null

	#NOTE: This is hardcoded following the order of cpi run (generating cpi.csv).  See run_codelet.sh for details.
	#cpi_header_minus_variant_cpi="Codelet"${DELIM}"Data Size (N)"${DELIM}"Memory Load (MB/s)"${DELIM}"Frequency (kHz)"${DELIM}"Num. Cores"${DELIM}"Iterations"${DELIM}"Repetitions"
	#cpi_header=${cpi_header_minus_variant_cpi}${DELIM}"Variant"${DELIM}"CPI"

	# for memload in $memload_list
	# do
	# 	for freq in $freq_list
	# 	do
	# 	  echo res_folder is $res_folder
	# 	  echo cpifolder is $CPIS_FOLDER
	# 		output_cpi_file="$res_folder/$CPIS_FOLDER/cpi_${memload}MBs_${freq}kHz.csv"
	# # NOTE The following awk command also hardcoded column order following cpi.csv generation in run_codelet.sh.
	# 		cat "$res_folder"/data_*"/memload_$memload/freq_$freq/"variant_*/numcores_*/cpi.csv	\
		# 			| sort -k5r -t ${DELIM}							\
		# 			| awk -F ${DELIM} '
	# 				BEGIN {
	# 				}
	# 				{
	# 					key = $1 "'${DELIM}'" $2 "'${DELIM}'" $3 "'${DELIM}'" $4 "'${DELIM}'" $5 "'${DELIM}'" $6 "'${DELIM}'" $7;
	# 					values[key, $8] = $9;
	# 					keys[key] = key;

	# 					there = 0;
	# 					for (ind in variants)
	# 					{
	# 						if (variants[ind] == $8)
	# 						{
	# 							there = 1;
	# 						}
	# 					}
	# 					if (there != 1)
	# 					{
	# 						variants[counter++] = $8;
	# 					}

	# 					#variants[$8] = $8;

	# 				}
	# 				END {
	# 					printf "'"${cpi_header_minus_variant_cpi}${DELIM}"'";
	# 					for (variant = 0; variant < counter; variant++)
	# 					{
	# 						printf variants[variant] "'${DELIM}'";
	# 					}
	# 					printf "\n";

	# 					for (key in keys)
	# 					{
	# 						printf key "'${DELIM}'";
	# 						for (variant = 0; variant < counter; variant++)
	# 						{
	# 							printf values[key, variants[variant]] "'${DELIM}'";
	# 						}
	# 						printf "\n";
	# 					}
	# 				}
	# 				'								\
		# 			| sort -k2n -t ${DELIM} > "$output_cpi_file"
	# #			./draw_cpi.sh "$output_cpi_file" "CPI" "CPI"
	# 	done
	# done

	# if [[ "$ACTIVATE_COUNTERS" != "0" ]]
	# then
	# 	echo "Gathering counters..."
	# 	mkdir "$res_folder/$COUNTERS_FOLDER/" &> /dev/null

	# 	for variant in "$res_folder"/data_*/memload_*/freq_*/variant_*
	# 	do
	# 		some_variant_path="$variant"
	# 		variant=$( basename "$variant" )
	# 		variant_list=$( echo -e "$variant\n$variant_list" )
	# 	done
	# 	variant_list=$( echo "$variant_list" | sort --uniq | tr "\n" " " | sed "s/variant_//g" )
	# 	#echo "Variant_list: '$variant_list'"
	# 	echo "Some variant path: ${some_variant_path}"
	# 	likwid_counters=$(ls "$some_variant_path"/numcores_*/likwid_counter_*|sort|uniq)
	# 	for counter in ${likwid_counters}
	# 	do
	# 		counter=$( basename "$counter" )
	# 		counter_list=$( echo -e "$counter\n$counter_list" )
	# 	done
	# 	counter_list=$( echo "$counter_list" | sort --uniq | tr "\n" " " | sed "s/counter_//g" )
	# 	echo "Counter_list: '$counter_list'"


	# #	for data_size in "$res_folder"/iterations_for_*
	# #       find command should work for both REPETITION_PER_DATASIZE or not
	# 	for data_size in $(find ${res_folder} -name 'iterations_for_*')
	# 	do
	# 		data_size=$( basename "$data_size" )
	# 		data_size_list=$( echo -e "$data_size\n$data_size_list" )
	# 	done
	# 	data_size_list=$( echo "$data_size_list" | sort --uniq | sed "s/iterations_for_//g" | sort -k1n | tr "\n" " "  )
	# 	#echo "Data size list: '$data_size_list'"


	# 	for memload in $memload_list
	# 	do
	# 		for freq in $freq_list
	# 		do
	# 			for variant in $variant_list
	# 			do
	# 			    for num_core in $num_cores
	# 			    do

	# 				res_file="$res_folder/$COUNTERS_FOLDER/counters_${variant}_${memload}MBs_${freq}kHz_${num_core}cores.csv"
	# 				# NOTE: The first few columns of counters.csv was copied from cpi.csv (See format_counters.sh for details).
	# 				header=${cpi_header}
	# 				for counter in $counter_list
	# 				do
	# 				    echo "COUNTER: $counter"
	# 					counter=$( echo "$counter" | sed "s/likwid_//g" )
	# 					header="$header"${DELIM}"$counter"
	# 				done
	# 				echo "$header" > "$res_file"
	# 				cat "$res_folder"/data_*/memload_$memload/freq_$freq/variant_$variant/numcores_${num_core}/counters.csv | sort -k2n -t ${DELIM} >> $res_file
	# 				for data_size in $data_size_list
	# 				do
	# 					echo "" >> $res_file
	# 					echo "Data Size"${DELIM}"$data_size"${DELIM} >> $res_file
	# 					if [[ "${REPETITION_PER_DATASIZE}" != "0" ]]; then
	# #					    cat "$res_folder/iterations_for_${data_size}" | grep "$variant" | cut -d':' -f2 >> $res_file
	# 					    res_path="$res_folder"
	# 					else
	# 					    res_path="$res_folder/data_$data_size/memload_$memory_load/freq_$frequency/variant_$variant/numcores_${num_core}"
	# 					fi
	# 					cat "${res_path}/iterations_for_${data_size}" | grep "$variant" | cut -d':' -f2 >> $res_file
	# 				done

	# 				echo "" >> $res_file
	# 				cat "$res_folder"/binaries/*_$variant.asm >> $res_file
	# 				echo "" >> $res_file
	# 				echo "" >> $res_file
	# #				cat "$res_folder"/binaries/*_$variant.stan.csv >> $res_file
	# #				echo "" >> $res_file
	# #				echo "" >> $res_file

	# 				#./draw_counters.sh "$res_file" "Overview" "" "CPI CPU_CLK_UNHALTED_REF INSTR_RETIRED_ANY"
	# 				#./draw_counters.sh "$res_file" "Memory" "" "L1D_REPLACEMENT L1D_WB_RQST_ALL L1D_WB_RQST_MISS SQ_MISC_FILL_DROPPED L2_LINES_IN_ALL L2_TRANS_L2_WB L3_LAT_CACHE_MISS"
	# 				#./draw_counters.sh "$res_file" "Memory Hits" "" "MEMLOAD_UOPS_RETIRED_L1_HIT MEMLOAD_UOPS_RETIRED_L2_HIT MEMLOAD_UOPS_RETIRED_LLC_HIT MEMLOAD_UOPS_RETIRED_HIT_LFB MEMLOAD_UOPS_RETIRED_LLC_MISS"
	# 			    done
	# 			done
	# 		done
	# 	done
	# else
	# 	echo "Skipping counters (not activated)."
	# fi
fi

echo "Converting gathered data to Cape format..."
#echo Format2Cape cmd ${FORMAT_2_CAPE_SH} ${res_folder} $(hostname) ${variants} "${num_cores}"
#${FORMAT_2_CAPE_SH} ${res_folder} $(hostname) ${variants} "${num_cores}"
echo Format2Cape cmd ${FORMAT_2_CAPE_SH} ${res_folder}
${FORMAT_2_CAPE_SH} ${res_folder}

exit 0
