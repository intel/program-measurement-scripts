#!/bin/bash 

source $(dirname $0)/const.sh

if [[ "$nb_args" != "2" ]]
then
    echo "ERROR! Invalid arguments (need: emon-info-file (generated by 'emon -v') and list override)."
    exit -1
fi

emon_info_file="$1"
list_override="$2"

if [[ $( grep SEP "$emon_info_file" ) == "" ]]
then 
    old_emon="1"
else 
    old_emon="0"
fi      
emon_db=$(grep "EMON Database" ${emon_info_file}|cut -f4 -d' '|tr -d '\r')



overrides=($(echo ${list_override} | sed 's/,/ /g'))
echo "OVERRIDING LIST: (" ${overrides[@]} ")" 1>&2

for ov in ${overrides[@]}
do
  key=$(echo $ov|sed 's/=.*//g')
  value=$(echo $ov|sed 's/.*=//g')
  echo "OVERRIDING: $key <= $value" 1>&2
  activateCtrs[${key}]=${value}
done


mk_histo_counters()
{
    local __counters=$1
    local name=$2
    local ub=$3

    local items=( ${name}:c{1..9} )
    eval 'hexitems=($(printf "${name}:c0x%x " '{10..${ub}'}))'
    items=(${items[@]} ${hexitems[@]})
    local result=$(IFS=','; echo "${items[*]}")
    eval $__counters="'$result'"
}

append_counters()
{
    activate="$1"
    item_type="$2"
    more_items="$3"

# More checkes for activate because it could be an associate array
#echo "ACT ${item_type} is -->${activate}<--"
    if [[ ! -z "${activate}" && "${activate}" != "0" ]]
	then
	if [ -z ${more_items} ]
	    then
	    echo "ERROR! ACTIVATED empty ${item_type} counters"
	    exit -1
	else
#	    echo "ADDED: ${more_items}"
#	    echo "counters: ${emon_counters}"
	    emon_counters+=",${more_items}"
	fi
    fi      
}




basic_counters="INST_RETIRED.ANY,CPU_CLK_UNHALTED.REF_TSC,CPU_CLK_UNHALTED.THREAD"
mem_hit_counters="MEM_LOAD_UOPS_RETIRED.L1_HIT,MEM_LOAD_UOPS_RETIRED.L1_MISS,MEM_LOAD_UOPS_RETIRED.HIT_LFB,MEM_LOAD_UOPS_RETIRED.L2_HIT,MEM_UOPS_RETIRED.ALL_LOADS,MEM_UOPS_RETIRED.ALL_STORES"

tlb_counters="DTLB_LOAD_MISSES.MISS_CAUSES_A_WALK,DTLB_LOAD_MISSES.STLB_HIT,DTLB_STORE_MISSES.MISS_CAUSES_A_WALK,DTLB_STORE_MISSES.STLB_HIT,DTLB_LOAD_MISSES.WALK_DURATION,DTLB_STORE_MISSES.WALK_DURATION"
lfb_counters="L1D_PEND_MISS.PENDING,L1D_PEND_MISS.PENDING_CYCLES"
sq_counters="OFFCORE_REQUESTS_BUFFER.SQ_FULL,OFFCORE_REQUESTS_OUTSTANDING.ALL_DATA_RD,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:u5,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD,OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DATA_RD"

#      lfb_histogram_counters="L1D_PEND_MISS.PENDING:c1,L1D_PEND_MISS.PENDING:c2,L1D_PEND_MISS.PENDING:c3,L1D_PEND_MISS.PENDING:c4,L1D_PEND_MISS.PENDING:c5,L1D_PEND_MISS.PENDING:c6,L1D_PEND_MISS.PENDING:c7,L1D_PEND_MISS.PENDING:c8,L1D_PEND_MISS.PENDING:c9,L1D_PEND_MISS.PENDING:c0xa,L1D_PEND_MISS.PENDING:c0xb"

#       sqr_histogram_counters="OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c1,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c2,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c3,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c4,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c5,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c6,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c7,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c8,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c9,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c0xa,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c0xb,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c0xc,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c0xd,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c0xe,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c0xf,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c0x10"

#       sqw_histogram_counters="OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c1,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c2,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c3,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c4,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c5,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c6,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c7,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c8,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c9,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c0xa,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c0xb,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c0xc,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c0xd,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c0xe,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c0xf,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO:c0x10"

#       items=( OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:u5:c{1..9} )
#       hexitems=($(printf "OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:u5:c0x%x " {10..16}))
#       items=(${items[@]} ${hexitems[@]})
#       sqrw_histogram_counters=$(IFS=','; echo "${items[*]}")


mk_histo_counters lfb_histogram_counters "L1D_PEND_MISS.PENDING" 11
mk_histo_counters sqr_histogram_counters "OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD" 16
mk_histo_counters sqw_histogram_counters "OFFCORE_REQUESTS_OUTSTANDING.DEMAND_RFO" 16
mk_histo_counters sqrw_histogram_counters "OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:u5" 16

sq_histogram_counters="${sqr_histogram_counters},${sqw_histogram_counters},${sqrw_histogram_counters}"

# More counter about latency breakdowns provided by Michael Frederick
l3_hit_rate_check_counters="UNC_CBO_CACHE_LOOKUP.ANY_I,UNC_CBO_CACHE_LOOKUP.ANY_MESI"
irq_life_counters="UNC_CBO_INGRESS_OCCUPANACY.IRQ,UNC_CBO_INGRESS_ALLOCATION.IRQ"
tor_life_counters="UNC_CBO_TOR_OCCUPANCY.DRD_VALID,UNC_CBO_TOR_ALLOCATION.DRD"
egr_ad_life_counters="UNC_CBO_EGRESS_OCCUPANCY.AD_CORE,UNC_CBO_EGRESS_ALLOCATION.AD_CORE"
egr_bl_life_counters="UNC_CBO_EGRESS_OCCUPANCY.BL_CACHE,UNC_CBO_EGRESS_ALLOCATION.BL_CACHE"


# Topdown counters.  Initialized with SNB set and update per arch afterwards.  At the end assembled as counter set.
topdown_FE="IDQ_UOPS_NOT_DELIVERED.CORE"
topdown_BADS="UOPS_ISSUED.ANY,UOPS_RETIRED.RETIRE_SLOTS,INT_MISC.RECOVERY_CYCLES_ANY"
topdown_RETR="UOPS_RETIRED.RETIRE_SLOTS"
topdown_BE="${topdown_FE},${topdown_BADS},${topdown_RETR}"

topdown_FE_LAT="CPU_CLK_UNHALTED.THREAD,IDQ_UOPS_NOT_DELIVERED.CYCLES_0_UOPS_DELIV.CORE"
topdown_FE_BW="${topdown_FE},${topdown_FE_LAT}"

topdown_BADS_BR="${topdown_BADS},BR_MISP_RETIRED.ALL_BRANCHES,MACHINE_CLEARS.COUNT"
topdown_BADS_MCLR="${topdown_BADS},${topdown_BADS_BR}"

topdown_aux_Memory_Bound_Fraction="" # Has formula for SNB, BDW but complicated so only define for SKX below (simpler)

topdown_BE_MEM_L1="CYCLE_ACTIVITY.STALLS_MEM_ANY,CYCLE_ACTIVITY.STALLS_L1D_MISS"
topdown_BE_MEM_L2="" # None for SNB
topdown_BE_MEM_L3="" # Has formula for SNB, BDW but complicated so only define for SKX below (simpler)
topdown_BE_MEM_DRAM="" # Has formula for SNB, BDW but complicated so only define for SKX below (simpler)
topdown_BE_MEM_STOR="RESOURCE_STALLS.SB"


topdown_BE_CORE_DIV="ARITH.FPU_DIV_ACTIVE"
topdown_BE_CORE_PORT="" # Has formula for SNB, BDW but complicated so only define for SKX below (simpler)

# TODO: Add if needed
#topdown_RETR_BASE=""
#topdown_RETR_MSEQ=""




# following are top down counters only for IVB.  When the list of other arch is available, we should move the assignment into IVB case statements.
# (Obsolete)
topdown_unc_counters="OFFCORE_REQUESTS_OUTSTANDING.CYCLES_WITH_DEMAND_DATA_RD,OFFCORE_REQUESTS_OUTSTANDING.DEMAND_DATA_RD:c6"
topdown_l3_bound_counters=""
topdown_mem_bound_counters=""
topdown_store_bound_counters=""
topdown_ms_seq_counters="IDQ.MS_UOPS"
topdown_fp_arith_counters="FP_COMP_OPS_EXE.X87,FP_COMP_OPS_EXE.SSE_SCALAR_SINGLE,FP_COMP_OPS_EXE.SSE_SCALAR_DOUBLE,FP_COMP_OPS_EXE.SSE_PACKED_SINGLE,FP_COMP_OPS_EXE.SSE_PACKED_DOUBLE,SIMD_FP_256.PACKED_SINGLE,SIMD_FP_256.PACKED_DOUBLE"
topdown_port_counters="UOPS_DISPATCHED_PORT.PORT_0,UOPS_DISPATCHED_PORT.PORT_1,UOPS_DISPATCHED_PORT.PORT_2,UOPS_DISPATCHED_PORT.PORT_3,UOPS_DISPATCHED_PORT.PORT_4,UOPS_DISPATCHED_PORT.PORT_5"

#      topdown_fe_lat_counters="ICACHE.IFETCH_STALL,ITLB_MISSES.STLB_HIT,ITLB_MISSES.WALK_DURATION,RS_EVENTS.EMPTY_END,BR_MISP_RETIRED.ALL_BRANCHES_PS,MACHINE_CLEARS.COUNT,BACLEARS.ANY,DSB2MITE_SWITCHES.PENALTY_CYCLES,ILD_STALL.LCP"
topdown_fe_lat_counters="IDQ.MS_UOPS:e1"
branch_counters="BR_INST_RETIRED.ALL_BRANCHES,BR_MISP_RETIRED.ALL_BRANCHES"
lsd_counters="LSD.CYCLES_ACTIVE,LSD.UOPS,IDQ.DSB_UOPS,IDQ.MITE_UOPS,IDQ.MS_UOPS"

topdown_exe_counters="RS_EVENTS.EMPTY_CYCLES,IDQ_UOPS_NOT_DELIVERED.CYCLES_0_UOPS_DELIV.CORE,IDQ_UOPS_NOT_DELIVERED.CORE"
mem_rowbuff_counters=""



#case "$UARCH" in
case "$emon_db" in
# Below need to first upgrade EMON to v10.0.0 to work
    "SANDY_BRIDGE")
        if [[ "$old_emon" == "1" ]]
	then
	    topdown_mem_counters="CYCLE_ACTIVITY.STALL_CYCLES_L1D_PENDING,CYCLE_ACTIVITY.STALL_CYCLES_L2_PENDING,MEM_LOAD_UOPS_RETIRED.LLC_HIT,MEM_LOAD_UOPS_RETIRED.LLC_MISS"
	else
	    topdown_mem_counters="CYCLE_ACTIVITY.STALLS_L1D_PENDING,CYCLE_ACTIVITY.STALLS_L2_PENDING,MEM_LOAD_UOPS_RETIRED.LLC_HIT,MEM_LOAD_UOPS_RETIRED.LLC_MISS"
	fi

	mem_hit_counters+=",MEM_LOAD_UOPS_RETIRED.LLC_HIT,MEM_LOAD_UOPS_RETIRED.LLC_MISS"

	mem_traffic_counters="UNC_M_CAS_COUNT.RD,UNC_M_CAS_COUNT.WR,L1D.REPLACEMENT,L2_L1D_WB_RQSTS.ALL,L2_L1D_WB_RQSTS.MISS,L2_LINES_IN.ALL,L2_TRANS.L2_WB,SQ_MISC.FILL_DROPPED"
	resource_counters="RESOURCE_STALLS.ANY,RESOURCE_STALLS.RS,RESOURCE_STALLS.LB,RESOURCE_STALLS.SB,RESOURCE_STALLS.OOO_RSRC,RESOURCE_STALLS2.ALL_PRF_CONTROL,RESOURCE_STALLS2.LOAD_MATRIX,RESOURCE_STALLS.ROB,RESOURCE_STALLS2.PHT_FULL,RESOURCE_STALLS.MEM_RS,RESOURCE_STALLS.LB_SB,RESOURCE_STALLS.FPCW,RESOURCE_STALLS2.OOO_RSRC,RESOURCE_STALLS.OTHER,RESOURCE_STALLS.MXCSR"
 	energy_counters="FREERUN_PKG_ENERGY_STATUS,FREERUN_CORE_ENERGY_STATUS"
	other_counters="${energy_counters},L2_RQSTS.PF_MISS,IDQ_UOPS_NOT_DELIVERED.CORE,INT_MISC.RECOVERY_CYCLES,OFFCORE_RESPONSE.STREAMING_STORES.ANY_RESPONSE_0,MEM_LOAD_UOPS_RETIRED.L1_HIT,MEM_LOAD_UOPS_RETIRED.L2_HIT,L1D_BLOCKS.BANK_CONFLICT_CYCLES"
	uop_issue_retire_counters="UOPS_RETIRED.RETIRE_SLOTS,UOPS_ISSUED.ANY,UOPS_RETIRED.ALL"

	;;


