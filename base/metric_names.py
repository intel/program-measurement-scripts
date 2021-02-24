from enum import Enum
import re

def _instsPctStr(type): 
    return 'Count[Insts[{}]]_%'.format(type)

def _opsPctStr(type): 
    return 'Count[Ops[{}]]_%'.format(type)

def _stallPctStr(stall):
    return 'Stall[{}]_%'.format(stall)

def _busyLfbPctStr(cnt):
    return 'Busy[LFB[k{}]]_%'.format(cnt)

def _energyStr(type):
    return 'E[{}]_J'.format(type)

def _powerStr(type):
    return 'P[{}]_W'.format(type)


def _epoStr(ekind, ikind):
    return 'EPerOp[{},{}]_J/GI'.format(ekind, ikind)

def _rpeStr(ekind, ikind):
    return 'RatePerE[{},{}]_GI/Js'.format(ikind, ekind)

def _ropeStr(ekind, ikind):
    return 'RateOpsPerE[{},{}]_GI2/Js'.format(ikind, ekind)

def _memlevelStr(threshold):
    return 'MaxMemlevel[{}%]'.format(threshold)

def _capStr(node, unit):
    return 'C_{} [{}]'.format(node, unit)

def _capWUnitStr(node_w_unit):
    return 'C_{}'.format(node_w_unit)

# See https://docs.python.org/3/library/enum.html#others for reason why MetricName mixes str.
class CapeEnum(str, Enum):
    def __str__(self):
        return str(self.value)

    def __format__(self, format_spec):
        return format(self.value, format_spec)
    
