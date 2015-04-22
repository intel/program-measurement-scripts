#!/bin/bash

declare -A pcr_metrics

pcr_metrics["CPI"]="CPI_D"
pcr_metrics["CPU_CLK_UNHALTED_REF"]="CPU_CLK_UNHALTED_REF_P_ND"
pcr_metrics["CAS_COUNT_RD"]="CAS_COUNT_RD_ND"
pcr_metrics["CAS_COUNT_WR"]="CAS_COUNT_WR_ND"
pcr_metrics["INSTR_RETIRED_ANY"]="INST_RETIRED_ND"
pcr_metrics["L1D_REPLACEMENT"]="L1D_REPLACEMENT_ND"
pcr_metrics["L1D_WB_RQST_ALL"]="L1D_WB_RQST_ALL_ND"
pcr_metrics["L1D_WB_RQST_MISS"]="L1D_WB_RQST_MISS_ND"
pcr_metrics["L2_LINES_IN_ALL"]="L2_LINES_IN_ANY_ND"
pcr_metrics["L2_TRANS_L2_WB"]="L2_TRANS_L2_WB_ND"
pcr_metrics["L3_LAT_CACHE_MISS"]="L3_LAT_CACHE_MISS_ND"
pcr_metrics["MEMLOAD_UOPS_RETIRED_HIT_LFB"]="MEM_LOAD_UOPS_RETIRED_HIT_LFB_ND"
pcr_metrics["MEMLOAD_UOPS_RETIRED_L1_HIT"]="MEM_LOAD_UOPS_RETIRED_L1_HIT_ND"
pcr_metrics["MEMLOAD_UOPS_RETIRED_L2_HIT"]="MEM_LOAD_UOPS_RETIRED_L2_HIT_ND"
pcr_metrics["MEMLOAD_UOPS_RETIRED_LLC_HIT"]="MEM_LOAD_UOPS_RETIRED_L3_HIT_ND"
pcr_metrics["MEMLOAD_UOPS_RETIRED_LLC_MISS"]="MEM_LOAD_UOPS_RETIRED_L3_MISS_ND"
pcr_metrics["SQ_MISC_FILL_DROPPED"]="SQ_MISC_FILL_DROPPED_ND"
pcr_metrics["CPU_CLK_UNHALTED_CORE"]="CPU_CLK_UNHALTED_CORE_P_ND"

