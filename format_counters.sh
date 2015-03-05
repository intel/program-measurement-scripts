#!/bin/bash -l

# Assume const.sh under same directory as this script
source $(dirname $0)/const.sh

if [[ "$nb_args" != "8" ]]
then
	echo "ERROR! Invalid arguments (need: codelet's name, data size, memory load, frequency, variant, iterations, emon counters,res path)."
	exit -1
fi

codelet_name="$1"
data_size=$2
memory_load=$3
frequency=$4
variant="$5"
iterations="$6"
emon_counters=$7
res_path=$8


counters=$( echo "$emon_counters" | tr "," " " | tr "." "_" | tr " " "\n" | sort --uniq | tr "\n" " " )
sed 's/\./_/g' -i $res_path/emon_report

	for counter in $counters
	do
		if [[ "$counter" == "UNC_L4_REQUEST_RD_HIT" || "$counter" == "UNC_L4_REQUEST_WR_HIT" || "$counter" == "UNC_L4_REQUEST_WR_FILL" || "$counter" == "UNC_L4_REQUEST_RD_EVICT_LINE_TO_DRAM" || "$counter" == "UNC_CBO_L4_SUPERLINE_ALLOC_FAIL" ]]
		then
			echo "Special treatment for server uncore '$counter'"
			values=$( grep "$counter" $res_path/emon_report | sed 's/\t/;/g' | grep "$counter;" | cut -f3-6 -d';' | sed 's/ //g' )
			#echo "debug values: '$values'"
			for value in $values
			do
				val1=$( echo "$value" | cut -f1 -d';' )
				val2=$( echo "$value" | cut -f2 -d';' )
				val3=$( echo "$value" | cut -f3 -d';' )
				val4=$( echo "$value" | cut -f4 -d';' )
				let "val = $val1 + $val2 + $val3 + $val4"
				echo "$counter||$val" >> $res_path/likwid_report
			done
			continue
		fi
		if [[ ( "$HOSTNAME" == "fxilab147" ) && ( "$counter" == "UNC_M_CAS_COUNT_RD" || "$counter" == "UNC_M_CAS_COUNT_WR" ) ]]
		then
			echo "Special treatment (recent emon) for uncore '$counter'"
			values=$( grep "$counter" $res_path/emon_report | sed 's/\t/;/g' | grep "$counter;" | cut -f3-10 -d';' | sed 's/ //g' )
			#echo "debug values: '$values'"
			for value in $values
			do
				val1=$( echo "$value" | cut -f1 -d';' )
				val2=$( echo "$value" | cut -f2 -d';' )
				val3=$( echo "$value" | cut -f3 -d';' )
				val4=$( echo "$value" | cut -f4 -d';' )
				val5=$( echo "$value" | cut -f5 -d';' )
				val6=$( echo "$value" | cut -f6 -d';' )
				val7=$( echo "$value" | cut -f7 -d';' )
				val8=$( echo "$value" | cut -f8 -d';' )
				let "val = $val1 + $val2 + $val3 + $val4 + $val5 + $val6 + $val7 + $val8"
				echo "$counter||$val" >> $res_path/likwid_report
			done
			continue
		fi
		if [[ ( "$HOSTNAME" == "fxilab148" ) && ( "$counter" == "UNC_M_CAS_COUNT_RD" || "$counter" == "UNC_M_CAS_COUNT_WR" ) ]]
		then
				echo "Special treatment (recent emon) for uncore '$counter'"
				values=$( grep "$counter" $res_path/emon_report | sed 's/\t/;/g' | grep "$counter;" | cut -f11-18 -d';' | sed 's/ //g' )
				#echo "debug values: '$values'"
				for value in $values
				do
					val1=$( echo "$value" | cut -f1 -d';' )
					val2=$( echo "$value" | cut -f2 -d';' )
					val3=$( echo "$value" | cut -f3 -d';' )
					val4=$( echo "$value" | cut -f4 -d';' )
					val5=$( echo "$value" | cut -f5 -d';' )
					val6=$( echo "$value" | cut -f6 -d';' )
					val7=$( echo "$value" | cut -f7 -d';' )
					val8=$( echo "$value" | cut -f8 -d';' )
					let "val = $val1 + $val2 + $val3 + $val4 + $val5 + $val6 + $val7 + $val8"
					echo "$counter||$val" >> $res_path/likwid_report
				done
				continue
		fi
		if [[ "$counter" == "UNC_IMC_DRAM_DATA_READS" || "$counter" == "UNC_IMC_DRAM_DATA_WRITES" || "$counter" == "UNC_PP0_ENERGY_STATUS" || "$counter" == "UNC_PKG_ENERGY_STATUS" ]]
		then
			echo "Special treatment (uncore counter) for uncore '$counter'"
			values=$( grep "$counter" $res_path/emon_report | sed 's/\t/;/g' | grep "$counter;" | cut -f3 -d';' | sed 's/ //g' )
			echo "$counter||$values" >> $res_path/likwid_report
		else
			if [[ ( "$HOSTNAME" == "fxe32lin04" || "$HOSTNAME" == "fxtcarilab027" ) && ( "$counter" == "UNC_M_CAS_COUNT_RD" || "$counter" == "UNC_M_CAS_COUNT_WR" ) ]]
			then
				echo "Special treatment (recent emon) for uncore '$counter'"
				values=$( grep "$counter" $res_path/emon_report | sed 's/\t/;/g' | grep "$counter;" | cut -f7-10 -d';' | sed 's/ //g' )
				#echo "debug values: '$values'"
				for value in $values
				do
					val1=$( echo "$value" | cut -f1 -d';' )
					val2=$( echo "$value" | cut -f2 -d';' )
					val3=$( echo "$value" | cut -f3 -d';' )
					val4=$( echo "$value" | cut -f4 -d';' )
					let "val = $val1 + $val2 + $val3 + $val4"
					echo "$counter||$val" >> $res_path/likwid_report
				done
			else
				if [[ "$counter" == "UNC_M_CAS_COUNT_RD" || "$counter" == "UNC_M_CAS_COUNT_WR" ]]
				then
					echo "Special treatment for server uncore '$counter'"
					values=$( grep "$counter" $res_path/emon_report | sed 's/\t/;/g' | grep "$counter;" | cut -f3,7 -d';' | sed 's/ //g' )
					#echo "debug values: '$values'"
					for value in $values
					do
						val1=$( echo "$value" | cut -f1 -d';' )
						val2=$( echo "$value" | cut -f2 -d';' )
						let "val = $val1 + $val2"
						echo "$counter||$val" >> $res_path/likwid_report
					done
				else
					if [[ "$counter" == "FREERUN_PKG_ENERGY_STATUS" || "$counter" == "FREERUN_CORE_ENERGY_STATUS" ]]
					then
						echo "Special treatment for in-CPU energy '$counter'"
						values=$( grep "$counter" $res_path/emon_report | sed 's/\t/;/g' | grep "$counter;" | cut -f3,4 -d';' | sed 's/ //g' )
						for value in $values
						do
							val1=$( echo "$value" | cut -f1 -d';' )
							val2=$( echo "$value" | cut -f2 -d';' )
							let "val = $val1 + $val2"
							echo "$counter||$val" >> $res_path/likwid_report
						done
					else
							echo "Regular treatment for '$counter'"
							let "target_field = $XP_CORE + 3"
							values=$( grep "$counter" $res_path/emon_report | sed 's/\t/;/g' | grep "$counter;" | cut -f$target_field -d';' | sed 's/ //g' )
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

	echo "$codelet_name;$data_size;$memory_load;$frequency;$variant;" > $res_path/counters.csv

	cp $res_path/cpi.csv $res_path/counters.csv
	for counter in $counters
	do
		#echo "Processing counter '$counter'"
		#echo "Debug: $( grep "$counter \|$counter|" $res_path/likwid_report | sed "s/ //g" | cut -f3 -d'|' )"
		grep "$counter \|$counter|" $res_path/likwid_report | sed "s/ //g" | cut -f3 -d'|' | awk '{average += ($1 /'$iterations'); } END {print average / NR;}' > $res_path/likwid_counter_$counter
		paste -d';' $res_path/counters.csv $res_path/likwid_counter_$counter > $res_path/tmp
		mv $res_path/tmp $res_path/counters.csv
	done