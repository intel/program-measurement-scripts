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

START_RUN_CODELETS_SH=$(date '+%s')
echo "Xp: '$codelet_name', size '$data_size', memload '$memory_load', frequency '$frequency', variant '$variant', iterations '$iterations'."


cd $codelet_folder
res_path="$codelet_folder/$CLS_RES_FOLDER/data_$data_size/memload_$memory_load/freq_$frequency/variant_$variant"

TASKSET=$( which taskset )
NUMACTL=$( which numactl )

rm -f time.out

append_counters()
{
    activate="$1"
    item_type="$2"
    more_items="$3"

    if [[ "${activate}" != "0" ]]
	then
	if [ -z ${more_items} ]
	    then
	    echo "ERROR! ACTIVATED empty ${item_type} counters"
	    exit -1
	else
	    emon_counters+=",${more_items}"
	fi
    fi      
}

echo "Computing CPI..."
res=""

if [[ "${variant}" == "ORG" ]]
    then
# Run the original program
    run_prog="./${codelet_name}"
else
# Run the DECAN generated program
    run_prog="./${codelet_name}_${variant}_hwc"
fi

for i in $( seq $META_REPETITIONS )
do
	#res=$( taskset -c $XP_CORE ./${codelet_name}_${variant}_cpi | grep CYCLES -A 1 | tail -n 1 )$( echo -e "\n$res" )
#	taskset -c $XP_CORE ./${codelet_name}_${variant}_hwc 
#	${NUMACTL} -m ${XP_NODE} -C ${XP_CORE} ./${codelet_name}_${variant}_hwc 
  echo ${NUMACTL} -m ${XP_NODE} -C ${XP_CORE} ${run_prog}
	${NUMACTL} -m ${XP_NODE} -C ${XP_CORE} ${run_prog}
	res=$( tail -n 1 time.out | cut -d'.' -f1 )$( echo -e "\n$res" )
done
rm -f time.out


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
      basic_counters="INST_RETIRED.ANY,CPU_CLK_UNHALTED.REF_TSC,CPU_CLK_UNHALTED.THREAD"
      tlb_counters="DTLB_LOAD_MISSES.MISS_CAUSES_A_WALK,DTLB_LOAD_MISSES.STLB_HIT,DTLB_STORE_MISSES.MISS_CAUSES_A_WALK,DTLB_STORE_MISSES.STLB_HIT"

      # following are top down counters only for IVB.  When the list of other arch is available, we should move the assignment into IVB case statements.
      topdown_unc_counters="OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DEMAND_DATA_RD,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c6"
      topdown_mem_counters="CYCLE_ACTIVITY.STALLS_LDM_PENDING,CYCLE_ACTIVITY.STALLS_L1D_PENDING,CYCLE_ACTIVITY.STALLS_L2_PENDING,MEM_LOAD_UOPS_RETIRED.LLC_HIT_PS,MEM_LOAD_UOPS_RETIRED.LLC_MISS_PS"
      topdown_exe_counters="CYCLE_ACTIVITY.CYCLES_NO_EXECUTE,RS_EVENTS.EMPTY_CYCLES,UOPS_EXECUTED.THREAD,UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC,UOPS_EXECUTED.CYCLES_GE_2_UOPS_EXEC,UOPS_EXECUTED.CYCLES_GE_3_UOPS_EXEC,UOPS_EXECUTED.CYCLES_GE_4_UOPS_EXEC,IDQ_UOPS_NOT_DELIVERED.CYCLES_0_UOPS_DELIV.CORE"
      topdown_ms_seq_counters="IDQ.MS_UOPS"
      topdown_fp_arith_counters="FP_COMP_OPS_EXE.X87,FP_COMP_OPS_EXE.SSE_SCALAR_SINGLE,FP_COMP_OPS_EXE.SSE_SCALAR_DOUBLE,FP_COMP_OPS_EXE.SSE_PACKED_SINGLE,FP_COMP_OPS_EXE.SSE_PACKED_DOUBLE,SIMD_FP_256.PACKED_SINGLE,SIMD_FP_256.PACKED_DOUBLE"
      
      topdown_port_counters="UOPS_DISPATCHED_PORT.PORT_0,UOPS_DISPATCHED_PORT.PORT_1,UOPS_DISPATCHED_PORT.PORT_2,UOPS_DISPATCHED_PORT.PORT_3,UOPS_DISPATCHED_PORT.PORT_4,UOPS_DISPATCHED_PORT.PORT_5"
      topdown_port_util_counters="${topdown_port_counters},ARITH.FPU_DIV_ACTIVE"
