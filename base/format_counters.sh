#!/bin/bash -l

# Assume const.sh under same directory as this script
source $(dirname $0)/const.sh

if [[ "$nb_args" != "8" ]]
then
	echo "ERROR! Invalid arguments (need: codelet's name, data size, memory load, frequency, variant, iterations, emon counters,res path)."
	exit -1
fi

#set -x
codelet_name="$1"
data_size=$2
memory_load=$3
frequency=$4
variant="$5"
iterations="$6"
emon_counters=$7
res_path=$8
set +x

verbose=0

fc_echo() {
	local msg="$1"

	if [[ "$verbose" == "1" ]]; then
		echo "$msg"
	fi

}

#source $(dirname $0)/pick_cores.sh $res_path
picked_cores=($($CLS_FOLDER/pick_cores.sh $res_path))
XP_CORE=${picked_cores[0]}

if [[ "$ENABLE_SEP" == "1" ]]; then
	./parse_sep_output.sh $res_path
fi

rm -f $res_path/likwid_report $res_path/likwid_counter_*

counters=$( echo "$emon_counters" | tr "," " " | tr "." "_" | tr " " "\n" | sort --uniq | tr "\n" " " )
sed 's/\./_/g' -i $res_path/emon_report
# Remove commas in EMON output as commas may be used as delimiters below.
sed 's/,//g'  $res_path/emon_report |tr -d '\r' > $res_path/emon_report.trim