#    "HASWELL")
    "haswell"|"haswell_server"|"crystalwell")
	topdown_mem_counters="CYCLE_ACTIVITY.STALLS_LDM_PENDING,CYCLE_ACTIVITY.STALLS_L1D_PENDING,CYCLE_ACTIVITY.STALLS_L2_PENDING,MEM_LOAD_UOPS_RETIRED.L3_HIT,MEM_LOAD_UOPS_RETIRED.L3_MISS"
	mem_hit_counters+=",MEM_LOAD_UOPS_RETIRED.L3_HIT,MEM_LOAD_UOPS_RETIRED.L3_MISS"
	mem_traffic_counters="L1D.REPLACEMENT,L2_DEMAND_RQSTS.WB_HIT,L2_TRANS.L1D_WB,L2_DEMAND_RQSTS.WB_MISS,L2_LINES_IN.ALL,L2_TRANS.L2_WB,SQ_MISC.FILL_DROPPED,L2_RQSTS.MISS"

	resource_counters="RESOURCE_STALLS.ANY,RESOURCE_STALLS.RS,RESOURCE_STALLS.LB,RESOURCE_STALLS.SB,RESOURCE_STALLS.OOO_RSRC,RESOURCE_STALLS2.ALL_PRF_CONTROL,RESOURCE_STALLS.LOAD_MATRIX,RESOURCE_STALLS.ROB,RESOURCE_STALLS2.PHT_FULL,RESOURCE_STALLS.MEM_RS,RESOURCE_STALLS.LB_SB,RESOURCE_STALLS.FPCW_OR_MXCSR,RESOURCE_STALLS.OTHER"
	#	  tlb_counters="DTLB_LOAD_MISSES.MISS_CAUSES_A_WALK,DTLB_LOAD_MISSES.STLB_HIT,DTLB_STORE_MISSES.MISS_CAUSES_A_WALK,DTLB_STORE_MISSES.STLB_HIT"
	#	  tlb_counters="DTLB_LOAD_MISSES.MISS_CAUSES_A_WALK,DTLB_LOAD_MISSES.STLB_HIT,DTLB_STORE_MISSES.MISS_CAUSES_A_WALK,DTLB_STORE_MISSES.STLB_HIT,DTLB_LOAD_MISSES.WALK_DURATION,DTLB_STORE_MISSES.WALK_DURATION"
	energy_counters="UNC_PP0_ENERGY_STATUS,UNC_PKG_ENERGY_STATUS"
	other_counters="${energy_counters},IDQ_UOPS_NOT_DELIVERED.CORE,INT_MISC.RECOVERY_CYCLES,MEM_LOAD_UOPS_RETIRED.L1_HIT,MEM_LOAD_UOPS_RETIRED.L2_HIT"
	uop_issue_retire_counters="UOPS_RETIRED.RETIRE_SLOTS,UOPS_ISSUED.ANY,UOPS_RETIRED.ALL"
	topdown_port_counters+=",UOPS_DISPATCHED_PORT.PORT_6,UOPS_DISPATCHED_PORT.PORT_7"

	case "$emon_db" in
	    haswell_server)
		mem_traffic_counters+=",UNC_M_CAS_COUNT.RD,UNC_M_CAS_COUNT.WR"
		mem_rowbuff_counters="UNC_M_ACT_COUNT.RD,UNC_M_ACT_COUNT.WR,UNC_M_PRE_COUNT.PAGE_MISS,UNC_M_PRE_COUNT.WR,UNC_M_PRE_COUNT.RD"
		energy_counters="FREERUN_PKG_ENERGY_STATUS,FREERUN_CORE_ENERGY_STATUS,FREERUN_DRAM_ENERGY_STATUS"
		;;

	    crystalwell)
		# Fall through to default for DRAM traffic
		mem_traffic_counters+=",UNC_L4_REQUEST.RD_HIT,UNC_L4_REQUEST.WR_HIT,UNC_L4_REQUEST.WR_FILL,UNC_L4_REQUEST.RD_EVICT_LINE_TO_DRAM,UNC_CBO_L4_SUPERLINE.ALLOC_FAIL"
		;&
	    *)
		mem_traffic_counters+=",UNC_IMC_DRAM_DATA_READS,UNC_IMC_DRAM_DATA_WRITES"
		mem_rowbuff_counters=""  # no rowbuff counters
		energy_counters="UNC_PKG_ENERGY_STATUS,UNC_PP0_ENERGY_STATUS,UNC_PP1_ENERGY_STATUS"
		;;
	esac
	topdown_BE_MEM_L2="CYCLE_ACTIVITY.STALLS_L1D_PENDING,CYCLE_ACTIVITY.STALLS_L2_PENDING"
	topdown_BE_CORE_DIV="ARITH.DIVIDER_UOPS"
      	;;
    "skylake_server")
	topdown_mem_counters="CYCLE_ACTIVITY.STALLS_MEM_ANY,CYCLE_ACTIVITY.STALLS_L1D_MISS,CYCLE_ACTIVITY.STALLS_L2_MISS,CYCLE_ACTIVITY.STALLS_L3_MISS"
        mem_hit_counters="MEM_LOAD_RETIRED.L1_HIT,MEM_LOAD_RETIRED.L1_MISS,MEM_LOAD_RETIRED.FB_HIT,MEM_LOAD_RETIRED.L2_HIT,MEM_INST_RETIRED.ALL_LOADS,MEM_INST_RETIRED.ALL_STORES"
	mem_hit_counters+=",MEM_LOAD_RETIRED.L3_HIT,MEM_LOAD_RETIRED.L3_MISS"
	mem_traffic_counters="L1D.REPLACEMENT,L2_TRANS.L1D_WB,L2_LINES_IN.ALL,L2_TRANS.L2_WB,SQ_MISC.FILL_DROPPED,L2_RQSTS.MISS"
	mem_traffic_counters+=",IDI_MISC.WB_UPGRADE,IDI_MISC.WB_DOWNGRADE,UNC_M_CAS_COUNT.RD,UNC_M_CAS_COUNT.WR"
	resource_counters="RESOURCE_STALLS.ANY,RESOURCE_STALLS.SB"
	#	  tlb_counters="DTLB_LOAD_MISSES.MISS_CAUSES_A_WALK,DTLB_LOAD_MISSES.STLB_HIT,DTLB_STORE_MISSES.MISS_CAUSES_A_WALK,DTLB_STORE_MISSES.STLB_HIT"
	#	  tlb_counters="DTLB_LOAD_MISSES.MISS_CAUSES_A_WALK,DTLB_LOAD_MISSES.STLB_HIT,DTLB_STORE_MISSES.MISS_CAUSES_A_WALK,DTLB_STORE_MISSES.STLB_HIT,DTLB_LOAD_MISSES.WALK_PENDING,DTLB_STORE_MISSES.WALK_PENDING"
	tlb_counters="DTLB_LOAD_MISSES.MISS_CAUSES_A_WALK,DTLB_LOAD_MISSES.STLB_HIT,DTLB_STORE_MISSES.MISS_CAUSES_A_WALK,DTLB_STORE_MISSES.STLB_HIT,DTLB_LOAD_MISSES.WALK_PENDING,DTLB_STORE_MISSES.WALK_PENDING"
	energy_counters="FREERUN_PKG_ENERGY_STATUS,FREERUN_CORE_ENERGY_STATUS,FREERUN_DRAM_ENERGY_STATUS,STATIC_CORE_THERMAL_STATUS"
	other_counters="${energy_counters},IDQ_UOPS_NOT_DELIVERED.CORE,INT_MISC.RECOVERY_CYCLES,MEM_LOAD_UOPS_RETIRED.L1_HIT,MEM_LOAD_UOPS_RETIRED.L2_HIT"
	uop_issue_retire_counters="UOPS_RETIRED.RETIRE_SLOTS,UOPS_ISSUED.ANY,UOPS_RETIRED.ALL"
	topdown_port_counters+=",UOPS_DISPATCHED_PORT.PORT_6,UOPS_DISPATCHED_PORT.PORT_7"

	topdown_info_mem_Load_Miss_Real_Latency="L1D_PEND_MISS.PENDING,MEM_LOAD_RETIRED.L1_MISS,MEM_LOAD_RETIRED.FB_HIT"
	topdown_BE_MEM_L1_FB="${topdown_info_mem_Load_Miss_Real_Latency},L1D_PEND_MISS.FB_FULL:c1"
	topdown_aux_load_l1_miss="MEM_LOAD_RETIRED.L2_HIT,MEM_LOAD_RETIRED.L3_HIT,MEM_LOAD_L3_HIT_RETIRED.XSNP_HIT,MEM_LOAD_L3_HIT_RETIRED.XSNP_HITM,MEM_LOAD_L3_HIT_RETIRED.XSNP_MISS"
	topdown_aux_load_l1_miss_net="${topdown_aux_load_l1_miss},MEM_LOAD_RETIRED.L3_MISS"
	topdown_aux_load_l2_hit="MEM_LOAD_RETIRED.L2_HIT,MEM_LOAD_RETIRED.FB_HIT,${topdown_aux_load_l1_miss_net}"
	topdown_aux_L2_Bound_Ratio="CYCLE_ACTIVITY.STALLS_L1D_MISS,CYCLE_ACTIVITY.STALLS_L2_MISS"
	topdown_BE_MEM_L2="${topdown_BE_MEM_L1_FB},${topdown_aux_load_l2_hit},L1D_PEND_MISS.FB_FULL:c1,${topdown_aux_L2_Bound_Ratio}"
	topdown_BE_MEM_L3="CYCLE_ACTIVITY.STALLS_L2_MISS,CYCLE_ACTIVITY.STALLS_L3_MISS"
	topdown_aux_Mem_Bound_Ratio="CYCLE_ACTIVITY.STALLS_L3_MISS,${topdown_aux_L2_Bound_Ratio},${topdown_BE_MEM_L2}"
	topdown_BE_MEM_DRAM="${topdown_aux_Mem_Bound_Ratio}"
	topdown_BE_MEM_STOR="EXE_ACTIVITY.BOUND_ON_STORES"
	topdown_aux_Few_Uops_Executed_Threshold="EXE_ACTIVITY.2_PORTS_UTIL"
	topdown_aux_Backend_Bound_Cycles="EXE_ACTIVITY.EXE_BOUND_0_PORTS,EXE_ACTIVITY.1_PORTS_UTIL,${topdown_aux_Few_Uops_Executed_Threshold},CYCLE_ACTIVITY.STALLS_MEM_ANY,EXE_ACTIVITY.BOUND_ON_STORES"
	topdown_aux_Memory_Bound_Fraction="CYCLE_ACTIVITY.STALLS_MEM_ANY,EXE_ACTIVITY.BOUND_ON_STORES,${topdown_aux_Backend_Bound_Cycles}"
	topdown_BE_CORE_DIV="ARITH.DIVIDER_ACTIVE"
	topdown_BE_CORE_PORT="${topdown_aux_Backend_Bound_Cycles},CYCLE_ACTIVITY.STALLS_MEM_ANY,EXE_ACTIVITY.BOUND_ON_STORES,ARITH.DIVIDER_ACTIVE,EXE_ACTIVITY.EXE_BOUND_0_PORTS"
        ;;

