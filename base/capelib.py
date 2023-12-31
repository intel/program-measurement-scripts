import re
import math
from collections import namedtuple
import pandas as pd
from metric_names import MetricName, KEY_METRICS
# Importing the MetricName enums to global variable space
# See: http://www.qtrac.eu/pyenum.html
globals().update(MetricName.__members__)

# Common routines needed for Cape tool chain

class Vecinfo:
    def __init__(self, SUM=0, SC=0, XMM=0, YMM=0, ZMM=0, FMA=0, DIV=0, SQRT=0, RSQRT=0, RCP=0, CVT=0, PACK=0):
        self.SUM = SUM
        self.SC = SC
        self.XMM = XMM
        self.YMM = YMM
        self.ZMM = ZMM
        self.FMA = FMA
        self.DIV = DIV
        self.SQRT = SQRT
        self.RSQRT = RSQRT
        self.RCP = RCP
        self.CVT = CVT
        self.PACK = PACK

    def __add__(self, other):
        return Vecinfo(SUM = self.SUM + other.SUM, SC = self.SC + other.SC, XMM = self.XMM + other.XMM, 
        YMM = self.YMM + other.YMM, ZMM = self.ZMM + other.ZMM, FMA = self.FMA + other.FMA, \
        DIV = self.DIV + other.DIV, SQRT = self.SQRT + other.SQRT, RSQRT = self.RSQRT + other.RSQRT, \
        RCP = self.RCP + other.RCP, CVT = self.CVT + other.CVT, PACK = self.PACK + other.PACK)

    @classmethod
    def from_dict(cls, dict):
        created = cls()
        for key, value in dict.items():
            if key in vars(created):
                setattr(created, key, value)
            else:
                raise AttributeError('Attempt to set invalid attribute \'{}\''.format(key))
        return created

    def __str__(self):
        return str(vars(self))

    

# Vecinfo = namedtuple('Vecinfo', ['SUM','SC','XMM','YMM','ZMM', 'FMA', \
#     'DIV', 'SQRT', 'RSQRT', 'RCP', 'CVT'])
# # Allows defaults values 
# # See: https://stackoverflow.com/questions/11351032/named-tuple-and-default-values-for-optional-keyword-arguments
# Vecinfo.__new__.__defaults__ = (0,)*len(Vecinfo._fields)


# This function should be called instead of individual calls of
# add_one_mem_max_level_columns() to ensure consistent thresholds being computed
def add_mem_max_level_columns(inout_df, node_list, max_rate_name, metric_to_memlevel_lambda):
    max_rate =inout_df[node_list].max(axis=1)
    inout_df[max_rate_name] = max_rate
    add_one_mem_max_level_columns(inout_df, node_list, max_rate, metric_to_memlevel_lambda, 100)
    add_one_mem_max_level_columns(inout_df, node_list, max_rate, metric_to_memlevel_lambda, 85)

# Compute the max memory level column 
# node_list is an ordered list with preferred node at the right
# threshold is in percentage ranging [0-100]
# order(n) = index of n in node_list
# acceptableNodes = { node \in node_list : v[node] >= max_{n \in node_list}(v[n]) * threshold }
# max_level_node = node_list[max({order(n) : n in acceptableNodes})]
def add_one_mem_max_level_columns(inout_df, node_list, max_rate, metric_to_memlevel_lambda, threshold=100):
    memLevel = MetricName.memlevel(threshold)
    # TODO: Comment out below to avoid creating new df.  Need to fix if notna() check needed
    # inout_df = inout_df[inout_df[max_rate_name].notna()]
    # Note (threshold/100) needs to be computed first to avoid rounding errors
    passValues = max_rate*(threshold/100)
    rnode_list = node_list[::-1] # Reverse list to put preferred nodes first
    # mask with values passing the threshold and column in reversed order so prefered columns come first
    passMask = inout_df.loc[:, rnode_list].ge(passValues,axis=0)
    # Use idxmax() to return first column with the biggest value (which is value of True)
    inout_df[memLevel]=passMask.idxmax(axis=1)
    # inout_df[MEM_LEVEL]=inout_df[node_list].idxmax(axis=1)
    nonnullMask = ~inout_df[memLevel].isnull()
    inout_df.loc[nonnullMask, memLevel] = inout_df.loc[nonnullMask, memLevel].apply(metric_to_memlevel_lambda)
    # Old stuff below to be deleted
	# Remove the first two characters which is 'C_'
    # inout_df[MEM_LEVEL] = inout_df[MEM_LEVEL].apply((lambda v: v[2:]))
	# Drop the unit
	# inout_df[MEM_LEVEL] = inout_df[MEM_LEVEL].str.replace(" \[.*\]","", regex=True)