#      topdown_fe_lat_counters="ICACHE.IFETCH_STALL,ITLB_MISSES.STLB_HIT,ITLB_MISSES.WALK_DURATION,RS_EVENTS.EMPTY_END,BR_MISP_RETIRED.ALL_BRANCHES_PS,MACHINE_CLEARS.COUNT,BACLEARS.ANY,DSB2MITE_SWITCHES.PENALTY_CYCLES,ILD_STALL.LCP"
      topdown_fe_lat_counters="IDQ.MS_UOPS:e1"

      topdown_counters="${topdown_ms_seq_counters},${topdown_exe_counters},${topdown_mem_counters},${topdown_unc_counters},${topdown_port_util_counters}"

      case "$UARCH" in
	  "SANDY_BRIDGE")
	  mem_traffic_counters="UNC_M_CAS_COUNT.RD,UNC_M_CAS_COUNT.WR,L1D.REPLACEMENT,L2_L1D_WB_RQSTS.ALL,L2_L1D_WB_RQSTS.MISS,L2_LINES_IN.ALL,L2_TRANS.L2_WB,SQ_MISC.FILL_DROPPED"
	  resource_counters="RESOURCE_STALLS.ANY,RESOURCE_STALLS.RS,RESOURCE_STALLS.ROB,RESOURCE_STALLS2.ALL_PRF_CONTROL"
 	  energy_counters="FREERUN_PKG_ENERGY_STATUS,FREERUN_CORE_ENERGY_STATUS"
	  other_counters="${energy_counters},L2_RQSTS.PF_MISS,UOPS_RETIRED.RETIRE_SLOTS,IDQ_UOPS_NOT_DELIVERED.CORE,UOPS_ISSUED.ANY,INT_MISC.RECOVERY_CYCLES,UOPS_RETIRED.ALL,OFFCORE_RESPONSE.STREAMING_STORES.ANY_RESPONSE_0"
	  ;;

	  "HASWELL")
	  mem_traffic_counters="UNC_IMC_DRAM_DATA_READS,UNC_IMC_DRAM_DATA_WRITES,L1D.REPLACEMENT,L2_DEMAND_RQSTS.WB_HIT,L2_TRANS.L1D_WB,L2_DEMAND_RQSTS.WB_MISS,L2_LINES_IN.ALL,L2_TRANS.L2_WB,SQ_MISC.FILL_DROPPED,L2_RQSTS.MISS"

	  resource_counters="RESOURCE_STALLS.ANY,RESOURCE_STALLS.RS,RESOURCE_STALLS.ROB,RESOURCE_STALLS2.ALL_PRF_CONTROL"
	  tlb_counters="DTLB_LOAD_MISSES.MISS_CAUSES_A_WALK,DTLB_LOAD_MISSES.STLB_HIT,DTLB_STORE_MISSES.MISS_CAUSES_A_WALK,DTLB_STORE_MISSES.STLB_HIT"
	  energy_counters="UNC_PP0_ENERGY_STATUS,UNC_PKG_ENERGY_STATUS"
	  other_counters="${energy_counters},UOPS_RETIRED.RETIRE_SLOTS,IDQ_UOPS_NOT_DELIVERED.CORE,UOPS_ISSUED.ANY,INT_MISC.RECOVERY_CYCLES,UOPS_RETIRED.ALL"
	  if [[ "$HOSTNAME" == "fxhaswell-l4" ]]
	      then
	      mem_traffic_counters+=",UNC_L4_REQUEST.RD_HIT,UNC_L4_REQUEST.WR_HIT,UNC_L4_REQUEST.WR_FILL,UNC_L4_REQUEST.RD_EVICT_LINE_TO_DRAM,UNC_CBO_L4_SUPERLINE.ALLOC_FAIL"
	  fi
	  ;;

	  "IVY_BRIDGE")
	  mem_traffic_counters="UNC_M_CAS_COUNT.RD,UNC_M_CAS_COUNT.WR,L1D.REPLACEMENT,L2_L1D_WB_RQSTS.ALL,L2_L1D_WB_RQSTS.MISS,L2_LINES_IN.ALL,L2_TRANS.L2_WB,SQ_MISC.FILL_DROPPED"
	  resource_counters="RESOURCE_STALLS.ANY,RESOURCE_STALLS.RS,RESOURCE_STALLS.LB,RESOURCE_STALLS.SB,RESOURCE_STALLS.ROB,RESOURCE_STALLS2.ALL_PRF_CONTROL,RESOURCE_STALLS2.PHT_FULL,RESOURCE_STALLS2.OOO_RSRC,RESOURCE_STALLS.MEM_RS,RESOURCE_STALLS.OOO_RSRC,RESOURCE_STALLS.LB_SB,RESOURCE_STALLS.FPCW,RESOURCE_STALLS.MXCSR,RESOURCE_STALLS.LOAD_MATRIX"
	  other_counters="L2_RQSTS.PF_MISS,UOPS_RETIRED.RETIRE_SLOTS,IDQ_UOPS_NOT_DELIVERED.CORE,UOPS_ISSUED.ANY,INT_MISC.RECOVERY_CYCLES,UOPS_RETIRED.ALL,OFFCORE_RESPONSE.STREAMING_STORES.ANY_RESPONSE_0"
	  ;;
	  
	  
	  *)
	  # the basic counter is slightly different 'INST_RETIRED.ANY_P', redefine it
	  basic_counters="INST_RETIRED.ANY_P,CPU_CLK_UNHALTED.CORE,CPU_CLK_UNHALTED.REF_TSC"
	  mem_traffic_counters="LONGEST_LAT_CACHE.MISS,OFFCORE_RESPONSE:request=COREWB:response=L2_MISS.NO_SNOOP_NEEDED,OFFCORE_RESPONSE:request=COREWB:response=L2_HIT,MEM_UOPS_RETIRED.L1_MISS_LOADS,OFFCORE_RESPONSE:request=PF_L1_DATA_RD:response=ANY_RESPONSE,OFFCORE_RESPONSE:request=DEMAND_RFO:response=ANY_RESPONSE,OFFCORE_RESPONSE:request=DEMAND_DATA_RD:response=ANY_RESPONSE,OFFCORE_RESPONSE:request=COREWB:response=ANY_RESPONSE"
	  tlb_counters=""
	  resource_counters=""
	  other_counters="CYCLES_DIV_BUSY.ALL,UOPS_RETIRED.ALL,NO_ALLOC_CYCLES.ROB_FULL,NO_ALLOC_CYCLES.RAT_STALL,NO_ALLOC_CYCLES.NOT_DELIVERED,NO_ALLOC_CYCLES.ALL,RS_FULL_STALL.MEC,RS_FULL_STALL.ALL,REHABQ.STA_FULL,REHABQ.ANY_LD,REHABQ.ANY_ST,MEM_UOPS_RETIRED.L2_HIT_LOADS,MEM_UOPS_RETIRED.L2_MISS_LOADS,PAGE_WALKS.D_SIDE_WALKS,PAGE_WALKS.D_SIDE_CYCLES,MS_DECODED.MS_ENTRY"
	  ;;
      esac

      emon_counters="${basic_counters}"
      append_counters $ACTIVATE_MEM_TRAFFIC_COUNTERS "traffic" ${mem_traffic_counters}
      append_counters $ACTIVATE_RESOURCE_COUNTERS "resource" ${resource_counters}
      append_counters $ACTIVATE_TLB_COUNTERS "TLB" ${tlb_counters}
      append_counters $ACTIVATE_TOPDOWN_COUNTERS "TopDown" ${topdown_counters}
      append_counters $ACTIVATE_TOPDOWN_FP_ARITH_COUNTERS "TopDownFp" ${topdown_fp_arith_counters}
      append_counters $ACTIVATE_TOPDOWN_FE_LAT_COUNTERS "TopDownFeLat" ${topdown_fe_lat_counters}