class MetricName(CapeEnum):
    NAME = "Name"
    SHORT_NAME = "ShortName"
    SRC_NAME = "SourceName"
    TIMESTAMP = "Timestamp#"
    VARIANT = 'Variant'
    NUM_CORES = 'NumCores'
    DATA_SET = 'DataSet'
    #MEM_LEVEL = 'Memlevel'
    MAX_MEM_LEVEL_100 = _memlevelStr(100)
    MAX_MEM_LEVEL_85 = _memlevelStr(85)
    MEM_LEVEL = MAX_MEM_LEVEL_100
    PREFETCHERS = 'Prefetchers'
    REPETITIONS = 'Repetitions'
    TIME_LOOP_S = 'Time[Loop]_s'
    TIME_APP_S = 'Time[App]_s'
    RECIP_TIME_LOOP_MHZ = 'RecipTime[Loop]_MHz'
    COVERAGE_PCT = 'Coverage_%'
    RATE_REG_ADDR_GB_P_S = 'Rate[Reg[Addr]]_GB/s'
    RATE_REG_DATA_GB_P_S = 'Rate[Reg[Data]]_GB/s'
    RATE_REG_SIMD_GB_P_S = 'Rate[Reg[Simd]]_GB/s'
    RATE_REG_GB_P_S = 'Rate[Reg]_GB/s'
    RATE_L1_GB_P_S = 'Rate[L1]_GB/s'
    RATE_L2_GB_P_S = 'Rate[L2]_GB/s'
    RATE_L3_GB_P_S = 'Rate[L3]_GB/s'
    RATE_RAM_GB_P_S = 'Rate[RAM]_GB/s'
    RATE_MAXMEM_GB_P_S = 'Rate[MaxMem]_GB/s'
    RATE_LDST_GI_P_S = 'Rate[Ld+St]_GI/s'
    RATE_FP_GFLOP_P_S = 'Rate[Fp]_GFLOP/s'
    RATE_CVT_GCVTOP_P_S = 'Rate[Cvt]_GCVTOP/s'
    RATE_PACK_GPACKOP_P_S = 'Rate[Pack]_GPACKOP/s'
    RATE_MEM_GMEMOP_P_S = 'Rate[Mem]_GMEMOP/s'
    RATE_INT_GIOP_P_S = 'Rate[Int]_GIOP/s'
    RATE_INST_GI_P_S = 'Rate[Inst]_GI/s'
                
    COUNT_INSTS_GI = 'Count[Insts]_GI'
    COUNT_OPS_VEC_PCT = _opsPctStr('Vec')
    COUNT_INSTS_VEC_PCT = _instsPctStr('Vec')
    #COUNT_INSTS_VEC_PCT = '%Inst[Vec]'
    COUNT_OPS_FMA_PCT = _opsPctStr('FMA')
    COUNT_INSTS_FMA_PCT = _instsPctStr('FMA')
    COUNT_OPS_DIV_PCT = _opsPctStr('DIV')
    COUNT_INSTS_DIV_PCT = _instsPctStr('DIV')
    COUNT_OPS_SQRT_PCT = _opsPctStr('SQRT')
    COUNT_INSTS_SQRT_PCT = _instsPctStr('SQRT')
    COUNT_OPS_RSQRT_PCT = _opsPctStr('RSQRT')
    COUNT_INSTS_RSQRT_PCT = _instsPctStr('RSQRT')
    COUNT_OPS_RCP_PCT = _opsPctStr('RCP')
    COUNT_INSTS_RCP_PCT = _instsPctStr('RCP')
    COUNT_OPS_CVT_PCT = _opsPctStr('CVT')
    COUNT_INSTS_CVT_PCT = _instsPctStr('CVT')
    COUNT_OPS_PACK_PCT = _opsPctStr('PACK')
    COUNT_INSTS_PACK_PCT = _instsPctStr('PACK')
    COUNT_VEC_TYPE_OPS_PCT = 'VecType[Ops]'

    STALL_PRF_PCT = _stallPctStr('PRF')
    STALL_SB_PCT = _stallPctStr('SB')
    STALL_RS_PCT = _stallPctStr('RS')
    STALL_LB_PCT = _stallPctStr('LB')
    STALL_ROB_PCT = _stallPctStr('ROB')
    STALL_LM_PCT = _stallPctStr('LM')
    STALL_ANY_PCT = _stallPctStr('ANY')
    STALL_FE_PCT = _stallPctStr('FE')

    BUSY_LFB_K0_PCT = _busyLfbPctStr(0)
    BUSY_LFB_K1_PCT = _busyLfbPctStr(1)
    BUSY_LFB_K2_PCT = _busyLfbPctStr(2)
    BUSY_LFB_K3_PCT = _busyLfbPctStr(3)
    BUSY_LFB_K4_PCT = _busyLfbPctStr(4)
    BUSY_LFB_K5_PCT = _busyLfbPctStr(5)
    BUSY_LFB_K6_PCT = _busyLfbPctStr(6)
    BUSY_LFB_K7_PCT = _busyLfbPctStr(7)
    BUSY_LFB_K8_PCT = _busyLfbPctStr(8)
    BUSY_LFB_K9_PCT = _busyLfbPctStr(9)
    BUSY_LFB_K10_PCT = _busyLfbPctStr(10)
    
    SPEEDUP_VEC = 'Speedup[Vec]'
    SPEEDUP_DL1 = 'Speedup[DL1]'
    SPEEDUP_TIME_LOOP_S = 'Speedup[Time[Loop]_s]'
    SPEEDUP_TIME_APP_S = 'Speedup[Time[App]_s]'
    SPEEDUP_RATE_FP_GFLOP_P_S = 'Speedup[Rate[Fp]_GFLOP/s]'
    E_PKG_J = _energyStr('PKG')
    P_PKG_W = _powerStr('PKG')
    E_DRAM_J = _energyStr('DRAM')
    P_DRAM_W = _powerStr('DRAM')
    E_PKGDRAM_J = _energyStr('PKG+DRAM')
    P_PKGDRAM_W = _powerStr('PKG+DRAM')