# Simple function to convert nan's to 0
def nan2zero(v):
    return 0 if math.isnan(v) else v

# For CQA metrics
def calculate_all_rate_and_counts(out_row, in_row, iterations_per_rep, time):
    vec_ops = all_ops = vec_insts = all_insts = fma_ops = fma_insts = 0
    itypes = ['FMA', 'DIV', 'SQRT', 'RSQRT', 'RCP', 'CVT', 'PACK']
    ops_dict = {itype : 0 for itype in itypes}
    inst_dict = {itype : 0 for itype in itypes}

    def calculate_rate_and_counts(op_rate_name, op_count_name, inst_rate_name, calculate_counts_per_iter, add_global_count):
        try:
            nonlocal all_ops
            nonlocal all_insts
            nonlocal vec_ops
            nonlocal vec_insts
            nonlocal fma_ops
            nonlocal fma_insts
            nonlocal ops_dict
            nonlocal inst_dict
            cnts_per_iter, inst_cnts_per_iter = calculate_counts_per_iter(in_row)
            op_count_per_rep = (cnts_per_iter.SUM * iterations_per_rep) / 1E9 

            if op_count_name:
                out_row[op_count_name] =  op_count_per_rep
                
            out_row[op_rate_name] =  op_count_per_rep / time
            if inst_rate_name: out_row[inst_rate_name] = (inst_cnts_per_iter.SUM * iterations_per_rep) / (1E9 * time)

            if add_global_count:
                vec_ops += nan2zero(cnts_per_iter.XMM + cnts_per_iter.YMM + cnts_per_iter.ZMM)
                all_ops += nan2zero(cnts_per_iter.SUM)

                vec_insts += nan2zero(inst_cnts_per_iter.XMM + inst_cnts_per_iter.YMM + inst_cnts_per_iter.ZMM)
                all_insts += nan2zero(inst_cnts_per_iter.SUM)
                for itype in itypes:
                    ops_dict[itype] += nan2zero(getattr(cnts_per_iter, itype))
                    inst_dict[itype] += nan2zero(getattr(inst_cnts_per_iter, itype))

            return cnts_per_iter, inst_cnts_per_iter
        except:
            return None, None

    flop_cnts_per_iter, fl_inst_cnts_per_iter = calculate_rate_and_counts(RATE_FP_GFLOP_P_S, COUNT_FP_GFLOP, None, calculate_flops_counts_per_iter, True)
    iop_cnts_per_iter, i_inst_cnts_per_iter = calculate_rate_and_counts(RATE_INT_GIOP_P_S, None, None, calculate_iops_counts_per_iter, True)
    # Note: enabled global count so CVT insts will be contributing to total inst/op count in evaulating %Inst, %Vec metrics
    cvt_cnts_per_iter, cvt_inst_cnts_per_iter = calculate_rate_and_counts(RATE_CVT_GCVTOP_P_S, None, None, calculate_cvtops_counts_per_iter, True)
    pack_cnts_per_iter, pack_inst_cnts_per_iter = calculate_rate_and_counts(RATE_PACK_GPACKOP_P_S, None, None, calculate_packops_counts_per_iter, True)
    memop_cnts_per_iter, mem_inst_cnts_per_iter = calculate_rate_and_counts(RATE_MEM_GMEMOP_P_S, None, RATE_LDST_GI_P_S, calculate_memops_counts_per_iter, True)

    out_row[COUNT_OPS_VEC_PCT] = 100 * vec_ops / all_ops if all_ops else 0
    out_row[COUNT_INSTS_VEC_PCT] = 100 * vec_insts / all_insts if all_insts else 0
    for itype in itypes:
        out_row[MetricName.opsPct(itype)] = 100 * ops_dict[itype] / all_ops if all_ops else 0
        out_row[MetricName.instsPct(itype)] = 100 * inst_dict[itype] / all_insts if all_insts else 0

    try:
        # Check if CQA metric is available
        cqa_vec_ratio=in_row['Vec._ratio_(%)_all']
        if not math.isclose(cqa_vec_ratio, out_row[COUNT_INSTS_VEC_PCT], rel_tol=1e-8):
            warnings.warn("CQA Vec. ration not matching computed: CQA={}, Computed={}, AllIters={}".format \
                          (cqa_vec_ratio, out_row[COUNT_INSTS_VEC_PCT], in_row['AllIterations']))
            # Just set to CQA value for now.  (Pending check with Emmanuel)
            out_row[COUNT_INSTS_VEC_PCT] = cqa_vec_ratio
    except:
        pass 
    out_row[COUNT_VEC_TYPE_OPS_PCT] = find_vector_ext (flop_cnts_per_iter + iop_cnts_per_iter 
         + memop_cnts_per_iter + cvt_cnts_per_iter + pack_cnts_per_iter)