# Below need to first upgrade EMON to v10.0.0 to work
#    "IVY_BRIDGE")
	"ivybridge")
	topdown_mem_counters="CYCLE_ACTIVITY.STALLS_LDM_PENDING,CYCLE_ACTIVITY.STALLS_L1D_PENDING,CYCLE_ACTIVITY.STALLS_L2_PENDING,MEM_LOAD_UOPS_RETIRED.LLC_HIT_PS,MEM_LOAD_UOPS_RETIRED.LLC_MISS_PS"
	mem_hit_counters+=",MEM_LOAD_UOPS_RETIRED.LLC_HIT,MEM_LOAD_UOPS_RETIRED.LLC_MISS"
	mem_traffic_counters="UNC_M_CAS_COUNT.RD,UNC_M_CAS_COUNT.WR,L1D.REPLACEMENT,L2_L1D_WB_RQSTS.ALL,L2_L1D_WB_RQSTS.MISS,L2_LINES_IN.ALL,L2_TRANS.L2_WB,SQ_MISC.FILL_DROPPED"
	resource_counters="RESOURCE_STALLS.ANY,RESOURCE_STALLS.RS,RESOURCE_STALLS.LB,RESOURCE_STALLS.SB,RESOURCE_STALLS.OOO_RSRC,RESOURCE_STALLS2.ALL_PRF_CONTROL,RESOURCE_STALLS.LOAD_MATRIX,RESOURCE_STALLS.ROB,RESOURCE_STALLS2.PHT_FULL,RESOURCE_STALLS.MEM_RS,RESOURCE_STALLS.LB_SB,RESOURCE_STALLS.FPCW,RESOURCE_STALLS2.OOO_RSRC,RESOURCE_STALLS.MXCSR"
	other_counters="L2_RQSTS.PF_MISS,IDQ_UOPS_NOT_DELIVERED.CORE,INT_MISC.RECOVERY_CYCLES,OFFCORE_RESPONSE.STREAMING_STORES.ANY_RESPONSE_0"
	uop_issue_retire_counters="UOPS_RETIRED.RETIRE_SLOTS,UOPS_ISSUED.ANY,UOPS_RETIRED.ALL"
	energy_counters="UNC_PACKAGE_ENERGY_STATUS"
	topdown_BE_MEM_L2="CYCLE_ACTIVITY.STALLS_L1D_PENDING,CYCLE_ACTIVITY.STALLS_L2_PENDING"
      	;;

    *)
	topdown_mem_counters="CYCLE_ACTIVITY.STALLS_LDM_PENDING,CYCLE_ACTIVITY.STALLS_L1D_PENDING,CYCLE_ACTIVITY.STALLS_L2_PENDING,MEM_LOAD_UOPS_RETIRED.LLC_HIT_PS,MEM_LOAD_UOPS_RETIRED.LLC_MISS_PS"
	# the basic counter is slightly different 'INST_RETIRED.ANY_P', redefine it
	basic_counters="INST_RETIRED.ANY_P,CPU_CLK_UNHALTED.CORE,CPU_CLK_UNHALTED.REF_TSC"
	mem_traffic_counters="LONGEST_LAT_CACHE.MISS,OFFCORE_RESPONSE:request=COREWB:response=L2_MISS.NO_SNOOP_NEEDED,OFFCORE_RESPONSE:request=COREWB:response=L2_HIT,MEM_UOPS_RETIRED.L1_MISS_LOADS,OFFCORE_RESPONSE:request=PF_L1_DATA_RD:response=ANY_RESPONSE,OFFCORE_RESPONSE:request=DEMAND_RFO:response=ANY_RESPONSE,OFFCORE_RESPONSE:request=DEMAND_DATA_RD:response=ANY_RESPONSE,OFFCORE_RESPONSE:request=COREWB:response=ANY_RESPONSE"
	tlb_counters=""
	resource_counters=""
	other_counters="CYCLES_DIV_BUSY.ALL,UOPS_RETIRED.ALL,NO_ALLOC_CYCLES.ROB_FULL,NO_ALLOC_CYCLES.RAT_STALL,NO_ALLOC_CYCLES.NOT_DELIVERED,NO_ALLOC_CYCLES.ALL,RS_FULL_STALL.MEC,RS_FULL_STALL.ALL,REHABQ.STA_FULL,REHABQ.ANY_LD,REHABQ.ANY_ST,MEM_UOPS_RETIRED.L2_HIT_LOADS,MEM_UOPS_RETIRED.L2_MISS_LOADS,PAGE_WALKS.D_SIDE_WALKS,PAGE_WALKS.D_SIDE_CYCLES,MS_DECODED.MS_ENTRY"

	;;
