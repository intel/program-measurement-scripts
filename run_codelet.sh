#!/bin/bash -l

source ./const.sh

if [[ "$nb_args" != "7" ]]
then
	echo "ERROR! Invalid arguments (need: codelet's folder, codelet's name, data size, memory load, frequency, variant, number of iterations)."
	exit -1
fi

codelet_folder=$( readlink -f "$1" )
codelet_name="$2"
data_size=$3
memory_load=$4
frequency=$5
variant="$6"
iterations="$7"


echo "Xp: '$codelet_name', size '$data_size', memload '$memory_load', frequency '$frequency', variant '$variant', iterations '$iterations'."


cd $codelet_folder
res_path="$codelet_folder/$CLS_RES_FOLDER/data_$data_size/memload_$memory_load/freq_$frequency/variant_$variant"


echo "Computing CPI..."
res=""
for i in $( seq $META_REPETITIONS )
do
	res=$( numactl -C $XP_CORE ./${codelet_name}_${variant}_cpi | grep CYCLES -A 1 | tail -n 1 )$( echo -e "\n$res" )
done


res=$( echo "$res" | sort -k1n,1n )
let "mean_line = ($META_REPETITIONS / 2) + 1"
mean=$( echo "$res" | awk "NR==$mean_line" )
normalized_mean=$( echo $mean | awk '{print $1 / '$iterations';}' )

echo -e "CPI \t'$normalized_mean'"
echo "$codelet_name;$data_size;$memory_load;$frequency;$variant;$normalized_mean" > "$res_path/cpi.csv"

echo "Ld library path: '$LD_LIBRARY_PATH'"

