#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "5" ]]
then
	echo "ERROR! Invalid arguments (need: codelet's folder, variants, data sizes, memory loads, frequencies)."
	exit -1
fi

codelet_folder=$( readlink -f "$1" )
variants="$2"
data_sizes="$3"
memory_loads="$4"
frequencies="$5"


res_folder="$codelet_folder/$CLS_RES_FOLDER"


echo "Gathering results for '$codelet_folder'"

if [[ "$ACTIVATE_COUNTERS" != "0" ]]
    then
    echo "Proceeding to formatting counter experiments."
    for data_size in $data_sizes
      do
      for memory_load in $memory_loads
	do
	for frequency in $frequencies
	  do
	  for variant in $variants
	    do
	    datasize_path="${res_folder}/data_$data_size"
	    res_path="${datasize_path}/memload_$memory_load/freq_$frequency/variant_$variant"
#	    res_path="$codelet_folder/$CLS_RES_FOLDER/data_$data_size/memload_$memory_load/freq_$frequency/variant_$variant"
	    emon_counters=$(cat "${res_path}/${EMON_COUNTER_NAMES_FILE}")
	    loop_iterations=$(cat "${datasize_path}/${LOOP_ITERATION_COUNT_FILE}" | grep $variant | cut -d';' -f2 )
		codelet_name=$(cat "${res_folder}/codelet_name")
	    ${FORMAT_COUNTERS_SH} "$codelet_name" $data_size $memory_load $frequency "$variant" "${loop_iterations}" "${emon_counters}" ${res_path}
	  done
	  
	done
      done
    done
fi




for freq in "$res_folder"/data_*/memload_*/freq_*
do
	freq=$( basename "$freq" )
	freq_list=$( echo -e "$freq\n$freq_list" )
done
freq_list=$( echo "$freq_list" | sort --uniq | tr "\n" " " | sed "s/freq_//g" )
#echo "Freq_list: '$freq_list'"

for memload in "$res_folder"/data_*/memload_*
do
	memload=$( basename "$memload" )
	memload_list=$( echo -e "$memload\n$memload_list" )
done
memload_list=$( echo "$memload_list" | sort --uniq | tr "\n" " " | sed "s/memload_//g" )
echo "Memload_list: '$memload_list'"


echo "Gathering CPIs..."
mkdir "$res_folder/$CPIS_FOLDER/" &> /dev/null
for memload in $memload_list
do
	for freq in $freq_list
	do
		output_cpi_file="$res_folder/$CPIS_FOLDER/cpi_${memload}MBs_${freq}kHz.csv"
		cat "$res_folder"/data_*"/memload_$memload/freq_$freq/"variant_*/cpi.csv	\
			| sort -k5r -t ';'							\
			| awk -F ";" '
				BEGIN {
				}
				{
					key = $1 ";" $2 ";" $3 ";" $4;
					values[key, $5] = $6;
					keys[key] = key;

					there = 0;
					for (ind in variants)
					{
						if (variants[ind] == $5)
						{
							there = 1;
						}
					}
					if (there != 1)
					{
						variants[counter++] = $5;
					}
					
					#variants[$5] = $5;

				}
				END {
					printf "Codelet" ";" "Data Size (N)" ";" "Memory Load (MB/s)" ";" "Frequency (kHz)" ";";
					for (variant = 0; variant < counter; variant++)
					{
						printf variants[variant] ";";
					}
					printf "\n";

					for (key in keys)
					{
						printf key ";";
						for (variant = 0; variant < counter; variant++)
						{
							printf values[key, variants[variant]] ";";
						}
						printf "\n";
					}
				}
				'								\
			| sort -k2n -t ';' > "$output_cpi_file"
			./draw_cpi.sh "$output_cpi_file" "CPI" "CPI"
	done
done


if [[ "$ACTIVATE_COUNTERS" != "0" ]]
then
	echo "Gathering counters..."
	mkdir "$res_folder/$COUNTERS_FOLDER/" &> /dev/null

	for variant in "$res_folder"/data_*/memload_*/freq_*/variant_*
	do
		some_variant_path="$variant"
		variant=$( basename "$variant" )
		variant_list=$( echo -e "$variant\n$variant_list" )
	done
	variant_list=$( echo "$variant_list" | sort --uniq | tr "\n" " " | sed "s/variant_//g" )
	#echo "Variant_list: '$variant_list'"


	for counter in "$some_variant_path"/likwid_counter_*
	do
		counter=$( basename "$counter" )
		counter_list=$( echo -e "$counter\n$counter_list" )
	done
	counter_list=$( echo "$counter_list" | sort --uniq | tr "\n" " " | sed "s/counter_//g" )
	#echo "Counter_list: '$counter_list'"

	for data_size in "$res_folder"/iterations_for_*
	do
		data_size=$( basename "$data_size" )
		data_size_list=$( echo -e "$data_size\n$data_size_list" )
	done
	data_size_list=$( echo "$data_size_list" | sort --uniq | sed "s/iterations_for_//g" | sort -k1n | tr "\n" " "  )
	#echo "Data size list: '$data_size_list'"


	for memload in $memload_list
	do
		for freq in $freq_list
		do
			for variant in $variant_list
			do
				res_file="$res_folder/$COUNTERS_FOLDER/counters_${variant}_${memload}MBs_${freq}kHz.csv"
				header="Codelet;Data Size (N);Memory Load (MB/s);Frequency (kHz);Variant;CPI"
				for counter in $counter_list
				do
					counter=$( echo "$counter" | sed "s/likwid_//g" )
					header="$header;$counter"
				done
				echo "$header" > "$res_file"
				cat "$res_folder"/data_*/memload_$memload/freq_$freq/variant_$variant/counters.csv | sort -k2n -t ';' >> $res_file

				for data_size in $data_size_list
				do
					echo "" >> $res_file
					echo "Data Size;$data_size;" >> $res_file
					cat "$res_folder/iterations_for_${data_size}" | grep "$variant" | cut -d':' -f2 >> $res_file
				done
				echo "" >> $res_file
				cat "$res_folder"/binaries/*_$variant.asm >> $res_file
				echo "" >> $res_file
				echo "" >> $res_file
#				cat "$res_folder"/binaries/*_$variant.stan.csv >> $res_file
#				echo "" >> $res_file
#				echo "" >> $res_file

				#./draw_counters.sh "$res_file" "Overview" "" "CPI CPU_CLK_UNHALTED_REF INSTR_RETIRED_ANY"
				#./draw_counters.sh "$res_file" "Memory" "" "L1D_REPLACEMENT L1D_WB_RQST_ALL L1D_WB_RQST_MISS SQ_MISC_FILL_DROPPED L2_LINES_IN_ALL L2_TRANS_L2_WB L3_LAT_CACHE_MISS"
				#./draw_counters.sh "$res_file" "Memory Hits" "" "MEMLOAD_UOPS_RETIRED_L1_HIT MEMLOAD_UOPS_RETIRED_L2_HIT MEMLOAD_UOPS_RETIRED_LLC_HIT MEMLOAD_UOPS_RETIRED_HIT_LFB MEMLOAD_UOPS_RETIRED_LLC_MISS"
			done
		done
	done
else
	echo "Skipping counters (not activated)."
fi

echo "Converting gathered data to Cape format..."
${FORMAT_2_CAPE_SH} ${res_folder} ${HOSTNAME}

exit 0