esac




#if [[ "$UARCH" == "SANDY_BRIDGE" ]]
if [[ "$emon_db" == "SANDY_BRIDGE" ]]; then
    topdown_exe_counters+=",CYCLE_ACTIVITY.NO_DISPATCH,UOPS_DISPATCHED.THREAD"
elif [[ "$emon_db" == "skylake_server" ]]; then
    topdown_exe_counters+=",CYCLE_ACTIVITY.STALLS_TOTAL,UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC,UOPS_EXECUTED.CYCLES_GE_2_UOPS_EXEC,UOPS_EXECUTED.CYCLES_GE_3_UOPS_EXEC,UOPS_EXECUTED.CYCLES_GE_4_UOPS_EXEC"
else
    topdown_exe_counters+=",CYCLE_ACTIVITY.CYCLES_NO_EXECUTE,UOPS_EXECUTED.CYCLES_GE_1_UOP_EXEC,UOPS_EXECUTED.CYCLES_GE_2_UOPS_EXEC,UOPS_EXECUTED.CYCLES_GE_3_UOPS_EXEC,UOPS_EXECUTED.CYCLES_GE_4_UOPS_EXEC"
fi

topdown_port_util_counters="${topdown_port_counters},ARITH.FPU_DIV_ACTIVE"
topdown_counters="${topdown_ms_seq_counters},${topdown_exe_counters},${topdown_mem_counters},${topdown_unc_counters},${topdown_port_util_counters}"