if [[ "$ACTIVATE_COUNTERS" != "0" ]]
then
	echo "Running counters..."

	for i in $( seq $META_REPETITIONS )
	do
		if [[ "$ACTIVATE_ADVANCED_COUNTERS" == "0" ]]
		then
			$LIKWID_PERFCTR -g INSTR_RETIRED_ANY:FIXC0,L1D_REPLACEMENT:PMC0,L2_LINES_IN_ALL:PMC1,L3_LAT_CACHE_MISS:PMC2,L1D_WB_RQST_ALL:PMC3 -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report
			$LIKWID_PERFCTR -g CPU_CLK_UNHALTED_CORE:FIXC1,MEMLOAD_UOPS_RETIRED_L1_HIT:PMC0,MEMLOAD_UOPS_RETIRED_L2_HIT:PMC1,MEMLOAD_UOPS_RETIRED_LLC_HIT:PMC2,MEMLOAD_UOPS_RETIRED_HIT_LFB:PMC3 -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report

			$LIKWID_PERFCTR -g CPU_CLK_UNHALTED_REF:FIXC2,MEMLOAD_UOPS_RETIRED_LLC_MISS:PMC0,SQ_MISC_FILL_DROPPED:PMC1,L1D_WB_RQST_MISS:PMC2,L2_TRANS_L2_WB:PMC3 -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report
			if [[ "$ACTIVATE_SANDY_BRIDGE_UNCORE" != "0" ]]
			then
				counters="CAS_COUNT_RD CAS_COUNT_WR"

				res=$( $LIKWID_PERFCTR -C $XP_CORE -g CAS_COUNT_RD:MBOX0C0,CAS_COUNT_WR:MBOX1C0,CAS_COUNT_RD:MBOX0C1,CAS_COUNT_WR:MBOX1C1,CAS_COUNT_RD:MBOX0C2,CAS_COUNT_WR:MBOX1C2,CAS_COUNT_RD:MBOX0C3,CAS_COUNT_WR:MBOX1C3 ./${codelet_name}_${variant}_hwc )

				#LLC_VICTIMS_M_STATE

				#echo -e "Just in case: '$res'"

				for c in $counters
				do
				val_sum=$( echo -e "$res" | grep $c | sed "s/ //g" | cut -f3 -d'|' | awk '{sum += ($1); } END {print sum;}' )
				echo "| $c | $val_sum | summed values from boxes" &>> $res_path/likwid_report
				#echo "| $c | $val_sum | summed values from boxes"
				done

			else
				counters=""
			fi
		else
			emon_counters="ARITH.FPU_DIV_ACTIVE,IDQ_UOPS_NOT_DELIVERED.CORE,MEM_LOAD_UOPS_RETIRED.HIT_LFB,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_4,MEM_LOAD_UOPS_RETIRED.L1_HIT,MEM_LOAD_UOPS_RETIRED.L2_HIT,MEM_LOAD_UOPS_RETIRED.LLC_HIT,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_8,L1D_PEND_MISS.PENDING,MISALIGN_MEM_REF.LOADS,MISALIGN_MEM_REF.STORES,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_16,OFFCORE_REQUESTS_BUFFER.SQ_FULL,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD,L1D.REPLACEMENT,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_32,L2_L1D_WB_RQSTS.ALL,L2_L1D_WB_RQSTS.MISS,L2_LINES_IN.ALL,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_64,L2_TRANS.L2_WB,SQ_MISC.FILL_DROPPED,UNC_M_CAS_COUNT.RD,UNC_M_CAS_COUNT.WR,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_128,L1D.STALL_FOR_REPLACE_CORE,L1D_BLOCKS.FB_BLOCK,L1D_PEND_MISS.REQUEST_FB_FULL,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_256,L1D_PEND_MISS.SS_FB_FULL,RESOURCE_STALLS.ANY,RESOURCE_STALLS.FPCW,RESOURCE_STALLS.LB,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_512,RESOURCE_STALLS.MXCSR,RESOURCE_STALLS.OTHER,RESOURCE_STALLS.ROB,RESOURCE_STALLS.RS,RESOURCE_STALLS.SB,RESOURCE_STALLS2.ALL_PRF_CONTROL,RESOURCE_STALLS2.BOB_FULL,RESOURCE_STALLS2.LOAD_MATRIX,RESOURCE_STALLS2.PHT_FULL,RESOURCE_STALLS2.PRRT_FULL,UOPS_DISPATCHED.STALL_CYCLES,UOPS_ISSUED.STALL_CYCLES,UOPS_RETIRED.STALL_CYCLES,IDQ.ALL_DSB_CYCLES_ANY_UOPS,INST_RETIRED.ANY,UOPS_DISPATCHED.CANCELLED,UOPS_DISPATCHED.CANCELLED_RS,UOPS_DISPATCHED.THREAD,UOPS_DISPATCHED_PORT.PORT_0,UOPS_DISPATCHED_PORT.PORT_1,UOPS_DISPATCHED_PORT.PORT_2,UOPS_DISPATCHED_PORT.PORT_3,UOPS_DISPATCHED_PORT.PORT_4,UOPS_DISPATCHED_PORT.PORT_5,UOPS_ISSUED.ANY,UOPS_RETIRED.ALL,UOPS_RETIRED.RETIRE_SLOTS,INT_MISC.RAT_STALL_CYCLES,CPU_CLK_UNHALTED.REF_TSC,CPU_CLK_UNHALTED.THREAD,DTLB_LOAD_MISSES.MISS_CAUSES_A_WALK,DTLB_LOAD_MISSES.STLB_HIT,DTLB_STORE_MISSES.MISS_CAUSES_A_WALK,DTLB_STORE_MISSES.STLB_HIT"
			emon -qu -t0 -C"($emon_counters)" taskset -c $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/emon_report
		fi
	done

	echo "Counter experiments done, proceeding to formatting."

	if [[ "$ACTIVATE_ADVANCED_COUNTERS" == "0" ]]
	then
		counters=$( echo "$counters INSTR_RETIRED_ANY CPU_CLK_UNHALTED_CORE CPU_CLK_UNHALTED_REF L1D_REPLACEMENT L2_LINES_IN_ALL L3_LAT_CACHE_MISS L1D_WB_RQST_ALL MEMLOAD_UOPS_RETIRED_L1_HIT MEMLOAD_UOPS_RETIRED_L2_HIT MEMLOAD_UOPS_RETIRED_LLC_HIT MEMLOAD_UOPS_RETIRED_HIT_LFB MEMLOAD_UOPS_RETIRED_LLC_MISS SQ_MISC_FILL_DROPPED L1D_WB_RQST_MISS L2_TRANS_L2_WB" | tr " " "\n" | sort --uniq | tr "\n" " " )
	else
		counters=$( echo "$emon_counters" | tr "," " " | tr "." "_" | tr " " "\n" | sort --uniq | tr "\n" " " )
		sed 's/\./_/g' -i $res_path/emon_report

		for counter in $counters
		do
			if [[ "$counter" == "UNC_M_CAS_COUNT_RD" || "$counter" == "UNC_M_CAS_COUNT_WR" ]]
			then
				echo "Special treatement for uncore '$counter'"
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
				echo "Regular treatment for '$counter'"
				let "target_field = $XP_CORE + 3"
				values=$( grep "$counter" $res_path/emon_report | sed 's/\t/;/g' | grep "$counter;" | cut -f$target_field -d';' | sed 's/ //g' )
				#echo "debug values: '$values'"
				for value in $values
				do
					echo "$counter||$value" >> $res_path/likwid_report
				done
			fi
		done
	fi


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
else
	echo "Skipping counters (not activated)."
fi


exit 0