pcr_metrics["OFFCORE_REQUESTS_DEMAND_DATA_RD"]="OFFCORE_REQUESTS_DEMAND_DATA_RD_ND"
pcr_metrics["OFFCORE_REQUESTS_BUFFER_SQ_FULL"]="OFFCORE_REQUESTS_BUFFER_SQ_FULL_ND"
pcr_metrics["RESOURCE_STALLS2_ALL_FL_EMPTY"]="RESOURCE_STALLS2_ALL_FL_EMPTY_ND"
pcr_metrics["RESOURCE_STALLS2_ALL_PRF_CONTROL"]="RESOURCE_STALLS2_ALL_PRF_CONTROL_ND"
pcr_metrics["RESOURCE_STALLS_ROB"]="RESOURCE_STALLS_ROB_ND"
pcr_metrics["RESOURCE_STALLS_LB"]="RESOURCE_STALLS_LB_ND"
pcr_metrics["RESOURCE_STALLS_RS"]="RESOURCE_STALLS_RS_ND"
pcr_metrics["RESOURCE_STALLS2_OOO_RSRC"]="RESOURCE_STALLS2_OOO_RSRC_ND"
pcr_metrics["UOPS_DISPATCHED_PORT_PORT_0"]="UOPS_DISPATCHED_PORT_PORT_0_ND"
pcr_metrics["UOPS_DISPATCHED_PORT_PORT_1"]="UOPS_DISPATCHED_PORT_PORT_1_ND"
pcr_metrics["UOPS_DISPATCHED_PORT_PORT_2"]="UOPS_DISPATCHED_PORT_PORT_2_ND"
pcr_metrics["UOPS_DISPATCHED_PORT_PORT_3"]="UOPS_DISPATCHED_PORT_PORT_3_ND"
pcr_metrics["UOPS_DISPATCHED_PORT_PORT_4"]="UOPS_DISPATCHED_PORT_PORT_4_ND"
pcr_metrics["UOPS_DISPATCHED_PORT_PORT_5"]="UOPS_DISPATCHED_PORT_PORT_5_ND"
pcr_metrics["RESOURCE_STALLS_B"]="RESOURCE_STALLS_B_ND"
pcr_metrics["RESOURCE_STALLS_FCSW"]="RESOURCE_STALLS_FCSW_ND"
pcr_metrics["RESOURCE_STALLS_MXCSR"]="RESOURCE_STALLS_MXCSR_ND"
pcr_metrics["RESOURCE_STALLS_OTHER"]="RESOURCE_STALLS_OTHER_ND"
pcr_metrics["MISALIGN_MEM_REF_LOAD"]="MISALIGN_MEM_REF_LOAD_ND"
pcr_metrics["MISALIGN_MEM_REF_STORE"]="MISALIGN_MEM_REF_STORE_ND"
pcr_metrics["RESOURCE_STALLS_ANY"]="RESOURCE_STALLS_ANY_ND"
pcr_metrics["UOPS_RETIRED_ALL"]="UOPS_RETIRED_ALL_ND"
pcr_metrics["IDQ_MITE_UOPS"]="IDQ_MITE_UOPS_ND"
pcr_metrics["IDQ_DSB_UOPS"]="IDQ_DSB_UOPS_ND"
pcr_metrics["IDQ_MS_UOPS"]="IDQ_MS_UOPS_ND"
pcr_metrics["IDQ_UOPS_NOT_DELIVERED_CORE"]="IDQ_UOPS_NOT_DELIVERED_CORE_ND"
pcr_metrics["PARTIAL_RAT_STALLS_FLAGS_MERGE_UOP"]="PARTIAL_RAT_STALLS_FLAGS_MERGE_UOP_ND"
pcr_metrics["PARTIAL_RAT_STALLS_SLOW_LEA_WINDOW"]="PARTIAL_RAT_STALLS_SLOW_LEA_WINDOW_ND"
pcr_metrics["UOPS_ISSUED_ANY"]="UOPS_ISSUED_ANY_ND"
pcr_metrics["RESOURCE_STALLS2_BOB_FULL"]="RESOURCE_STALLS2_BOB_FULL_ND"
pcr_metrics["PARTIAL_RAT_STALLS_MUL_SINGLE_UOP"]="PARTIAL_RAT_STALLS_MUL_SINGLE_UOP_ND"
pcr_metrics["DTLB_LOAD_MISSES_CAUSES_A_WALK"]="DTLB_LOAD_MISSES_CAUSES_A_WALK_ND"
pcr_metrics["DTLB_STORE_MISSES_MISS_CAUSES_A_WALK"]="DTLB_STORE_MISSES_MISS_CAUSES_A_WALK_ND"