tmp_file=$( mktemp )
counter_list=()
for counter in $counters
do
	counter_list+=( $counter )
	case "$counter" in
		"UNC_M_CAS_COUNT_RD" | "UNC_M_CAS_COUNT_WR" | "UNC_M_ACT_COUNT_RD" |"UNC_M_ACT_COUNT_WR" | "UNC_M_PRE_COUNT_PAGE_MISS" | "UNC_M_PRE_COUNT_WR" | "UNC_M_PRE_COUNT_RD" | "FREERUN_PKG_ENERGY_STATUS")
			fc_echo "Special treatment for server uncore '$counter'"
			# Add all columns
			values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f3- -d${DELIM} | sed 's/ //g' )
			#echo "debug values: '$values'"
			nc=$( grep number_of_processors $res_path/emon_info | awk '{print $3}' |tr -d '\r')
			c_per_pkg=$( grep "Cores Per Package:" $res_path/emon_info  | awk -F"[:|)]" '{print $2}' | tr -d '\r')
			let "npkg = $nc / $c_per_pkg"

			split_counters=""
			# Clear the file for split counter info
			> ${tmp_file}
			for value0 in $values
			do
				value=$( echo $value0 |sed 's/,$//g')
				((ndata=$( echo $value |tr -dc ','|wc -c )+1))
				let "ndata_per_pkg = ${ndata} / ${npkg}"
				echo ${value}|awk -v RS=${DELIM} -v counter=${counter} '{s+=$1}END{print counter"||"s}' >> $res_path/likwid_report
				# per socket counts, assuming numbers are contiguously put together for each socket
				# Uncomment below to print command
				# echo 'echo '$value' |awk -v RS='${DELIM}' -v BATCH='${ndata_per_pkg}' -v counter='${counter}" 'BEGIN{i=0}{s+=\$1} NR%BATCH==0 {print counter"'"_"i"||"'"s;s=0;i++}' >> "${tmp_file}
				# echo $value |awk -v RS=${DELIM} -v BATCH=${ndata_per_pkg} -v counter=${counter} 'BEGIN{i=0}{s+=$1} NR%BATCH==0 {print counter"_"i"||"s;s=0;i++}' >> ${tmp_file}
				# Simply just print the valule with its index
				echo $value |awk -v RS=${DELIM} -v counter=${counter} '{print counter"_"(NR-1)"||"$1}' >> ${tmp_file}
			done
			cat ${tmp_file} >> $res_path/likwid_report
			readarray -t split_counters < <(cut -f1 -d'|' ${tmp_file} |sort |uniq)
			counter_list+=(${split_counters[@]})
			;;

			#      "FREERUN_PKG_ENERGY_STATUS" | "FREERUN_CORE_ENERGY_STATUS" | "FREERUN_DRAM_ENERGY_STATUS" )
		"FREERUN_CORE_ENERGY_STATUS" | "FREERUN_DRAM_ENERGY_STATUS" )
			fc_echo "Special treatment for in-CPU energy '$counter'"
			values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f3,4 -d${DELIM} | sed 's/ //g' )
			for value in $values
			do
				let energy_col=${XP_NODES[${HOSTNAME}]}+1
				# Pick the energy corresponding to the node that runs the codelet
				val=$( echo "$value" | cut -f${energy_col} -d${DELIM} )
				echo "$counter||$val" >> $res_path/likwid_report
			done
			;;

		"UNC_L4_REQUEST_RD_HIT" | "UNC_L4_REQUEST_WR_HIT" | "UNC_L4_REQUEST_WR_FILL" | "UNC_L4_REQUEST_RD_EVICT_LINE_TO_DRAM" | "UNC_CBO_L4_SUPERLINE_ALLOC_FAIL")
			fc_echo "Special treatment for server uncore '$counter'"
			values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f3-6 -d${DELIM} | sed 's/ //g' )
			#echo "debug values: '$values'"
			for value in $values
			do
				val1=$( echo "$value" | cut -f1 -d${DELIM} )
				val2=$( echo "$value" | cut -f2 -d${DELIM} )
				val3=$( echo "$value" | cut -f3 -d${DELIM} )
				val4=$( echo "$value" | cut -f4 -d${DELIM} )
				let "val = $val1 + $val2 + $val3 + $val4"
				echo "$counter||$val" >> $res_path/likwid_report
			done
			;;

		"UNC_IMC_DRAM_DATA_READS" | "UNC_IMC_DRAM_DATA_WRITES" | "UNC_PP0_ENERGY_STATUS" | "UNC_PKG_ENERGY_STATUS")
			fc_echo "Special treatment (uncore counter) for uncore '$counter'"
			values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f3 -d${DELIM} | sed 's/ //g' )
			for value in $values
			do
				echo "$counter||$value" >> $res_path/likwid_report
			done
			;;

		"UNC_CBO_CACHE_LOOKUP_ANY_I" | "UNC_CBO_CACHE_LOOKUP_ANY_MESI" | "UNC_CBO_EGRESS_ALLOCATION_AD_CORE" | "UNC_CBO_EGRESS_ALLOCATION_BL_CACHE" |  "UNC_CBO_EGRESS_OCCUPANCY_AD_CORE" |  "UNC_CBO_EGRESS_OCCUPANCY_BL_CACHE" |  "UNC_CBO_INGRESS_ALLOCATION_IRQ" | "UNC_CBO_INGRESS_OCCUPANACY_IRQ" | "UNC_CBO_TOR_ALLOCATION_DRD" |  "UNC_CBO_TOR_OCCUPANCY_DRD_VALID")
			fc_echo "Special treatment for server uncore '$counter'"
			values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f3-6 -d${DELIM} | sed 's/ //g' )
			#echo "debug values: '$values'"
			> ${tmp_file}
			for value in $values
			do
				# 				val1=$( echo "$value" | cut -f1 -d${DELIM} )
				# 				val2=$( echo "$value" | cut -f2 -d${DELIM} )
				# 				val3=$( echo "$value" | cut -f3 -d${DELIM} )
				# 				val4=$( echo "$value" | cut -f4 -d${DELIM} )
				# 				echo "${counter}_0||$val1" >> $res_path/likwid_report
				# 				echo "${counter}_1||$val2" >> $res_path/likwid_report
				# 				echo "${counter}_2||$val3" >> $res_path/likwid_report
				# 				echo "${counter}_3||$val4" >> $res_path/likwid_report
				echo ${value}|awk -v RS=${DELIM} -v ctr=${counter} 'BEGIN{c=0}{print ctr"_"c"||"$1; c++}' >> ${tmp_file}
			done
			cat ${tmp_file} >> $res_path/likwid_report
			readarray -t split_counters < <(cut -f1 -d'|' ${tmp_file} |sort |uniq)
			counter_list+=(${split_counters[@]})
			;;


		*)
			fc_echo "Regular treatment for '$counter'"
			#      let "target_field = $XP_CORE + 3"
			target_field=$(echo ${picked_cores[@]} | awk  '{for (i=1;i<=NF;i++) print $i+3}' |tr '\n' ','|sed 's/,$//g')
			values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f$target_field -d${DELIM} | sed 's/ //g' |awk -F${DELIM} '{for(i=1;i<=NF;i++) sum+=$i; print sum; sum=0}' )
			for value in $values; do
				echo "$counter||$value" >> $res_path/likwid_report
			done
	esac