def calculate_flops_counts_per_iter(in_row):
    def calculate_flops_counts_with_weights(in_row, w_sc_sp, w_sc_dp, w_vec_xmm, w_vec_ymm, w_vec_zmm, w_fma):
        def calculate_flops(flops_per_sp_inst, flops_per_dp_inst, sp_inst_template, dp_inst_template):
            itypes = ['ADD_SUB', 'MUL']
            all_flops=0
            for itype in itypes:
                all_flops += (flops_per_sp_inst * getter(in_row, sp_inst_template.format(itype)) + \
                    flops_per_dp_inst * getter(in_row, dp_inst_template.format(itype)))

            itypes = ['DIV', 'SQRT', 'RSQRT', 'RCP']
            per_type_flops = {}
            for itype in itypes:
                per_type_flops[itype] = (flops_per_sp_inst * getter(in_row, sp_inst_template.format(itype)) + \
                    flops_per_dp_inst * getter(in_row, dp_inst_template.format(itype)))
                all_flops += per_type_flops[itype]
            ans = all_flops, *tuple([per_type_flops[itype] for itype in itypes])
            return ans


        try:
            # try to use counters if collected.  The count should already be across all cores.
            # NOTE: for counters, we could not distinguish FMA instruction and those will be double counted
            flops_sc = w_sc_sp * getter(in_row, 'FP_ARITH_INST_RETIRED_SCALAR_SINGLE') + w_sc_dp * getter(in_row, 'FP_ARITH_INST_RETIRED_SCALAR_DOUBLE') 
            flops_xmm = w_vec_xmm * (getter(in_row, 'FP_ARITH_INST_RETIRED_128B_PACKED_SINGLE') + getter(in_row, 'FP_ARITH_INST_RETIRED_128B_PACKED_DOUBLE'))
            flops_ymm = w_vec_ymm * (getter(in_row, 'FP_ARITH_INST_RETIRED_256B_PACKED_SINGLE') + getter(in_row, 'FP_ARITH_INST_RETIRED_256B_PACKED_DOUBLE'))
            flops_zmm = w_vec_zmm * (getter(in_row, 'FP_ARITH_INST_RETIRED_512B_PACKED_SINGLE') + getter(in_row, 'FP_ARITH_INST_RETIRED_512B_PACKED_DOUBLE'))
            flops_fma = 0  # Don't have that for counters
            flops = flops_sc + flops_xmm + flops_ymm + flops_zmm
            results = (flops, flops_sc, flops_xmm, flops_ymm, flops_zmm, flops_fma, 0, 0, 0, 0)
        except:
            metric_prefix="Nb_FP_insn" if "Nb_FP_insn_ADD_SUBSS" in in_row.keys() else "Nb_insn"

            flops_sc, flops_div_sc, flops_sqrt_sc, flops_rsqrt_sc, flops_rcp_sc = \
                calculate_flops(w_sc_sp, w_sc_dp, metric_prefix+'_{}SS', metric_prefix+'_{}SD')
            flops_xmm, flops_div_xmm, flops_sqrt_xmm, flops_rsqrt_xmm, flops_rcp_xmm = \
                calculate_flops(w_vec_xmm, w_vec_xmm, metric_prefix+'_{}PS_XMM', metric_prefix+'_{}PD_XMM')
            flops_ymm, flops_div_ymm, flops_sqrt_ymm, flops_rsqrt_ymm, flops_rcp_ymm = \
                calculate_flops(w_vec_ymm, w_vec_ymm, metric_prefix+'_{}PS_YMM', metric_prefix+'_{}PD_YMM')
            flops_zmm, flops_div_zmm, flops_sqrt_zmm, flops_rsqrt_zmm, flops_rcp_zmm = \
                calculate_flops(w_vec_zmm, w_vec_zmm, metric_prefix+'_{}PS_ZMM', metric_prefix+'_{}PD_ZMM')
    
    
            # try to add the FMA counts
            flops_fma_sc = w_fma * (w_sc_sp * getter(in_row, metric_prefix+'_FMASS') + w_sc_dp * getter(in_row, metric_prefix+'_FMASD'))
            flops_sc += flops_fma_sc
            flops_fma_xmm = w_fma * w_vec_xmm*(getter(in_row, metric_prefix+'_FMAPS_XMM') + getter(in_row, metric_prefix+'_FMAPD_XMM'))
            flops_xmm += flops_fma_xmm
            flops_fma_ymm = w_fma * w_vec_ymm*(getter(in_row, metric_prefix+'_FMAPS_YMM')  + getter(in_row, metric_prefix+'_FMAPD_YMM'))
            flops_ymm += flops_fma_ymm
            flops_fma_zmm = w_fma * w_vec_zmm*(getter(in_row, metric_prefix+'_FMAPS_ZMM') + getter(in_row, metric_prefix+'_FMAPD_ZMM'))
            flops_zmm += flops_fma_zmm
            flops_fma = flops_fma_sc + flops_fma_xmm + flops_fma_ymm + flops_fma_zmm
            flops_div = flops_div_sc + flops_div_xmm + flops_div_ymm + flops_div_zmm
            flops_sqrt = flops_sqrt_sc + flops_sqrt_xmm + flops_sqrt_ymm + flops_sqrt_zmm
            flops_rsqrt = flops_rsqrt_sc + flops_rsqrt_xmm + flops_rsqrt_ymm + flops_rsqrt_zmm
            flops_rcp = flops_rcp_sc + flops_rcp_xmm + flops_rcp_ymm + flops_rcp_zmm

            flops = flops_sc + flops_xmm + flops_ymm + flops_zmm

    