topdown_BE_MEM="${topdown_BE},${topdown_aux_Memory_Bound_Fraction}"

topdown_BE_CORE="${topdown_BE},${topdown_BE_MEM}"

topdown_set="${topdown_FE},${topdown_BADS},${topdown_BE},${topdown_RETR}"
topdown_FE_set="${topdown_FE_LAT},${topdown_FE_BW}"
topdown_BADS_set="${topdown_BADS_BR},${topdown_BADS_MCLR}"
topdown_BE_set="${topdown_BE_MEM},${topdown_BE_CORE}"
topdown_BE_MEM_set="${topdown_MEM_L1},${topdown_MEM_L2},${topdown_MEM_L3},${topdown_MEM_DRAM},${topdown_MEM_STOR}"
topdown_BE_CORE_set="${topdown_CORE_DIV},${topdown_CORE_PORT}"
topdown_RETR_set="${topdown_RETR_BASE},${topdown_RETR_MSEQ}"


emon_counters="${basic_counters}"
#append_counters $ACTIVATE_MEM_TRAFFIC_COUNTERS "traffic" ${mem_traffic_counters}
append_counters "${activateCtrs[MEM_TRAFFIC]}" "traffic" ${mem_traffic_counters}
#append_counters $ACTIVATE_MEM_HIT_COUNTERS "memhit" ${mem_hit_counters}
append_counters "${activateCtrs[MEM_HIT]}" "memhit" ${mem_hit_counters}
#append_counters $ACTIVATE_MEM_ROWBUFF_COUNTERS "rowbuff" ${mem_rowbuff_counters}
append_counters "${activateCtrs[MEM_ROWBUFF]}" "rowbuff" ${mem_rowbuff_counters}
#append_counters $ACTIVATE_RESOURCE_COUNTERS "resource" ${resource_counters}
append_counters "${activateCtrs[RESOURCE]}" "resource" ${resource_counters}
#append_counters $ACTIVATE_TLB_COUNTERS "TLB" ${tlb_counters}
append_counters "${activateCtrs[TLB]}" "TLB" ${tlb_counters}
#append_counters $ACTIVATE_SQ_COUNTERS "SuperQ" ${sq_counters}
append_counters "${activateCtrs[SQ]}" "SuperQ" ${sq_counters}
#append_counters $ACTIVATE_SQ_HISTOGRAM_COUNTERS "SqHisto" ${sq_histogram_counters}
append_counters "${activateCtrs[SQ_HISTOGRAM]}" "SqHisto" ${sq_histogram_counters}

