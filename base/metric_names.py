from enum import Enum

def _instsPctStr(type): 
    return '%Inst[{}]'.format(type)

def _opsPctStr(type): 
    return '%Ops[{}]'.format(type)


# See https://docs.python.org/3/library/enum.html#others for reason why MetricName mixes str.
class MetricName(str, Enum):
    NAME = "Name"
    SHORT_NAME = "Short Name"
    SRC_NAME = "Source Name"
    TIMESTAMP = "Timestamp#"
    VARIANT = 'Variant'
    NUM_CORES = 'Num. Cores'
    DATA_SET = 'DataSet/Size'
    PREFETCHERS = 'prefetchers'
    REPETITIONS = 'Repetitions'
    TIME_LOOP_S = 'Time (s)'
    TIME_APP_S = 'AppTime (s)'
    RECIP_TIME_LOOP_MHZ = 'RecipTime (MHz)'
    COVERAGE_PCT = '%Coverage'
    RATE_REG_ADDR_GB_P_S = 'Register ADDR Rate (GB/s)'
    RATE_REG_DATA_GB_P_S = 'Register DATA Rate (GB/s)'
    RATE_REG_SIMD_GB_P_S = 'Register SIMD Rate (GB/s)'
    RATE_REG_GB_P_S = 'Register Rate (GB/s)'
    RATE_L1_GB_P_S = 'L1 Rate (GB/s)'
    RATE_L2_GB_P_S = 'L2 Rate (GB/s)'
    RATE_L3_GB_P_S = 'L3 Rate (GB/s)'
    RATE_RAM_GB_P_S = 'RAM Rate (GB/s)'
    RATE_LDST_GI_P_S = 'Load+Store Rate (GI/s)'
    RATE_FP_GFLOP_P_S = 'FLOP Rate (GFLOP/s)'
    RATE_INT_GIOP_P_S = 'IOP Rate (GIOP/s)'
    RATE_INST_GI_P_S = 'C=Inst. Rate (GI/s)'
                
    COUNT_INSTS_GI = 'O=Inst. Count (GI)'
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
    COUNT_VEC_TYPE_OPS_PCT = 'VecType[Ops]'

    STALL_PRF_PCT = '%PRF'
    STALL_SB_PCT = '%SB'
    STALL_RS_PCT = '%RS'
    STALL_LB_PCT = '%LB'
    STALL_ROB_PCT = '%ROB'
    STALL_LM_PCT = '%LM'
    STALL_ANY_PCT = '%ANY'
    STALL_FE_PCT = '%FrontEnd'
    
    SPEEDUP_VEC = 'Speedup[Vec]'
    SPEEDUP_DL1 = 'Speedup[DL1]'
    E_PKG_J = 'Total PKG Energy (J)'
    P_PKG_W = 'Total PKG Power (W)'
    E_DRAM_J = 'Total DRAM Energy (J)'
    P_DRAM_W = 'Total DRAM Power (W)'
    E_PKGDRAM_J = 'Total PKG+DRAM Energy (J)'
    P_PKGDRAM_W = 'Total PKG+DRAM Power (W)'

# EPO - Energy per Op, RPE - Rate per Energy, ROPE - (Rate * Op) per Energy
# Then the next two part e.g. PKG_INST is refering to specifiy what energy/power/rate/operation is about
    EPO_PKG_INST_J_P_GI = 'E[PKG]/O (J/GI)'
    RPE_INST_PKG_GI_P_JS = 'C/E[PKG] (GI/Js)'
    ROPE_INST_PKG_GI2_P_JS = 'CO/E[PKG] (GI2/Js)'
    EPO_DRAM_INST_J_P_GI = 'E[DRAM]/O (J/GI)'
    RPE_INST_DRAM_GI_P_JS = 'C/E[DRAM] (GI/Js)'
    ROPE_INST_DRAM_GI2_P_JS = 'CO/E[DRAM] (GI2/Js)'
    EPO_PKGDRAM_INST_J_P_GI = 'E[PKG+DRAM]/O (J/GI)'
    RPE_INST_PKGDRAM_GI_P_JS = 'C/E[PKG+DRAM] (GI/Js)'
    ROPE_INST_PKGDRAM_GI2_P_JS = 'CO/E[PKG+DRAM] (GI2/Js)',

    BRANCHES_MISP_PCT = '%Misp. Branches'
    EXE_PER_RET_UOPS = 'Executed/Retired Uops',

    ARRAY_EFFICIENCY_PCT = '%ArrayEfficiency'

    @classmethod
    def opsPct(cls, type):
        return cls(_opsPctStr(type))

    @classmethod
    def instsPct(cls, type):
        return cls(_instsPctStr(type))
    @classmethod
    def stallPct(cls, stall):
        return cls('%'+stall)

    @classmethod
    def energy(cls, kind):
        return cls('Total {} Energy (J)'.format(kind))

    @classmethod
    def power(cls, kind):
        return cls('Total {} Power (W)'.format(kind))

    @classmethod
    def epo(cls, ekind, ikind='INST'):
        return cls('E[{}]/O (J/GI)'.format(ekind))

    @classmethod
    def rpe(cls, ekind, ikind='INST'):
        return cls('C/E[{}] (GI/Js)'.format(ekind))

    @classmethod
    def rope(cls, ekind, ikind='INST'):
        return cls('CO/E[{}] (GI2/Js)'.format(ekind))