#       if [[ "$ACTIVATE_MEM_TRAFFIC_COUNTERS" != "0" ]]
# 	  then
# 	  if [ -z ${mem_traffic_counters} ]
# 	      then
# 	      echo "ERROR! ACTIVATED empty traffic counters"
# 	      exit -1
# 	  else
# 	      emon_counters+=",${mem_traffic_counters}"
# 	  fi
#       fi      

#       if [[ "$ACTIVATE_RESOURCE_COUNTERS" != "0" ]]
# 	  then
# 	  if [ -z ${resource_counters} ]
# 	      then
# 	      echo "ERROR! ACTIVATED empty resource counters"
# 	      exit -1
# 	  else
# 	      emon_counters+=",${resource_counters}"
# 	  fi
#       fi      


#       if [[ "$ACTIVATE_TLB_COUNTERS" != "0" ]]
# 	  then
# 	  if [ -z ${tlb_counters} ]
# 	      then
# 	      echo "ERROR! ACTIVATED empty TLB counters"
# 	      exit -1
# 	  else
# 	      emon_counters+=",${tlb_counters}"
# 	  fi
#       fi      

#       if [[ "$ACTIVATE_TOPDOWN_COUNTERS" != "0" ]]
# 	  then
# 	  if [ -z ${topdown_counters} ]
# 	      then
# 	      echo "ERROR! ACTIVATED empty TOPDOWN counters"
# 	      exit -1
# 	  else
# 	      emon_counters+=",${topdown_counters}"
# 	  fi
#       fi      

      emon_counters+=",${other_counters}"
      
      
      
      # Add more counters for advance counter choice
      if [[ "$ACTIVATE_ADVANCED_COUNTERS" != "0" ]]
	  then
	  case "$UARCH" in
	      "SANDY_BRIDGE")
	      mem_hit_counters="MEM_LOAD_UOPS_RETIRED.HIT_LFB,MEM_LOAD_UOPS_RETIRED.L1_HIT,MEM_LOAD_UOPS_RETIRED.L2_HIT,MEM_LOAD_UOPS_RETIRED.LLC_HIT,"
	      adv_resource_counters="RESOURCE_STALLS.FPCW,RESOURCE_STALLS.LB,RESOURCE_STALLS.MXCSR,RESOURCE_STALLS.OTHER,RESOURCE_STALLS.SB,RESOURCE_STALLS2.BOB_FULL,RESOURCE_STALLS2.LOAD_MATRIX,RESOURCE_STALLS2.PHT_FULL,RESOURCE_STALLS2.PRRT_FULL"
	      port_counters="UOPS_DISPATCHED_PORT.PORT_0,UOPS_DISPATCHED_PORT.PORT_1,UOPS_DISPATCHED_PORT.PORT_2,UOPS_DISPATCHED_PORT.PORT_3,UOPS_DISPATCHED_PORT.PORT_4,UOPS_DISPATCHED_PORT.PORT_5"
	      emon_counters+=",${mem_hit_counters},${adv_resource_counters},${port_counters},ARITH.FPU_DIV_ACTIVE,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_4,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_8,L1D_PEND_MISS.PENDING,MISALIGN_MEM_REF.LOADS,MISALIGN_MEM_REF.STORES,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_16,OFFCORE_REQUESTS_BUFFER.SQ_FULL,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_32,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_64,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_128,L1D.STALL_FOR_REPLACE_CORE,L1D_BLOCKS.FB_BLOCK,L1D_PEND_MISS.REQUEST_FB_FULL,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_256,L1D_PEND_MISS.SS_FB_FULL,MEM_TRANS_RETIRED.LOAD_LATENCY_GT_512,UOPS_ISSUED.STALL_CYCLES,UOPS_RETIRED.STALL_CYCLES,IDQ.ALL_DSB_CYCLES_ANY_UOPS,UOPS_DISPATCHED.CANCELLED,UOPS_DISPATCHED.CANCELLED_RS,UOPS_DISPATCHED.THREAD,INT_MISC.RAT_STALL_CYCLES,LD_BLOCKS_PARTIAL.ADDRESS_ALIAS,LD_BLOCKS.ALL_BLOCK,UOPS_DISPATCHED.THREAD:u0x3F:c1:i0:e0,UOPS_DISPATCHED.THREAD:u0x3F:c2:i0:e0,UOPS_DISPATCHED.THREAD:u0x3F:c4:i0:e0"
	      ;;
	      "HASWELL")
	      ;;
	      *)
	      ;;
	  esac
	  
      fi
      echo ${emon_counters} > "$res_path/${EMON_COUNTER_NAMES_FILE}"