#append_counters $ACTIVATE_LFB_COUNTERS "Lfb" ${lfb_counters}
append_counters "${activateCtrs[LFB]}" "Lfb" ${lfb_counters}
#append_counters $ACTIVATE_LFB_HISTOGRAM_COUNTERS "LfbHisto" ${lfb_histogram_counters}
append_counters "${activateCtrs[LFB_HISTOGRAM]}" "LfbHisto" ${lfb_histogram_counters}

#append_counters $ACTIVATE_TOPDOWN_COUNTERS "TopDown" ${topdown_counters}
append_counters "${activateCtrs[TOPDOWN]}" "TopDown" ${topdown_counters}
#append_counters $ACTIVATE_TOPDOWN_FP_ARITH_COUNTERS "TopDownFp" ${topdown_fp_arith_counters}
append_counters "${activateCtrs[TOPDOWN_FP_ARITH]}" "TopDownFp" ${topdown_fp_arith_counters}
#append_counters $ACTIVATE_TOPDOWN_FE_LAT_COUNTERS "TopDownFeLat" ${topdown_fe_lat_counters}
append_counters "${activateCtrs[TOPDOWN_FE_LAT]}" "TopDownFeLat" ${topdown_fe_lat_counters}

append_counters "${activateCtrs[TOPDOWN_SET]}" "TopDownSet" ${topdown_set}
append_counters "${activateCtrs[TOPDOWN_FE_SET]}" "TopDownFeSet" ${topdown_FE_set}
append_counters "${activateCtrs[TOPDOWN_BADS_SET]}" "TopDownBadsSet" ${topdown_BADS_set}
append_counters "${activateCtrs[TOPDOWN_BE_SET]}" "TopDownBeSet" ${topdown_BE_set}
append_counters "${activateCtrs[TOPDOWN_BE_MEM_SET]}" "TopDownBeMemSet" ${topdown_BE_MEM_set}
append_counters "${activateCtrs[TOPDOWN_BE_CORE_SET]}" "TopDownBeCoreSet" ${topdown_BE_CORE_set}