pcr_metrics["ARITH_FPU_DIV_ACTIVE"]="FPU_DIV_ACTIVE_ND"
pcr_metrics["IDQ_UOPS_NOT_DELIVERED_CORE"]="IDQ_UOPS_NOT_DELIVERED_CORE_ND"
pcr_metrics["MEM_LOAD_UOPS_RETIRED_HIT_LFB"]="MEM_LOAD_UOPS_RETIRED_HIT_LFB_ND"
pcr_metrics["MEM_TRANS_RETIRED_LOAD_LATENCY_GT_4"]="LATENCY_ABOVE_THRESHOLD_4_ND"
pcr_metrics["MEM_LOAD_UOPS_RETIRED_L1_HIT"]="MEM_LOAD_UOPS_RETIRED_L1_HIT_ND"
pcr_metrics["MEM_LOAD_UOPS_RETIRED_L2_HIT"]="MEM_LOAD_UOPS_RETIRED_L2_HIT_ND"
pcr_metrics["MEM_LOAD_UOPS_RETIRED_LLC_HIT"]="MEM_LOAD_UOPS_RETIRED_L3_HIT_ND"
pcr_metrics["MEM_TRANS_RETIRED_LOAD_LATENCY_GT_8"]="LATENCY_ABOVE_THRESHOLD_8_ND"
pcr_metrics["L1D_PEND_MISS_PENDING"]="L1D_PEND_MISS_ND"
pcr_metrics["MISALIGN_MEM_REF_LOADS"]="MISALIGN_MEM_REF_LOAD_ND"
pcr_metrics["MISALIGN_MEM_REF_STORES"]="MISALIGN_MEM_REF_STORE_ND"
pcr_metrics["MEM_TRANS_RETIRED_LOAD_LATENCY_GT_16"]="LATENCY_ABOVE_THRESHOLD_16_ND"
pcr_metrics["OFFCORE_REQUESTS_BUFFER_SQ_FULL"]="OFFCORE_REQUESTS_BUFFER_SQ_FULL_ND"
pcr_metrics["OFFCORE_REQUESTS_OUTSTANDING_DEMAND_DATA_RD"]="OFFCORE_REQUESTS_DEMAND_DATA_RD_ND"
pcr_metrics["L1D_REPLACEMENT"]="L1D_REPLACEMENT_ND"
pcr_metrics["MEM_TRANS_RETIRED_LOAD_LATENCY_GT_32"]="LATENCY_ABOVE_THRESHOLD_32_ND"
pcr_metrics["L2_L1D_WB_RQSTS_ALL"]="L1D_WB_RQST_ALL_ND"
pcr_metrics["L2_L1D_WB_RQSTS_MISS"]="L1D_WB_RQST_MISS_ND"
pcr_metrics["L2_LINES_IN_ALL"]="L2_LINES_IN_ANY_ND"
pcr_metrics["MEM_TRANS_RETIRED_LOAD_LATENCY_GT_64"]="LATENCY_ABOVE_THRESHOLD_64_ND"
pcr_metrics["L2_TRANS_L2_WB"]="L2_TRANS_L2_WB_ND"
pcr_metrics["SQ_MISC_FILL_DROPPED"]="SQ_MISC_FILL_DROPPED_ND"
pcr_metrics["UNC_M_CAS_COUNT_RD"]="CAS_COUNT_RD_ND"
pcr_metrics["UNC_M_CAS_COUNT_WR"]="CAS_COUNT_WR_ND"
pcr_metrics["MEM_TRANS_RETIRED_LOAD_LATENCY_GT_128"]="LATENCY_ABOVE_THRESHOLD_128_ND"
pcr_metrics["L1D_STALL_FOR_REPLACE_CORE"]="L1D_BAD1_ND"
pcr_metrics["L1D_BLOCKS_FB_BLOCK"]="L1D_BAD2_ND"
pcr_metrics["L1D_PEND_MISS_REQUEST_FB_FULL"]="L1D_BAD3_ND"
pcr_metrics["MEM_TRANS_RETIRED_LOAD_LATENCY_GT_256"]="LATENCY_ABOVE_THRESHOLD_256_ND"
pcr_metrics["L1D_PEND_MISS_SS_FB_FULL"]="L1D_BAD4_ND"
pcr_metrics["RESOURCE_STALLS_ANY"]="RESOURCE_STALLS_ANY_ND"
pcr_metrics["RESOURCE_STALLS_FPCW"]="RESOURCE_STALLS_FCSW_ND"
pcr_metrics["RESOURCE_STALLS_LB"]="RESOURCE_STALLS_LB_ND"
pcr_metrics["MEM_TRANS_RETIRED_LOAD_LATENCY_GT_512"]="LATENCY_ABOVE_THRESHOLD_512_ND"
pcr_metrics["RESOURCE_STALLS_MXCSR"]="RESOURCE_STALLS_MXCSR_ND"
pcr_metrics["RESOURCE_STALLS_OTHER"]="RESOURCE_STALLS_OTHER_ND"
pcr_metrics["RESOURCE_STALLS_ROB"]="RESOURCE_STALLS_ROB_ND"
pcr_metrics["RESOURCE_STALLS_RS"]="RESOURCE_STALLS_RS_ND"
pcr_metrics["RESOURCE_STALLS_SB"]="RESOURCE_STALLS_SB_ND"
pcr_metrics["RESOURCE_STALLS2_ALL_PRF_CONTROL"]="RESOURCE_STALLS2_ALL_PRF_CONTROL_ND"
pcr_metrics["RESOURCE_STALLS2_BOB_FULL"]="RESOURCE_STALLS2_BOB_FULL_ND"
pcr_metrics["RESOURCE_STALLS2_LOAD_MATRIX"]="STALLS_BAD1_ND"
pcr_metrics["RESOURCE_STALLS2_PHT_FULL"]="STALLS_BAD2_ND"
pcr_metrics["RESOURCE_STALLS2_PRRT_FULL"]="STALLS_BAD3_ND"
pcr_metrics["UOPS_DISPATCHED_STALL_CYCLES"]="UOPS_DISPATCHED_STALL_CYCLES_ND"
pcr_metrics["UOPS_ISSUED_STALL_CYCLES"]="UOPS_ISSUED_STALL_CYCLES_ND"
pcr_metrics["UOPS_RETIRED_STALL_CYCLES"]="UOPS_RETIRED_STALL_CYCLES_ND"
pcr_metrics["IDQ_ALL_DSB_CYCLES_ANY_UOPS"]="IDQ_DSB_UOPS_ND"
pcr_metrics["INST_RETIRED_ANY"]="INST_RETIRED_ND"
pcr_metrics["UOPS_DISPATCHED_CANCELLED"]="UOPS_BAD1_ND"
pcr_metrics["UOPS_DISPATCHED_CANCELLED_RS"]="UOPS_BAD2_ND"
pcr_metrics["UOPS_DISPATCHED_THREAD"]="UOPS_DISPATCHED_THREAD_ND"
pcr_metrics["UOPS_DISPATCHED_PORT_PORT_0"]="UOPS_DISPATCHED_PORT_PORT_0_ND"
pcr_metrics["UOPS_DISPATCHED_PORT_PORT_1"]="UOPS_DISPATCHED_PORT_PORT_1_ND"
pcr_metrics["UOPS_DISPATCHED_PORT_PORT_2"]="UOPS_DISPATCHED_PORT_PORT_2_ND"
pcr_metrics["UOPS_DISPATCHED_PORT_PORT_3"]="UOPS_DISPATCHED_PORT_PORT_3_ND"
pcr_metrics["UOPS_DISPATCHED_PORT_PORT_4"]="UOPS_DISPATCHED_PORT_PORT_4_ND"
pcr_metrics["UOPS_DISPATCHED_PORT_PORT_5"]="UOPS_DISPATCHED_PORT_PORT_5_ND"
pcr_metrics["UOPS_ISSUED_ANY"]="UOPS_ISSUED_ANY_ND"
pcr_metrics["UOPS_RETIRED_ALL"]="UOPS_RETIRED_ALL_ND"
pcr_metrics["UOPS_RETIRED_RETIRE_SLOTS"]="UOPS_RETIRED_RETIRE_SLOTS_ND"
pcr_metrics["INT_MISC_RAT_STALL_CYCLES"]="INT_MISC_RAT_STALL_CYCLES_ND"
pcr_metrics["CPU_CLK_UNHALTED_REF_TSC"]="CPU_CLK_UNHALTED_REF_P_ND"
pcr_metrics["CPU_CLK_UNHALTED_THREAD"]="CPU_CLK_UNHALTED_CORE_P_ND"
pcr_metrics["DTLB_LOAD_MISSES_MISS_CAUSES_A_WALK"]="DTLB_LOAD_MISSES_CAUSES_A_WALK_ND"
pcr_metrics["DTLB_LOAD_MISSES_STLB_HIT"]="DTLB_LOAD_MISSES_STLB_HIT_ND"
pcr_metrics["DTLB_STORE_MISSES_MISS_CAUSES_A_WALK"]="DTLB_STORE_MISSES_MISS_CAUSES_A_WALK_ND"
pcr_metrics["DTLB_STORE_MISSES_STLB_HIT"]="DTLB_STORE_MISSES_STLB_HIT_ND"
pcr_metrics["INT_MISC_RECOVERY_CYCLES"]="INT_MISC_RECOVERY_CYCLES_ND"
pcr_metrics["LD_BLOCKS_PARTIAL_ADDRESS_ALIAS"]="LD_BLOCKS_PARTIAL_ADDRESS_ALIAS_ND"
pcr_metrics["LD_BLOCKS_ALL_BLOCK"]="LD_BLOCKS_ALL_BLOCK_ND"
pcr_metrics["UOPS_DISPATCHED_THREAD:u0x3F:c1:i0:e0"]="UOPS_EXECUTED_CYCLES_GE_1_UOP_EXEC_ND"
pcr_metrics["UOPS_DISPATCHED_THREAD:u0x3F:c2:i0:e0"]="UOPS_EXECUTED_CYCLES_GE_2_UOP_EXEC_ND"
pcr_metrics["UOPS_DISPATCHED_THREAD:u0x3F:c4:i0:e0"]="UOPS_EXECUTED_CYCLES_GE_4_UOP_EXEC_ND"
pcr_metrics["FREERUN_PKG_ENERGY_STATUS"]="PWR_PP1_ENERGY_ND"
pcr_metrics["FREERUN_CORE_ENERGY_STATUS"]="PWR_PP0_ENERGY_ND"
pcr_metrics["FREERUN_DRAM_ENERGY_STATUS"]="PWR_DRAM_ENERGY_ND"
pcr_metrics["L2_RQSTS_PF_MISS"]="L2_RQSTS_PF_MISS_ND"
pcr_metrics["OFFCORE_RESPONSE_STREAMING_STORES_ANY_RESPONSE_0"]="NT_STORES_ND"


