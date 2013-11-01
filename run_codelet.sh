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
      else
         $LIKWID_PERFCTR -g INSTR_RETIRED_ANY:FIXC0,L1D_REPLACEMENT:PMC0,L2_LINES_IN_ALL:PMC1,L3_LAT_CACHE_MISS:PMC2,OFFCORE_REQUESTS_DEMAND_DATA_RD:PMC3 -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report
         $LIKWID_PERFCTR -g MEMLOAD_UOPS_RETIRED_L1_HIT:PMC0,MEMLOAD_UOPS_RETIRED_L2_HIT:PMC1,MEMLOAD_UOPS_RETIRED_LLC_HIT:PMC2,MEMLOAD_UOPS_RETIRED_HIT_LFB:PMC3 -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report
         $LIKWID_PERFCTR -g MEMLOAD_UOPS_RETIRED_LLC_MISS:PMC0,SQ_MISC_FILL_DROPPED:PMC1,RESOURCE_STALLS2_ALL_FL_EMPTY:PMC2,RESOURCE_STALLS2_ALL_PRF_CONTROL:PMC3 -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report
         $LIKWID_PERFCTR -g RESOURCE_STALLS2_OOO_RSRC:PMC0,UOPS_DISPATCHED_PORT_PORT_0:PMC1,UOPS_DISPATCHED_PORT_PORT_1:PMC2,UOPS_DISPATCHED_PORT_PORT_2:PMC3 -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report
         $LIKWID_PERFCTR -g UOPS_DISPATCHED_PORT_PORT_3:PMC0,UOPS_DISPATCHED_PORT_PORT_4:PMC1,UOPS_DISPATCHED_PORT_PORT_5:PMC2,RESOURCE_STALLS_LB:PMC3 -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report
         $LIKWID_PERFCTR -g RESOURCE_STALLS_B:PMC0,RESOURCE_STALLS_FCSW:PMC1,RESOURCE_STALLS_MXCSR:PMC2,RESOURCE_STALLS_OTHER:PMC3 -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report
         $LIKWID_PERFCTR -g CPU_CLK_UNHALTED_CORE:FIXC1,CPU_CLK_UNHALTED_REF:FIXC2,MISALIGN_MEM_REF_LOAD:PMC0,MISALIGN_MEM_REF_STORE:PMC1,RESOURCE_STALLS_ANY:PMC2,UOPS_RETIRED_ALL:PMC3 -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report
         $LIKWID_PERFCTR -g IDQ_MITE_UOPS:PMC0,IDQ_DSB_UOPS:PMC1,IDQ_MS_UOPS:PMC2,IDQ_UOPS_NOT_DELIVERED_CORE:PMC3 -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report
         $LIKWID_PERFCTR -g PARTIAL_RAT_STALLS_FLAGS_MERGE_UOP:PMC0,PARTIAL_RAT_STALLS_SLOW_LEA_WINDOW:PMC1,RESOURCE_STALLS2_BOB_FULL:PMC2,PARTIAL_RAT_STALLS_MUL_SINGLE_UOP:PMC3 -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report
         $LIKWID_PERFCTR -g RESOURCE_STALLS_LB:PMC0,RESOURCE_STALLS_RS:PMC1,UOPS_ISSUED_ANY:PMC2,OFFCORE_REQUESTS_BUFFER_SQ_FULL:PMC3 -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report
         $LIKWID_PERFCTR -g RESOURCE_STALLS_ROB:PMC0,DTLB_LOAD_MISSES_CAUSES_A_WALK:PMC1,DTLB_STORE_MISSES_MISS_CAUSES_A_WALK:PMC2,L1D_WB_RQST_ALL:PMC3  -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report
         $LIKWID_PERFCTR -g L1D_WB_RQST_MISS:PMC0,L2_TRANS_L2_WB:PMC1  -C $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/likwid_report
      fi

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

	done

	echo "Counter experiments done, proceeding to formatting."

   if [[ "$ACTIVATE_ADVANCED_COUNTERS" == "0" ]]
   then
   	counters=$( echo "$counters INSTR_RETIRED_ANY CPU_CLK_UNHALTED_CORE CPU_CLK_UNHALTED_REF L1D_REPLACEMENT L2_LINES_IN_ALL L3_LAT_CACHE_MISS L1D_WB_RQST_ALL MEMLOAD_UOPS_RETIRED_L1_HIT MEMLOAD_UOPS_RETIRED_L2_HIT MEMLOAD_UOPS_RETIRED_LLC_HIT MEMLOAD_UOPS_RETIRED_HIT_LFB MEMLOAD_UOPS_RETIRED_LLC_MISS SQ_MISC_FILL_DROPPED L1D_WB_RQST_MISS L2_TRANS_L2_WB" | tr " " "\n" | sort --uniq | tr "\n" " " )
   else
         counters=$( echo "$counters INSTR_RETIRED_ANY L1D_REPLACEMENT L2_LINES_IN_ALL L3_LAT_CACHE_MISS OFFCORE_REQUESTS_DEMAND_DATA_RD OFFCORE_REQUESTS_BUFFER_SQ_FULL MEMLOAD_UOPS_RETIRED_L1_HIT MEMLOAD_UOPS_RETIRED_L2_HIT MEMLOAD_UOPS_RETIRED_LLC_HIT MEMLOAD_UOPS_RETIRED_HIT_LFB MEMLOAD_UOPS_RETIRED_LLC_MISS SQ_MISC_FILL_DROPPED RESOURCE_STALLS2_ALL_FL_EMPTY RESOURCE_STALLS2_ALL_PRF_CONTROL RESOURCE_STALLS_ROB RESOURCE_STALLS_LB RESOURCE_STALLS_RS RESOURCE_STALLS2_OOO_RSRC UOPS_DISPATCHED_PORT_PORT_0 UOPS_DISPATCHED_PORT_PORT_1 UOPS_DISPATCHED_PORT_PORT_2 UOPS_DISPATCHED_PORT_PORT_3 UOPS_DISPATCHED_PORT_PORT_4 UOPS_DISPATCHED_PORT_PORT_5 RESOURCE_STALLS_B RESOURCE_STALLS_FCSW RESOURCE_STALLS_MXCSR RESOURCE_STALLS_OTHER CPU_CLK_UNHALTED_CORE CPU_CLK_UNHALTED_REF MISALIGN_MEM_REF_LOAD MISALIGN_MEM_REF_STORE RESOURCE_STALLS_ANY UOPS_RETIRED_ALL IDQ_MITE_UOPS IDQ_DSB_UOPS IDQ_MS_UOPS IDQ_UOPS_NOT_DELIVERED_CORE PARTIAL_RAT_STALLS_FLAGS_MERGE_UOP PARTIAL_RAT_STALLS_SLOW_LEA_WINDOW UOPS_ISSUED_ANY RESOURCE_STALLS2_BOB_FULL PARTIAL_RAT_STALLS_MUL_SINGLE_UOP DTLB_LOAD_MISSES_CAUSES_A_WALK DTLB_STORE_MISSES_MISS_CAUSES_A_WALK L1D_WB_RQST_ALL L1D_WB_RQST_MISS L2_TRANS_L2_WB" | tr " " "\n" | sort --uniq | tr "\n" " " )
   fi

	echo "$codelet_name;$data_size;$memory_load;$frequency;$variant;" > $res_path/counters.csv
	cp $res_path/cpi.csv $res_path/counters.csv
	for counter in $counters
	do
		#echo "Processing counter '$counter'"
		grep $counter $res_path/likwid_report | sed "s/ //g" | cut -f3 -d'|' | awk '{average += ($1 /'$iterations'); } END {print average / NR;}' > $res_path/likwid_counter_$counter
		paste -d';' $res_path/counters.csv $res_path/likwid_counter_$counter > $res_path/tmp
		mv $res_path/tmp $res_path/counters.csv
	done
else
	echo "Skipping counters (not activated)."
fi


exit 0