# append_counters $ACTIVATE_LIFE_COUNTERS "LifeCounts" ${l3_hit_rate_check_counters}
# append_counters $ACTIVATE_LIFE_COUNTERS "LifeCounts" ${irq_life_counters}
# append_counters $ACTIVATE_LIFE_COUNTERS "LifeCounts" ${tor_life_counters}
# append_counters $ACTIVATE_LIFE_COUNTERS "LifeCounts" ${egr_ad_life_counters}
# append_counters $ACTIVATE_LIFE_COUNTERS "LifeCounts" ${egr_bl_life_counters}
# append_counters $ACTIVATE_OTHER_COUNTERS "OtherCounts" ${other_counters}
# append_counters $ACTIVATE_ENERGY_COUNTERS "EnergyCounts" ${energy_counters}
# append_counters $ACTIVATE_UOP_ISSUE_RETIRE_COUNTERS "UopIssueRetireCounts" ${uop_issue_retire_counters}
# append_counters $ACTIVATE_BRANCH_COUNTERS "BranchCounts" ${branch_counters}
# append_counters $ACTIVATE_LSD_COUNTERS "LsdCounts" ${lsd_counters}

append_counters "${activateCtrs[LIFE]}" "LifeCounts" ${l3_hit_rate_check_counters}
append_counters "${activateCtrs[LIFE]}" "LifeCounts" ${irq_life_counters}
append_counters "${activateCtrs[LIFE]}" "LifeCounts" ${tor_life_counters}
append_counters "${activateCtrs[LIFE]}" "LifeCounts" ${egr_ad_life_counters}
append_counters "${activateCtrs[LIFE]}" "LifeCounts" ${egr_bl_life_counters}
append_counters "${activateCtrs[OTHER]}" "OtherCounts" ${other_counters}
append_counters "${activateCtrs[ENERGY]}" "EnergyCounts" ${energy_counters}
append_counters "${activateCtrs[UOP_ISSUE_RETIRE]}" "UopIssueRetireCounts" ${uop_issue_retire_counters}
append_counters "${activateCtrs[BRANCH]}" "BranchCounts" ${branch_counters}
append_counters "${activateCtrs[LSD]}" "LsdCounts" ${lsd_counters}


#      emon_counters+=",${other_counters}"




# Add more counters for advance counter choice
if [[ "$ACTIVATE_ADVANCED_COUNTERS" != "0" ]]
then
    case "$UARCH" in
	"SANDY_BRIDGE")

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

# output emon counter and remove redundant ones
#echo "FINAL COUNTERS: ${emon_counters}"
echo ${emon_counters}|sed 's/,/\n/g' |sort|uniq|sed -z 's/^\n//g'|sed -z 's/\n/,/g'|sed 's/,$//g'
#echo ${emon_counters}