#Silvermont
pcr_metrics["OFFCORE_RESPONSE:request:COREWB:response:L2_MISS_NO_SNOOP_NEEDED"]="L2_WB_ND"
pcr_metrics["OFFCORE_RESPONSE:request:PF_L1_DATA_RD:response:ANY_RESPONSE"]="L1_PREFETCH_ND"
pcr_metrics["OFFCORE_RESPONSE:request:COREWB:response:L2_HIT"]="NICE_ND"
pcr_metrics["OFFCORE_RESPONSE:request:DEMAND_DATA_RD:response:ANY_RESPONSE"]="DEMAND_RD_ND"
pcr_metrics["OFFCORE_RESPONSE:request:DEMAND_RFO:response:ANY_RESPONSE"]="DEMAND_RFO_ND"
pcr_metrics["OFFCORE_RESPONSE:request:COREWB:response:ANY_RESPONSE"]="ANY_WB_ND"
pcr_metrics["CPU_CLK_UNHALTED_CORE_P"]="CPU_CLK_UNHALTED_CORE_P_ND"
pcr_metrics["CPU_CLK_UNHALTED_REF_P"]="CPU_CLK_UNHALTED_REF_P_ND"
pcr_metrics["CYCLES_DIV_BUSY_ALL"]="CYCLES_DIV_BUSY_ALL_ND"
pcr_metrics["INST_RETIRED_ANY_P"]="INST_RETIRED_ND"
pcr_metrics["LONGEST_LAT_CACHE_MISS"]="LONGEST_LAT_CACHE_MISS_ND"
pcr_metrics["LONGEST_LAT_CACHE_REFERENCE"]="LONGEST_LAT_CACHE_REFERENCE_ND"
pcr_metrics["MEM_UOPS_RETIRED_ALL_LOADS"]="MEM_UOPS_RETIRED_ALL_LOADS_ND"
pcr_metrics["MEM_UOPS_RETIRED_ALL_STORES"]="MEM_UOPS_RETIRED_ALL_STORES_ND"
pcr_metrics["MEM_UOPS_RETIRED_HITM"]="MEM_UOPS_RETIRED_HITM_ND"
pcr_metrics["MEM_UOPS_RETIRED_L1_MISS_LOADS"]="MEM_UOPS_RETIRED_L1_MISS_LOADS_ND"
pcr_metrics["MEM_UOPS_RETIRED_L2_HIT_LOADS"]="MEM_UOPS_RETIRED_L2_HIT_LOADS_ND"
pcr_metrics["MEM_UOPS_RETIRED_L2_MISS_LOADS"]="MEM_UOPS_RETIRED_L2_MISS_LOADS_ND"
pcr_metrics["NO_ALLOC_CYCLES_ALL"]="NO_ALLOC_CYCLES_ALL_ND"
pcr_metrics["NO_ALLOC_CYCLES_NOT_DELIVERED"]="NO_ALLOC_CYCLES_NOT_DELIVERED_ND"
pcr_metrics["NO_ALLOC_CYCLES_RAT_STALL"]="NO_ALLOC_CYCLES_RAT_STALL_ND"
pcr_metrics["NO_ALLOC_CYCLES_ROB_FULL"]="NO_ALLOC_CYCLES_ROB_FULL_ND"
pcr_metrics["PAGE_WALKS_D_SIDE_CYCLES"]="PAGE_WALKS_D_SIDE_CYCLES_ND"
pcr_metrics["PAGE_WALKS_D_SIDE_WALKS"]="PAGE_WALKS_D_SIDE_WALKS_ND"
pcr_metrics["REHABQ_ANY_LD"]="REHABQ_ANY_LD_ND"
pcr_metrics["REHABQ_ANY_ST"]="REHABQ_ANY_ST_ND"
pcr_metrics["REHABQ_STA_FULL"]="REHABQ_STA_FULL_ND"
pcr_metrics["RS_FULL_STALL_ALL"]="RS_FULL_STALL_ALL_ND"
pcr_metrics["RS_FULL_STALL_MEC"]="RS_FULL_STALL_MEC_ND"
pcr_metrics["UOPS_RETIRED_ALL"]="UOPS_RETIRED_ALL_ND"
pcr_metrics["MS_DECODED_MS_ENTRY"]="MS_DECODED_MS_ENTRY_ND"
pcr_metrics["CORE_REJECT_L2Q_ALL"]="CORE_REJECT_L2Q_ALL_ND"