#            results = (flops, flops_sc, flops_xmm, flops_ymm, flops_zmm)

            # Multiple to get count for all cores
            results = [(ops * getter(in_row, 'decan_experimental_configuration.num_core')) \
                for ops in [flops, flops_sc, flops_xmm, flops_ymm, flops_zmm, flops_fma, flops_div, flops_sqrt, flops_rsqrt, flops_rcp]]
        return Vecinfo(*results)

    flops_counts = calculate_flops_counts_with_weights(in_row, 0.5, 1, 2, 4, 8, 2)
    insts_counts = calculate_flops_counts_with_weights(in_row, 1, 1, 1, 1, 1, 1)
    return flops_counts, insts_counts

# Calculate instruction and operation counts per iteration
# opc_table is a table with Units in Bytes
# Example of opc_table:
#  opc_table = [ 
#     { 'Inst':'DQ2PS', 'SC': None, 'XMM':    16, 'YMM':    32, 'ZMM':   64},
#     ...
#     { 'Inst':'SS2SI', 'SC':    4, 'XMM':  None, 'YMM':  None, 'ZMM': None}
#     ]
# TODO: If this function works well, unify with other instruction counting.
def calculate_ops_counts_per_iter(in_row, opc_table, op_type):
    opc_df = pd.DataFrame(opc_table)
    # Convert from bytes to DP (64-bit = 8B)
    opc_df[['SC','XMM', 'YMM', 'ZMM']]=opc_df[['SC', 'XMM', 'YMM', 'ZMM']]/8
    # Get a prefix of cvt instructions to match with in_row columns
    cvt_col_prefixes = tuple(["Nb_insn_{}".format(inst) for inst in opc_df.Inst])
    # Now we got the column names for cvt operations
    cvt_col_names = [col for col in in_row.keys() if col.startswith(cvt_col_prefixes)]
    opcount = { 'SUM': 0, 'SC': 0, 'XMM': 0, 'YMM' : 0, 'ZMM': 0 }
    icount = { 'SUM': 0, 'SC': 0, 'XMM': 0, 'YMM' : 0, 'ZMM': 0 }
    for cvt_col_name in cvt_col_names:
        matchobj = re.search(r'^Nb_insn_(.+?)_(.MM)$', cvt_col_name)
        if matchobj:
            inst = matchobj.group(1)
            regtype = matchobj.group(2)
        else:
            # match again to get rid of Nb_insn_
            matchobj = re.search(r'^Nb_insn_(.+?)$', cvt_col_name)
            inst = matchobj.group(1)
            regtype = 'SC'
        insts = in_row[cvt_col_name]
        ops = insts * opc_df.loc[opc_df.Inst == inst, regtype].values[0]
        opcount[regtype] += ops
        opcount['SUM'] += ops
        icount[regtype] += insts
        icount['SUM'] += insts
    icount[op_type] = icount['SUM']
    opcount[op_type] = opcount['SUM']
    return Vecinfo.from_dict(opcount), Vecinfo.from_dict(icount)

