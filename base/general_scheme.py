from metric_names import MetricName
from xlsxgen import DerivedMetric

grouping = [
    ("Run Info", [
        (MetricName.NAME, True), MetricName.SHORT_NAME, MetricName.VARIANT,
        (MetricName.NUM_CORES, True), (MetricName.DATA_SET, True),
        (MetricName.PREFETCHERS, True), (MetricName.REPETITIONS, True) ]),
    ("Rate Metrics", [
        MetricName.RATE_REG_ADDR_GB_P_S, (MetricName.RATE_REG_DATA_GB_P_S, True),
        MetricName.RATE_REG_SIMD_GB_P_S,
        DerivedMetric("VR/3",
            [ MetricName.RATE_REG_SIMD_GB_P_S ],
            (lambda m: m / 3)),
        (MetricName.RATE_REG_GB_P_S, True),
        MetricName.RATE_L1_GB_P_S, MetricName.RATE_L2_GB_P_S,
        MetricName.RATE_L3_GB_P_S, MetricName.RATE_RAM_GB_P_S,
        MetricName.RATE_MAXMEM_GB_P_S, MetricName.MEM_LEVEL,
        (MetricName.RATE_LDST_GI_P_S, True), (MetricName.RATE_PACK_GPACKOP_P_S, True), 
        MetricName.RATE_FP_GFLOP_P_S,
        DerivedMetric("Ia,m",
            [ MetricName.RATE_MAXMEM_GB_P_S, MetricName.RATE_FP_GFLOP_P_S ],
            (lambda m, a: m.divide(a))),
        MetricName.RATE_INT_GIOP_P_S,
        MetricName.RATE_CVT_GCVTOP_P_S, MetricName.RATE_MEM_GMEMOP_P_S,
        MetricName.RATE_INST_GI_P_S ]),
    ("Stall Metrics", [
        MetricName.STALL_PRF_PCT, MetricName.STALL_SB_PCT,
        MetricName.STALL_RS_PCT, MetricName.STALL_LB_PCT,
        MetricName.STALL_ROB_PCT, MetricName.STALL_LM_PCT,
        MetricName.STALL_ANY_PCT, MetricName.STALL_FE_PCT, ]),
    ("Source-Level Analytics", [
        "ddg_true_cyclic", "ddg_artifical_cyclic",
        "scalar_reduction", "recurrence", "init_only",
        "limits", "offsets",
        "rhs_op_count", "scores",
    ]),
    ("Data Locality Metrics", [
        MetricName.ARRAY_EFFICIENCY_PCT
    ]),
    ("Op/Inst Percentages", [
        MetricName.COUNT_VEC_TYPE_OPS_PCT, MetricName.COUNT_OPS_VEC_PCT,
        MetricName.COUNT_INSTS_VEC_PCT, MetricName.COUNT_OPS_FMA_PCT,
        MetricName.COUNT_INSTS_FMA_PCT, MetricName.COUNT_OPS_DIV_PCT,
        MetricName.COUNT_INSTS_DIV_PCT, (MetricName.COUNT_OPS_SQRT_PCT, True),
        (MetricName.COUNT_INSTS_SQRT_PCT, True), (MetricName.COUNT_OPS_RSQRT_PCT, True),
        (MetricName.COUNT_INSTS_RSQRT_PCT, True), (MetricName.COUNT_OPS_RCP_PCT, True),
        (MetricName.COUNT_INSTS_RCP_PCT, True), MetricName.COUNT_OPS_CVT_PCT,
        MetricName.COUNT_INSTS_CVT_PCT, MetricName.COUNT_INSTS_GI,
    ]),
    ("LFB Histogram", [
        MetricName.BUSY_LFB_K0_PCT, MetricName.BUSY_LFB_K1_PCT, MetricName.BUSY_LFB_K2_PCT,
        MetricName.BUSY_LFB_K3_PCT, MetricName.BUSY_LFB_K4_PCT, MetricName.BUSY_LFB_K5_PCT,
        MetricName.BUSY_LFB_K6_PCT, MetricName.BUSY_LFB_K7_PCT, MetricName.BUSY_LFB_K8_PCT,
        MetricName.BUSY_LFB_K9_PCT, MetricName.BUSY_LFB_K10_PCT,
    ]),
    ("Timing Metrics", [
        MetricName.TIME_LOOP_S, (MetricName.TIME_APP_S, True),
        MetricName.RECIP_TIME_LOOP_MHZ, (MetricName.COVERAGE_PCT, True) ]),
    ("What-If? Speedups", [
        MetricName.SPEEDUP_VEC, MetricName.SPEEDUP_DL1
    ]),
    ("Speculatic Exc. Metrics", [
        MetricName.BRANCHES_MISP_PCT, MetricName.EXE_PER_RET_UOPS
    ]),
]

def apply(xlsxgen):
    xlsxgen.put_thresholds(MetricName.RATE_FP_GFLOP_P_S, [ 0.2, 0.2, 0.2 ])
    xlsxgen.put_cutoff(MetricName.STALL_SB_PCT, 50)
    xlsxgen.put_cutoff(MetricName.STALL_LM_PCT, 50)
    xlsxgen.put_cutoff(MetricName.STALL_RS_PCT, 50)
    xlsxgen.put_cutoff(MetricName.STALL_FE_PCT, 65)
    xlsxgen.put_highlight(MetricName.COUNT_VEC_TYPE_OPS_PCT, "SC=100.0%")