# EPO - Energy per Op, RPE - Rate per Energy, ROPE - (Rate * Op) per Energy
# Then the next two part e.g. PKG_INST is refering to specifiy what energy/power/rate/operation is about
    EPO_PKG_INST_J_P_GI = _epoStr('PKG', 'Inst')
    RPE_INST_PKG_GI_P_JS = _rpeStr('PKG', 'Inst')
    ROPE_INST_PKG_GI2_P_JS = _ropeStr('PKG', 'Inst')
    EPO_DRAM_INST_J_P_GI = _epoStr('DRAM', 'Inst')
    RPE_INST_DRAM_GI_P_JS = _rpeStr('DRAM', 'Inst')
    ROPE_INST_DRAM_GI2_P_JS = _ropeStr('DRAM', 'Inst')
    EPO_PKGDRAM_INST_J_P_GI = _epoStr('PKG+DRAM', 'Inst')
    RPE_INST_PKGDRAM_GI_P_JS = _rpeStr('PKG+DRAM', 'Inst')
    ROPE_INST_PKGDRAM_GI2_P_JS = _ropeStr('PKG+DRAM', 'Inst')

    BRANCHES_MISP_PCT = 'Branches[Misp]_%'
    EXE_PER_RET_UOPS = 'ExeRetUopsRatio',

    ARRAY_EFFICIENCY_PCT = 'ArrayEfficiency_%'
    COUNT_OPS_RHS_OP = 'rhs_op_count'
    RECURRENCE_BOOL = 'recurrence'
    SCORE_CLU_PCT = 'clu_scores'

    # Capacities
    CAP_FP_GFLOP_P_S = _capStr('FLOP', 'GFlop/s')
    CAP_FP_GB_P_S = _capStr('FLOP', 'GB/s')
    CAP_L1_GW_P_S = _capStr('L1', 'GW/s')
    CAP_L1_GB_P_S = _capStr('L1', 'GB/s')
    CAP_L2_GW_P_S = _capStr('L2', 'GW/s')
    CAP_L2_GB_P_S = _capStr('L2', 'GB/s')
    CAP_L3_GW_P_S = _capStr('L3', 'GW/s')
    CAP_L3_GB_P_S = _capStr('L3', 'GB/s')
    CAP_RAM_GW_P_S = _capStr('RAM', 'GW/s')
    CAP_RAM_GB_P_S = _capStr('RAM', 'GB/s')
    CAP_VR_GW_P_S = _capStr('VR', 'GW/s')
    CAP_VR_GB_P_S = _capStr('VR', 'GB/s')
    CAP_MEMMAX_GW_P_S = _capStr('max', 'GW/s')
    CAP_MEMMAX_GB_P_S = _capStr('max', 'GB/s')
    CAP_ALLMAX_GW_P_S = _capStr('allmax', 'GW/s')
    CAP_ALLMAX_GB_P_S = _capStr('allmax', 'GB/s')
    CAP_SCALAR_GW_P_S = _capStr('scalar', 'GW/s')
    CAP_SCALAR_GB_P_S = _capStr('scalar', 'GB/s')
    CAP_FE_GW_P_S = _capStr('FE', 'GW/s')
    CAP_FE_GB_P_S = _capStr('FE', 'GB/s')
    CAP_SB_GW_P_S = _capStr('SB', 'GW/s')
    CAP_SB_GB_P_S = _capStr('SB', 'GB/s')
    CAP_LM_GW_P_S = _capStr('LM', 'GW/s')
    CAP_LM_GB_P_S = _capStr('LM', 'GB/s')
    CAP_RS_GW_P_S = _capStr('RS', 'GW/s')
    CAP_RS_GB_P_S = _capStr('RS', 'GB/s')
    CAP_CU_GW_P_S = _capStr('CU', 'GW/s')
    CAP_CU_GB_P_S = _capStr('CU', 'GB/s')
    CAP_LB_GW_P_S = _capStr('LB', 'GW/s')
    CAP_LB_GB_P_S = _capStr('LB', 'GB/s')
    

    @classmethod
    def cap(cls, node, unit):
        return cls(_capStr(node, unit))

    @classmethod
    def capWUnit(cls, node_w_unit):
        return cls(_capWUnitStr(node_w_unit))
        
    @classmethod
    def opsPct(cls, type):
        return cls(_opsPctStr(type))

    @classmethod
    def instsPct(cls, type):
        return cls(_instsPctStr(type))

    @classmethod
    def stallPct(cls, stall):
        return cls(_stallPctStr(stall))


    @classmethod
    def busyLfbPct(cls, cnt):
        return cls(_busyLfbPctStr(cnt))

    @classmethod
    def energy(cls, kind):
        return cls(_energyStr(kind))

    @classmethod
    def power(cls, kind):
        return cls(_powerStr(kind))

    @classmethod
    def epo(cls, ekind, ikind='Inst'):
        return cls(_epoStr(ekind, ikind))

    @classmethod
    def rpe(cls, ekind, ikind='Inst'):
        return cls(_rpeStr(ekind, ikind))

    @classmethod
    def rope(cls, ekind, ikind='Inst'):
        return cls(_ropeStr(ekind, ikind))

    @classmethod
    def memlevel(cls, threshold):
        return cls(_memlevelStr(threshold))

    # With metric pattern <MetricType>[<Component>]_<UNIT>
    # extract the <Component> part
    def extractComponent(self):
        matched = re.match(r"([^_]*)_(.*)", self)
        metricAndComp = matched.group(1)
        matched = re.match(r"([^\[]*)\[(.*)\]$", metricAndComp)
        return matched.group(2)
        