def calculate_packops_counts_per_iter(in_row):
    # Units in bytes
    opc_table = [
        { 'Inst':'INSERT/EXTRACT',  'SC': 4,    'XMM': None, 'YMM': None, 'ZMM': None},
        { 'Inst':'COMPRESS/EXPAND', 'SC': None, 'XMM':   16, 'YMM':   32, 'ZMM':   64},
        { 'Inst':'MMX_to/from',     'SC': 8,    'XMM': None, 'YMM': None, 'ZMM': None},
        { 'Inst':'BLEND/MERGE',     'SC': None, 'XMM':   16, 'YMM':   32, 'ZMM':   64},
        { 'Inst':'SHUFFLE/PERM',    'SC': None, 'XMM':   16, 'YMM':   32, 'ZMM':   64},
        { 'Inst':'BROADCAST',       'SC': None, 'XMM':   16, 'YMM':   32, 'ZMM':   64},
        { 'Inst':'GATHER/SCATTER',  'SC': None, 'XMM':   16, 'YMM':   32, 'ZMM':   64},
        { 'Inst':'MASKMOV/MOV2M',   'SC': None, 'XMM':   16, 'YMM':   32, 'ZMM':   64},
        { 'Inst':'Other_packing',   'SC': None, 'XMM':   16, 'YMM':   32, 'ZMM':   64},
    ]
    return calculate_ops_counts_per_iter(in_row, opc_table, 'PACK')

def calculate_cvtops_counts_per_iter(in_row):
    # Units in Bytes
    opc_table = [ 
        { 'Inst':'DQ2PS', 'SC': None, 'XMM':    16, 'YMM':    32, 'ZMM':   64},
        { 'Inst':'DQ2PD', 'SC': None, 'XMM':     8, 'YMM':    16, 'ZMM':   32},
        { 'Inst':'PD2DQ', 'SC': None, 'XMM':    16, 'YMM':    32, 'ZMM':   64},
        { 'Inst':'PD2PS', 'SC': None, 'XMM':    16, 'YMM':    32, 'ZMM':   64},
        { 'Inst':'PD2QQ', 'SC': None, 'XMM':    16, 'YMM':    32, 'ZMM':   64},
        { 'Inst':'PD2PI', 'SC':   16, 'XMM':  None, 'YMM':  None, 'ZMM': None},
        { 'Inst':'PH2PS', 'SC': None, 'XMM':     8, 'YMM':    16, 'ZMM':   32},
        { 'Inst':'PI2PS', 'SC':    8, 'XMM':  None, 'YMM':  None, 'ZMM': None},
        { 'Inst':'PI2PD', 'SC':    8, 'XMM':  None, 'YMM':  None, 'ZMM': None},
        { 'Inst':'PS2DQ', 'SC': None, 'XMM':    16, 'YMM':    32, 'ZMM':   64},
        { 'Inst':'PS2PH', 'SC': None, 'XMM':    16, 'YMM':    32, 'ZMM':   64},
        { 'Inst':'PS2PD', 'SC': None, 'XMM':     8, 'YMM':    16, 'ZMM':   32},
        { 'Inst':'PS2QQ', 'SC': None, 'XMM':     8, 'YMM':    16, 'ZMM':   32},
        { 'Inst':'PS2PI', 'SC':    8, 'XMM':  None, 'YMM':  None, 'ZMM': None},
        { 'Inst':'QQ2PS', 'SC': None, 'XMM':    16, 'YMM':    32, 'ZMM':   64},
        { 'Inst':'QQ2PD', 'SC': None, 'XMM':    16, 'YMM':    32, 'ZMM':   64},
        { 'Inst':'SD2SS', 'SC':    8, 'XMM':  None, 'YMM':  None, 'ZMM': None},
        { 'Inst':'SD2SI', 'SC':    8, 'XMM':  None, 'YMM':  None, 'ZMM': None},
        { 'Inst':'SI2SS', 'SC':    8, 'XMM':  None, 'YMM':  None, 'ZMM': None},
        { 'Inst':'SI2SD', 'SC':    8, 'XMM':  None, 'YMM':  None, 'ZMM': None},
        { 'Inst':'SS2SI', 'SC':    4, 'XMM':  None, 'YMM':  None, 'ZMM': None}
        ]
    return calculate_ops_counts_per_iter(in_row, opc_table, 'CVT')