#		echo "emon -qu -t0 -C\"($emon_counters)\" $TASKSET -c $XP_CORE ./${codelet_name}_${variant}_hwc &>> $res_path/emon_report"
		#emon -F "$res_path/emon_report" -qu -t0 -C"($emon_counters)" $TASKSET -c $XP_CORE ./${codelet_name}_${variant}_hwc &> "$res_path/emon_execution_log"
      if [[ "ENABLE_SEP" == "1" ]];then
	  emon_counters_to_run=$(./split_counters.sh $emon_counters)
	  emon_counters_core=$(echo $emon_counters_to_run | tr '#' '\n' | head -n 1)
	  emon_counters_uncore=$(echo $emon_counters_to_run | tr '#' '\n' | tail -n 1)
	  
	  echo $emon_counters_core >  "$res_path/core_events_list"
	  echo $emon_counters_uncore >  "$res_path/uncore_events_list"
	  
	  for events in $(echo $emon_counters_core  | tr ';' ' ')
	    do
	    events_code=$(echo $events | cut -d':' -f1)
	    events=$(echo $events | cut -d':' -f2)
#	    $NUMACTL -m $XP_NODE -C $XP_CORE sep -start -sp -out $res_path"/sep_report_"$events_code"_"$i -ec "$events" -count -app ./${codelet_name}_${variant}_hwc &> "$res_path/emon_execution_log"
	    $NUMACTL -m $XP_NODE -C $XP_CORE sep -start -sp -out $res_path"/sep_report_"$events_code"_"$i -ec "$events" -count -app ${run_prog} &> "$res_path/emon_execution_log"
	  done
	  
	  for events in $(echo $emon_counters_uncore  | tr ';' ' ')
	    do	
	    events_code=$(echo $events | cut -d':' -f1)
	    events=$(echo $events | cut -d':' -f2)