#Haswell
pcr_metrics["L2_TRANS_L1D_WB"]="L2_TRANS_L1D_WB_ND"
pcr_metrics["L2_DEMAND_RQSTS_WB_MISS"]="HSW_HOHO_ND"
pcr_metrics["L2_DEMAND_RQSTS_WB_HIT"]="L2_DEMAND_RQSTS_WB_HIT_ND"
pcr_metrics["UNC_IMC_DRAM_DATA_READS"]="CAS_COUNT_RD_ND"
pcr_metrics["UNC_IMC_DRAM_DATA_WRITES"]="CAS_COUNT_WR_ND"
pcr_metrics["UNC_PP0_ENERGY_STATUS"]="UNC_PP0_ENERGY_STATUS_ND"
pcr_metrics["UNC_PKG_ENERGY_STATUS"]="UNC_PKG_ENERGY_STATUS_ND"
pcr_metrics["UNC_DRAM_ENERGY_STATUS"]="UNC_DRAM_ENERGY_STATUS_ND"
pcr_metrics["L2_RQSTS_MISS"]="L2_RQSTS_MISS_ND"

#Haswell-L4
pcr_metrics["UNC_L4_REQUEST_RD_HIT"]="UNC_L4_REQUEST.RD_HIT_ND"
pcr_metrics["UNC_L4_REQUEST_WR_HIT"]="UNC_L4_REQUEST.WR_HIT_ND"
pcr_metrics["UNC_L4_REQUEST_WR_FILL"]="UNC_L4_REQUEST_WR_FILL_ND"
pcr_metrics["UNC_L4_REQUEST_RD_EVICT_LINE_TO_DRAM"]="UNC_L4_REQUEST_RD_EVICT_LINE_TO_DRAM_ND"
pcr_metrics["UNC_CBO_L4_SUPERLINE_ALLOC_FAIL"]="UNC_CBO_L4_SUPERLINE_ALLOC_FAIL_ND"







function convert_metric {
	local converted_result

	arg=$( echo "$1" | tr "=" ":" )

	converted_result=${pcr_metrics["$arg"]}

	if [[ "$converted_result" == "" ]]
	then
		converted_result="${arg}"
	fi

	echo "$converted_result"	|
		sed 's/ /_/g'		|
		sed 's/,//g'		|
		sed 's/\[/(/g'		|
		sed 's/\]/)/g'		|
		sed 's/-/_/g'		|
		sed 's/\.//g'		|
		sed 's/:/_/g'		|
		sed 's/__/_/g'		|
		sed 's/__/_/g'		|
		sed 's/__/_/g'		|
		sed 's/__/_/g'		|
		sed 's/__/_/g'
}

convert_metric "$1"
