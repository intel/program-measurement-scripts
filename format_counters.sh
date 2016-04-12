#!/bin/bash -l

# Assume const.sh under same directory as this script
source $(dirname $0)/const.sh

if [[ "$nb_args" != "8" ]]
then
	echo "ERROR! Invalid arguments (need: codelet's name, data size, memory load, frequency, variant, iterations, emon counters,res path)."
	exit -1
fi

set -x
codelet_name="$1"
data_size=$2
memory_load=$3
frequency=$4
variant="$5"
iterations="$6"
emon_counters=$7
res_path=$8
set +x


if [[ "$ENABLE_SEP" == "1" ]]; then
	./parse_sep_output.sh $res_path
fi

rm -f $res_path/likwid_report $res_path/likwid_counter_*

counters=$( echo "$emon_counters" | tr "," " " | tr "." "_" | tr " " "\n" | sort --uniq | tr "\n" " " )
sed 's/\./_/g' -i $res_path/emon_report
sed 's/,//g'  $res_path/emon_report > $res_path/emon_report.trim

	for counter in $counters
	do
		if [[ ( "$HOSTNAME" == "fxhaswell" ) && ( "$counter" == "UNC_CBO_CACHE_LOOKUP_ANY_I" || "$counter" == "UNC_CBO_CACHE_LOOKUP_ANY_MESI" ||  "$counter" == "UNC_CBO_EGRESS_ALLOCATION_AD_CORE" ||  "$counter" == "UNC_CBO_EGRESS_ALLOCATION_BL_CACHE" ||  "$counter" == "UNC_CBO_EGRESS_OCCUPANCY_AD_CORE" ||  "$counter" == "UNC_CBO_EGRESS_OCCUPANCY_BL_CACHE" ||  "$counter" == "UNC_CBO_INGRESS_ALLOCATION_IRQ" ||  "$counter" == "UNC_CBO_INGRESS_OCCUPANACY_IRQ" ||  "$counter" == "UNC_CBO_TOR_ALLOCATION_DRD" ||  "$counter" == "UNC_CBO_TOR_OCCUPANCY_DRD_VALID" ) ]]
		then
			echo "Special treatment for server uncore '$counter'"
			values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f3-6 -d${DELIM} | sed 's/ //g' )
			#echo "debug values: '$values'"
			for value in $values
			do
				val1=$( echo "$value" | cut -f1 -d${DELIM} )
				val2=$( echo "$value" | cut -f2 -d${DELIM} )
				val3=$( echo "$value" | cut -f3 -d${DELIM} )
				val4=$( echo "$value" | cut -f4 -d${DELIM} )
				echo "${counter}_0||$val1" >> $res_path/likwid_report
				echo "${counter}_1||$val2" >> $res_path/likwid_report
				echo "${counter}_2||$val3" >> $res_path/likwid_report
				echo "${counter}_3||$val4" >> $res_path/likwid_report
			done
			continue
		fi

		if [[ "$counter" == "UNC_L4_REQUEST_RD_HIT" || "$counter" == "UNC_L4_REQUEST_WR_HIT" || "$counter" == "UNC_L4_REQUEST_WR_FILL" || "$counter" == "UNC_L4_REQUEST_RD_EVICT_LINE_TO_DRAM" || "$counter" == "UNC_CBO_L4_SUPERLINE_ALLOC_FAIL" ]]
		then
			echo "Special treatment for server uncore '$counter'"
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
			continue
		fi
		if [[ ( "$HOSTNAME" == "fxilab147" ) && ( "$counter" == "FREERUN_PKG_ENERGY_STATUS" || "$counter" == "FREERUN_CORE_ENERGY_STATUS" ||  "$counter" == "FREERUN_DRAM_ENERGY_STATUS" ) ]]
		then
			echo "Special treatment for in-CPU energy '$counter'"
			values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f3,4 -d${DELIM} | sed 's/ //g' )
			for value in $values
			do
				val=$( echo "$value" | cut -f1 -d${DELIM} )
				echo "$counter||$val" >> $res_path/likwid_report
			done
			continue
		fi
		if [[ ( "$HOSTNAME" == "fxilab147" ) && ( "$counter" == "UNC_M_CAS_COUNT_RD" || "$counter" == "UNC_M_CAS_COUNT_WR" ) ]]
		then
			echo "Special treatment (recent emon) for uncore '$counter'"
			values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f3-10 -d${DELIM} | sed 's/ //g' )
			#echo "debug values: '$values'"
			for value in $values
			do
				val1=$( echo "$value" | cut -f1 -d${DELIM} )
				val2=$( echo "$value" | cut -f2 -d${DELIM} )
				val3=$( echo "$value" | cut -f3 -d${DELIM} )
				val4=$( echo "$value" | cut -f4 -d${DELIM} )
				val5=$( echo "$value" | cut -f5 -d${DELIM} )
				val6=$( echo "$value" | cut -f6 -d${DELIM} )
				val7=$( echo "$value" | cut -f7 -d${DELIM} )
				val8=$( echo "$value" | cut -f8 -d${DELIM} )
				let "val = $val1 + $val2 + $val3 + $val4 + $val5 + $val6 + $val7 + $val8"
				echo "$counter||$val" >> $res_path/likwid_report
			done
			continue
		fi
		if [[ ( "$HOSTNAME" == "fxilab148" ) && ( "$counter" == "UNC_M_CAS_COUNT_RD" || "$counter" == "UNC_M_CAS_COUNT_WR" ) ]]
		then
				echo "Special treatment (recent emon) for uncore '$counter'"
				values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f11-18 -d${DELIM} | sed 's/ //g' )
				#echo "debug values: '$values'"
				for value in $values
				do
					val1=$( echo "$value" | cut -f1 -d${DELIM} )
					val2=$( echo "$value" | cut -f2 -d${DELIM} )
					val3=$( echo "$value" | cut -f3 -d${DELIM} )
					val4=$( echo "$value" | cut -f4 -d${DELIM} )
					val5=$( echo "$value" | cut -f5 -d${DELIM} )
					val6=$( echo "$value" | cut -f6 -d${DELIM} )
					val7=$( echo "$value" | cut -f7 -d${DELIM} )
					val8=$( echo "$value" | cut -f8 -d${DELIM} )
					let "val = $val1 + $val2 + $val3 + $val4 + $val5 + $val6 + $val7 + $val8"
					echo "$counter||$val" >> $res_path/likwid_report
				done
				continue
		fi
		if [[ "$counter" == "UNC_IMC_DRAM_DATA_READS" || "$counter" == "UNC_IMC_DRAM_DATA_WRITES" || "$counter" == "UNC_PP0_ENERGY_STATUS" || "$counter" == "UNC_PKG_ENERGY_STATUS" ]]
		then
			echo "Special treatment (uncore counter) for uncore '$counter'"
			values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f3 -d${DELIM} | sed 's/ //g' )
			for value in $values
			do
				echo "$counter||$value" >> $res_path/likwid_report
			done
		else
			if [[ ( "$HOSTNAME" == "fxe32lin04" || "$HOSTNAME" == "fxtcarilab027" ) && ( "$counter" == "UNC_M_CAS_COUNT_RD" || "$counter" == "UNC_M_CAS_COUNT_WR" ) ]]
			then
				echo "Special treatment (recent emon) for uncore '$counter'"
				values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f7-10 -d${DELIM} | sed 's/ //g' )
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
			else
				if [[ "$counter" == "UNC_M_CAS_COUNT_RD" || "$counter" == "UNC_M_CAS_COUNT_WR" ]]
				then
					echo "Special treatment for server uncore '$counter'"
					values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f3,7 -d${DELIM} | sed 's/ //g' )
					#echo "debug values: '$values'"
					for value in $values
					do
						val1=$( echo "$value" | cut -f1 -d${DELIM} )
						val2=$( echo "$value" | cut -f2 -d${DELIM} )
						let "val = $val1 + $val2"
						echo "$counter||$val" >> $res_path/likwid_report
					done
				else
					if [[ "$counter" == "FREERUN_PKG_ENERGY_STATUS" || "$counter" == "FREERUN_CORE_ENERGY_STATUS" ]]
					then
						echo "Special treatment for in-CPU energy '$counter'"
						values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f3,4 -d${DELIM} | sed 's/ //g' )
						for value in $values
						do
							val1=$( echo "$value" | cut -f1 -d${DELIM} )
							val2=$( echo "$value" | cut -f2 -d${DELIM} )
							let "val = $val1 + $val2"
							echo "$counter||$val" >> $res_path/likwid_report
						done
					else
							echo "Regular treatment for '$counter'"
							let "target_field = $XP_CORE + 3"
							values=$( grep "$counter" $res_path/emon_report.trim | sed 's/\t/'${DELIM}'/g' | grep "$counter"${DELIM} | cut -f$target_field -d${DELIM} | sed 's/ //g' )
							#echo "debug values: '$values'"
							for value in $values
							do
								echo "$counter||$value" >> $res_path/likwid_report
							done
					fi
				fi
			fi
		fi
	done


	echo "$codelet_name"${DELIM}"$data_size"${DELIM}"$memory_load"${DELIM}"$frequency"${DELIM}"$variant"${DELIM} > $res_path/counters.csv
	if [[ "$HOSTNAME" == "fxhaswell" ]]
	then
		counters=$(echo $counters | sed 's:\(UNC_CBO_CACHE_LOOKUP_ANY_I\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_CACHE_LOOKUP_ANY_MESI\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_EGRESS_ALLOCATION_AD_CORE\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_EGRESS_ALLOCATION_BL_CACHE\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_EGRESS_OCCUPANCY_AD_CORE\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_EGRESS_OCCUPANCY_BL_CACHE\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_INGRESS_ALLOCATION_IRQ\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_INGRESS_OCCUPANACY_IRQ\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_TOR_ALLOCATION_DRD\):\1_0 \1_1 \1_2 \1_3:;s:\(UNC_CBO_TOR_OCCUPANCY_DRD_VALID\):\1_0 \1_1 \1_2 \1_3:')
	fi

	cp $res_path/cpi.csv $res_path/counters.csv
	for counter in $counters
	do
		##echo "Processing counter '$counter'"
		##echo "Debug: $( grep "$counter \|$counter|" $res_path/likwid_report | sed "s/ //g" | cut -f3 -d'|' )"
		#grep "$counter \|$counter|" $res_path/likwid_report | sed "s/ //g" | cut -f3 -d'|' | awk '{average += ($1 /'$iterations'); } END {print average / NR;}' > $res_path/likwid_counter_$counter

        let "mean_line = ($META_REPETITIONS / 2) + 1"
        res=$( grep "$counter \|$counter|" $res_path/likwid_report | sed "s/ //g" | cut -f3 -d'|' | sort -n )
        median=$( echo $res | tr ' ' '\n' | awk "NR==$mean_line" )
        echo $median | awk '{print $1 / '$iterations';}' > $res_path/likwid_counter_$counter

		paste -d${DELIM} $res_path/counters.csv $res_path/likwid_counter_$counter > $res_path/tmp
		mv $res_path/tmp $res_path/counters.csv
	done