#	    $NUMACTL -m $XP_NODE -C $XP_CORE sep -start -sp -out $res_path"/sep_report_"$events_code"_"$i -ec "$events" -app ./${codelet_name}_${variant}_hwc &> "$res_path/emon_execution_log"
	    $NUMACTL -m $XP_NODE -C $XP_CORE sep -start -sp -out $res_path"/sep_report_"$events_code"_"$i -ec "$events" -app ${run_prog} &> "$res_path/emon_execution_log"
	  done
      else
#	  emon -F "$res_path/emon_report" -qu -t0 -C"($emon_counters)" $NUMACTL -m $XP_NODE -C $XP_CORE  ./${codelet_name}_${variant}_hwc &> "$res_path/emon_execution_log"
#	  emon -F "$res_path/emon_report" -qu -t0 -C"($emon_counters)" $NUMACTL -m $XP_NODE -C $XP_CORE  ${run_prog} &> "$res_path/emon_execution_log"
	  if [[ "$MC_RUN" != "0" ]]
	      then 
	      for cc in ${XP_REST_CORES}
	      do
		$NUMACTL -m $XP_NODE -C ${cc} ${run_prog} &
	      done
# 	      $NUMACTL -m $XP_NODE -C 10 ${run_prog} &
# 	      $NUMACTL -m $XP_NODE -C 11 ${run_prog} &
# 	      $NUMACTL -m $XP_NODE -C 12 ${run_prog} &
# 	      $NUMACTL -m $XP_NODE -C 13 ${run_prog} &
# 	      $NUMACTL -m $XP_NODE -C 14 ${run_prog} &
# 	      $NUMACTL -m $XP_NODE -C 15 ${run_prog} &
# 	      $NUMACTL -m $XP_NODE -C 16 ${run_prog} &
# 	      $NUMACTL -m $XP_NODE -C 17 ${run_prog} &
# 	      $NUMACTL -m $XP_NODE -C 18 ${run_prog} &
	  fi
	  emon -F "$res_path/emon_report" -qu -t0 -C"($emon_counters)" $NUMACTL -m $XP_NODE -C $XP_CORE  ${run_prog} &> "$res_path/emon_execution_log"
      fi
    done
else
    echo "Skipping counters (not activated)."
fi

# if [[ "$ACTIVATE_COUNTERS" != "0" ]]
# then
# 	echo "Counter experiments done, proceeding to formatting."
# 	${FORMAT_COUNTERS_SH} "$codelet_name" $data_size $memory_load $frequency "$variant" "${iterations}" "${emon_counters}" ${res_path}
# fi

END_RUN_CODELETS_SH=$(date '+%s')
ELAPSED_RUN_CODELETS_SH=$((${END_RUN_CODELETS_SH} - ${START_RUN_CODELETS_SH}))
echo "run_codelets.sh finished in $(${SEC_TO_DHMS_SH} ${ELAPSED_RUN_CODELETS_SH}) seconds."



exit 0