#  For column names that are not measurement data
# TODO: move some of the MetricNames here.
class NonMetricName(CapeEnum):
    SI_CLUSTER_NAME = "SiClusterName"
    SI_SAT_NODES = "SiSatNodes"
    SI_SAT_TIER = "SiTier"
    SI_SW_BIAS = "Net_SW_Bias"

KEY_METRICS = [ MetricName.NAME, MetricName.TIMESTAMP ]

# Provides all the enums useful for filtering irrelevant metrics
ALL_METRICS = list(MetricName) + list(NonMetricName)


RUN_INFO_METRICS = KEY_METRICS + [ MetricName.SHORT_NAME, MetricName.VARIANT, 
                    MetricName.NUM_CORES, MetricName.DATA_SET, MetricName.PREFETCHERS, 
                    MetricName.REPETITIONS, MetricName.SRC_NAME]
TIME_METRICS = [ MetricName.TIME_LOOP_S, MetricName.RECIP_TIME_LOOP_MHZ, 
                MetricName.TIME_APP_S, MetricName.COVERAGE_PCT]

COUNT_METRICS = [ m for m in ALL_METRICS if m.startswith("Count[") ] + [MetricName.COUNT_VEC_TYPE_OPS_PCT]

RATE_METRICS = [ m for m in ALL_METRICS if m.startswith("Rate[") ] 

BRANCH_METRICS = [ MetricName.BRANCHES_MISP_PCT, MetricName.EXE_PER_RET_UOPS ]

ENERGY_METRICS = [ MetricName.E_PKG_J, MetricName.P_PKG_W, MetricName.E_DRAM_J, MetricName.P_DRAM_W, 
                  MetricName.E_PKGDRAM_J, MetricName.P_PKGDRAM_W, MetricName.EPO_PKG_INST_J_P_GI, 
                  MetricName.RPE_INST_PKG_GI_P_JS, MetricName.ROPE_INST_PKG_GI2_P_JS, 
                  MetricName.EPO_DRAM_INST_J_P_GI, MetricName.RPE_INST_DRAM_GI_P_JS, 
                  MetricName.ROPE_INST_DRAM_GI2_P_JS, MetricName.EPO_PKGDRAM_INST_J_P_GI, 
                  MetricName.RPE_INST_PKGDRAM_GI_P_JS, MetricName.ROPE_INST_PKGDRAM_GI2_P_JS ]


STALL_METRICS = [m for m in ALL_METRICS if m.startswith("Stall[") ] 

MEM_ACCESS_METRICS = [ MetricName.MAX_MEM_LEVEL_100, MetricName.MAX_MEM_LEVEL_85, MetricName.ARRAY_EFFICIENCY_PCT]

WHATIF_SPEEDUP_METRICS = [ MetricName.SPEEDUP_DL1, MetricName.SPEEDUP_VEC ]

SUMMARY_METRICS = RUN_INFO_METRICS + TIME_METRICS + COUNT_METRICS + RATE_METRICS \
    + BRANCH_METRICS + STALL_METRICS + MEM_ACCESS_METRICS + WHATIF_SPEEDUP_METRICS + ENERGY_METRICS  

NAME_FILE_METRICS = [ MetricName.SHORT_NAME, MetricName.VARIANT ]
CAPACITY_METRICS = [ m for m in ALL_METRICS if m.startswith("C_") ]