done

# Line below redundant?
#	echo "$codelet_name"${DELIM}"$data_size"${DELIM}"$memory_load"${DELIM}"$frequency"${DELIM}"$variant"${DELIM} > $res_path/counters.csv
# 	if [[ "$HOSTNAME" == "fxhaswell" ]]
# 	then
# 		counters=$(echo $counters | sed 's:\(UNC_CBO_CACHE_LOOKUP_ANY_I\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_CACHE_LOOKUP_ANY_MESI\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_EGRESS_ALLOCATION_AD_CORE\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_EGRESS_ALLOCATION_BL_CACHE\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_EGRESS_OCCUPANCY_AD_CORE\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_EGRESS_OCCUPANCY_BL_CACHE\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_INGRESS_ALLOCATION_IRQ\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_INGRESS_OCCUPANACY_IRQ\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_TOR_ALLOCATION_DRD\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_TOR_OCCUPANCY_DRD_VALID\):\1_0 \1_1 \1_2 \1_3:')
# 	fi


#	cp $res_path/cpi.csv $res_path/counters.csv
#	echo -n "CPI"${DELIM}>$res_path/counter_names.csv
echo $(IFS=${DELIM}; echo "${counter_list[*]}") > $res_path/counter_nv.csv

echo > $res_path/counter_values.csv
for counter in ${counter_list[@]}
do
	##echo "Processing counter '$counter'"
	##echo "Debug: $( grep "$counter \|$counter|" $res_path/likwid_report | sed "s/ //g" | cut -f3 -d'|' )"
	#grep "$counter \|$counter|" $res_path/likwid_report | sed "s/ //g" | cut -f3 -d'|' | awk '{average += ($1 /'$iterations'); } END {print average / NR;}' > $res_path/likwid_counter_$counter

	#        let "mean_line = ($META_REPETITIONS / 2) + 1"


	res=$( grep "$counter \|$counter|" $res_path/likwid_report | sed "s/ //g" | cut -f3 -d'|' | sort -n )
	if [ x"$res" != x ]; then
		# res not empty
		elements=$( echo $res | tr ' ' '\n' )
		numels=$( echo "$elements" |wc -l )
		let "mean_line = ($numels / 2) + 1"
		fc_echo "Selecting median data for  ${counter}  from  $numels  samples"
		#        median=$( echo $res | tr ' ' '\n' | awk "NR==$mean_line" )
		median=$( echo "$elements" | awk "NR==$mean_line" )
		echo $median | awk '{print $1 / '$iterations';}' > $res_path/likwid_counter_$counter
	else
		echo "" > $res_path/likwid_counter_$counter
	fi

	#		paste -d${DELIM} $res_path/counters.csv $res_path/likwid_counter_$counter > $res_path/tmp
	#		mv $res_path/tmp $res_path/counters.csv
	paste -d${DELIM} $res_path/counter_values.csv $res_path/likwid_counter_$counter > $res_path/tmp
	mv $res_path/tmp $res_path/counter_values.csv
done
# Remove the extra leading comma because counter_values.csv was empty in the beginning
sed 's/^,//g' $res_path/counter_values.csv >> $res_path/counter_nv.csv

rm ${tmp_file}