def calculate_iops_counts_per_iter(in_row):
    def calculate_iops_counts_with_weights(in_row, w_sc, w_vec_xmm, w_vec_ymm, w_vec_zmm, w_sad, w_fma):
        def calculate_iops(iops_per_instr, instr_template, itypes):
            ans = 0
            for itype in itypes:
                ans += (iops_per_instr * getter(in_row, instr_template.format(itype)))
            return ans
        

            
        iops = 0
        itypes = ['ADD_SUB', 'CMP', 'MUL' ]
        iops_sc = calculate_iops(w_sc, 'Nb_scalar_INT_arith_insn_{}', itypes)
        iops_xmm = calculate_iops(w_vec_xmm, 'Nb_INT_arith_insn_{}_XMM', itypes)
        iops_ymm = calculate_iops(w_vec_ymm, 'Nb_INT_arith_insn_{}_YMM', itypes)
        iops_zmm = calculate_iops(w_vec_zmm, 'Nb_INT_arith_insn_{}_ZMM', itypes)    
            

        itypes = ['AND', 'XOR', 'OR', 'SHIFT']
        iops_sc += calculate_iops(w_sc, 'Nb_scalar_INT_logic_insn_{}', itypes)
        iops_xmm += calculate_iops(w_vec_xmm, 'Nb_INT_logic_insn_{}_XMM', itypes)
        iops_ymm += calculate_iops(w_vec_ymm, 'Nb_INT_logic_insn_{}_YMM', itypes)
        iops_zmm += calculate_iops(w_vec_zmm, 'Nb_INT_logic_insn_{}_ZMM', itypes)    
        # try to add the TEST, ANDN, FMA and SAD counts (they have not scalar count)
        # TODO: Need to check why ANDN and TEST instructions are included in FMA counting.
        iops_fma_xmm = w_vec_xmm * (getter(in_row, 'Nb_INT_logic_insn_ANDN_XMM') + getter(in_row, 'Nb_INT_logic_insn_TEST_XMM')
                                 + w_fma * getter(in_row, 'Nb_INT_arith_insn_FMA_XMM'))
        iops_xmm += iops_fma_xmm
        iops_fma_ymm = w_vec_ymm*(getter(in_row, 'Nb_INT_logic_insn_ANDN_YMM') + getter(in_row, 'Nb_INT_logic_insn_TEST_YMM')
                               + w_fma * getter(in_row, 'Nb_INT_arith_insn_FMA_YMM'))
        iops_ymm += iops_fma_ymm
        iops_fma_zmm = w_vec_zmm*(getter(in_row, 'Nb_INT_logic_insn_ANDN_ZMM') + getter(in_row, 'Nb_INT_logic_insn_TEST_ZMM')
                               + w_fma * getter(in_row, 'Nb_INT_arith_insn_FMA_ZMM'))
        iops_zmm += iops_fma_zmm
        iops_fma = iops_fma_xmm + iops_fma_ymm + iops_fma_zmm

        # For 128bit (XMM) SAD instructions, 1 instruction does
        # 1) 32 8-bit SUB
        # 2) 32 8-bit ABS
        # 3) 24 16-bit ADD
        # Ignoring 2), 1 XMM instruction generates/processes 32*8+24*16=640 bits = 10 DP element(64-bit)
        # Similar scaling, YMM = 20 DP, ZMM = 40DP
        iops_xmm += w_vec_xmm*(w_sad * getter(in_row, 'Nb_INT_arith_insn_SAD_XMM'))
        iops_ymm += w_vec_ymm*(w_sad * getter(in_row, 'Nb_INT_arith_insn_SAD_YMM'))
        iops_zmm += w_vec_zmm*(w_sad * getter(in_row, 'Nb_INT_arith_insn_SAD_ZMM'))

        iops = iops_sc + iops_xmm + iops_ymm + iops_zmm
        results = [(ops * getter(in_row, 'decan_experimental_configuration.num_core')) \
            for ops in [iops ,iops_sc, iops_xmm, iops_ymm, iops_zmm, iops_fma, 0, 0, 0, 0]]
        return Vecinfo(*results)

    iops_counts = calculate_iops_counts_with_weights(in_row, w_sc=0.5, w_vec_xmm=2, w_vec_ymm=4, w_vec_zmm=8, w_sad=5, w_fma=2)
    insts_counts = calculate_iops_counts_with_weights(in_row, w_sc=1, w_vec_xmm=1, w_vec_ymm=1, w_vec_zmm=1, w_sad=1, w_fma=1)    
    return iops_counts, insts_counts

def calculate_memops_counts_per_iter(in_row):
    def calculate_memops_counts_with_weights(in_row, w_sc_8bit, w_sc_16bit, w_sc_32bit, w_sc_64bit, w_vec_xmm, w_vec_ymm, w_vec_zmm):

        # Note that Nb_MOVH/LPS/D_loads and Nb_MOVH/LPS/D_stores are 64bits
        # See: (https://www.felixcloutier.com/x86/movhps, https://www.felixcloutier.com/x86/movhpd)

        memops_sc = w_sc_8bit * (getter(in_row, 'Nb_8_bits_loads') + getter(in_row, 'Nb_8_bits_stores')) \
                   + w_sc_16bit * (getter(in_row, 'Nb_16_bits_loads') + getter(in_row, 'Nb_16_bits_stores')) \
                   + w_sc_32bit * (getter(in_row, 'Nb_32_bits_loads') + getter(in_row, 'Nb_32_bits_stores')) \
                   + w_sc_64bit * (getter(in_row, 'Nb_64_bits_loads') + getter(in_row, 'Nb_64_bits_stores')) \
                   + w_sc_64bit * (getter(in_row, 'Nb_MOVH/LPS/D_loads') + getter(in_row, 'Nb_MOVH/LPS/D_stores'))                   

        memops_xmm = w_vec_xmm * (getter(in_row, 'Nb_128_bits_loads') + getter(in_row, 'Nb_128_bits_stores'))
        memops_ymm = w_vec_ymm * (getter(in_row, 'Nb_256_bits_loads') + getter(in_row, 'Nb_256_bits_stores'))
        memops_zmm = w_vec_zmm * (getter(in_row, 'Nb_512_bits_loads') + getter(in_row, 'Nb_512_bits_stores'))
        memops = memops_sc + memops_xmm + memops_ymm + memops_zmm
        memops_fma = memops_div = memops_sqrt = memops_rsqrt = memops_rcp = memops_cvt = 0

        results = (memops, memops_sc, memops_xmm, memops_ymm, memops_zmm, memops_fma, 
                   memops_div, memops_sqrt, memops_rsqrt, memops_rcp, memops_cvt)
        return Vecinfo(*results)    
    
    memops_counts = calculate_memops_counts_with_weights(in_row, w_sc_8bit=1/8, w_sc_16bit=1/4, w_sc_32bit=1/2, w_sc_64bit=1, \
                                                         w_vec_xmm=2, w_vec_ymm=4, w_vec_zmm=8)
    insts_counts = calculate_memops_counts_with_weights(in_row, w_sc_8bit=1, w_sc_16bit=1, w_sc_32bit=1, w_sc_64bit=1, \
                                                         w_vec_xmm=1, w_vec_ymm=1, w_vec_zmm=1)
    return memops_counts, insts_counts


def vector_ext_str(type2percent):
    return ";".join("%s=%.1f%%" % (x, y * 100) for x, y in type2percent if not (y is None or y < 0.001 or (x == "SC" and y != 1)))
    
def find_vector_ext(op_counts):
    if op_counts is None:
        op_counts = Vecinfo()
        
    out = zip([ "SC", "XMM", "YMM", "ZMM" ],
              [ getattr(op_counts, metric) / (op_counts.SUM) \
                  if op_counts.SUM  else None \
                      for metric in ["SC", "XMM", "YMM", "ZMM"] ])
    return vector_ext_str(out)

def calculate_energy_derived_metrics(out_row, kind, energy, num_ops, ops_per_sec):
    try:
        out_row[MetricName.epo(kind)] = energy / num_ops
    except:
        out_row[MetricName.epo(kind)] = math.nan
    try:
        out_row[MetricName.rpe(kind)] = ops_per_sec / energy 
    except:
        out_row[MetricName.rpe(kind)] = math.nan
    try:
        out_row[MetricName.rope(kind)] = (ops_per_sec * num_ops) / energy
    except:
        out_row[MetricName.rope(kind)] = math.nan

def getter(in_row, *argv, **kwargs):
    type_ = kwargs.pop('type', float)
    default_ = kwargs.pop('default', 0)
    result = None
    for arg in argv:
        if (arg.startswith('Nb_insn') and arg not in in_row):
            arg = 'Nb_FP_insn' + arg[7:]
        if (arg in in_row):
            result = in_row[arg] if result is None or pd.isna(result) else result
    if result is not None:
        return type_(default_ if pd.isna(result) else result)
    raise IndexError(', '.join(map(str, argv)))

def compute_speedup(output_rows, mapping_df):
    # keyColumns=[NAME, TIMESTAMP, VARIANT]
    timeColumns=[TIME_LOOP_S, TIME_APP_S]
    rateColumns=[RATE_FP_GFLOP_P_S]
    # perf_df = output_rows[keyColumns + timeColumns + rateColumns]
    perf_df = output_rows[KEY_METRICS + timeColumns + rateColumns]

    # new_mapping_df = pd.merge(mapping_df, perf_df, left_on=['Before Name', 'Before Timestamp', 'Before Variant'], 
    #                           right_on=keyColumns, how='left')
    # new_mapping_df = pd.merge(new_mapping_df, perf_df, left_on=['After Name', 'After Timestamp', 'After Variant'], 
    #                           right_on=keyColumns, suffixes=('_before', '_after'), how='left')
    new_mapping_df = pd.merge(mapping_df, perf_df, left_on=['Before Name', 'Before Timestamp'], 
                              right_on=KEY_METRICS, how='left')
    new_mapping_df = pd.merge(new_mapping_df, perf_df, left_on=['After Name', 'After Timestamp'], 
                              right_on=KEY_METRICS, suffixes=('_before', '_after'), how='left')
    for timeColumn in timeColumns: 
        new_mapping_df['Speedup[{}]'.format(timeColumn)] = \
            new_mapping_df['{}_before'.format(timeColumn)] / new_mapping_df['{}_after'.format(timeColumn)]
    for rateColumn in rateColumns: 
        new_mapping_df['Speedup[{}]'.format(rateColumn)] = \
            new_mapping_df['{}_after'.format(rateColumn)] / new_mapping_df['{}_before'.format(rateColumn)]
    # Remove those _after and _before columns
    retainColumns = filter(lambda a: not a.endswith('_after'), new_mapping_df.columns)
    retainColumns = filter(lambda a: not a.endswith('_before'), list(retainColumns))
    return new_mapping_df[retainColumns]

    
def clear_dataframe(df):
    df.drop(columns=df.columns, inplace=True)
    df.drop(df.index, inplace=True)

def replace_dataframe_content(to_df, from_df):
    clear_dataframe(to_df)
    for col in from_df.columns:
        to_df[col] = from_df[col]

def import_dataframe_columns(to_df, from_df, cols):
    merged = pd.merge(left=to_df, right=from_df[KEY_METRICS+list(cols)], on=KEY_METRICS, how='left')      
    merged = merged.set_index(to_df.index)
    assert to_df[MetricName.NAME].equals(merged[MetricName.NAME])
    assert to_df[MetricName.TIMESTAMP].astype('int64').equals(merged[MetricName.TIMESTAMP].astype('int64'))
    for col in cols:
        if col + "_y" in merged.columns and col + "_x" in merged.columns:
            # _y is incoming df data so use it and fill in _x (original) if missing
            merged[col] = merged[col + "_y"].fillna(merged[col + "_x"])
        to_df[col] = merged[col]
    
def append_dataframe_rows(df, append_df):
    merged = df.append(append_df, ignore_index=True)
    replace_dataframe_content(df, merged)


# pandas version <1.2 does not support crossjoin so here is a simple implementation.
def crossjoin(df1, df2, suffixes=("_x", "_y")):
    df1['_tmp'] = 1
    df2['_tmp'] = 1
    join_results = pd.merge(df1, df2, on='_tmp', suffixes=suffixes).drop('_tmp', axis=1)
    df1.drop('_tmp', inplace=True, axis=1)
    df2.drop('_tmp', inplace=True, axis=1)
    return join_results