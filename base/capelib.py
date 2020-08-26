import re
from collections import namedtuple
import pandas as pd

# Common routines needed for Cape tool chain

Vecinfo = namedtuple('Vecinfo', ['SUM','SC','XMM','YMM','ZMM', 'FMA', \
    'DIV', 'SQRT', 'RSQRT', 'RCP', 'CVT'])

def succinctify(value):
    def helper(x):
        x = x[:x.index(')')] if ')' in x else x
        return x.lower().strip().replace(' ', '_').replace('_(', '_').replace('._','_')
    if isinstance(value, str):
        return helper(value)
    else:
        return list(map(helper,value))

def add_mem_max_level_columns(inout_df, node_list, max_rate_name, metric_to_memlevel_lambda):
	inout_df[max_rate_name]=inout_df[node_list].max(axis=1)
    # TODO: Comment out below to avoid creating new df.  Need to fix if notna() check needed
	# inout_df = inout_df[inout_df[max_rate_name].notna()]
	inout_df['memlevel']=inout_df[node_list].idxmax(axis=1)
	inout_df['memlevel'] = inout_df['memlevel'].apply(metric_to_memlevel_lambda)
    # Old stuff below to be deleted
	# Remove the first two characters which is 'C_'
    # inout_df['memlevel'] = inout_df['memlevel'].apply((lambda v: v[2:]))
	# Drop the unit
	# inout_df['memlevel'] = inout_df['memlevel'].str.replace(" \[.*\]","", regex=True)

# For CQA metrics
def calculate_all_rate_and_counts(out_row, in_row, iterations_per_rep, time):
    vec_ops = all_ops = vec_insts = all_insts = fma_ops = fma_insts = 0
    itypes = ['FMA', 'DIV', 'SQRT', 'RSQRT', 'RCP', 'CVT']
    ops_dict = {itype : 0 for itype in itypes}
    inst_dict = {itype : 0 for itype in itypes}

    def calculate_rate_and_counts(rate_name, calculate_counts_per_iter, add_global_count):
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
            out_row[rate_name] = (cnts_per_iter.SUM * iterations_per_rep) / (1E9 * time)

            if add_global_count:
                vec_ops += (cnts_per_iter.XMM + cnts_per_iter.YMM + cnts_per_iter.ZMM)
                all_ops += cnts_per_iter.SUM

                vec_insts += (inst_cnts_per_iter.XMM + inst_cnts_per_iter.YMM + inst_cnts_per_iter.ZMM)
                all_insts += inst_cnts_per_iter.SUM
                for itype in itypes:
                    ops_dict[itype] += getattr(cnts_per_iter, itype)
                    inst_dict[itype] += getattr(inst_cnts_per_iter, itype)

            return cnts_per_iter, inst_cnts_per_iter
        except:
            return None, None

    flop_cnts_per_iter, fl_inst_cnts_per_iter = calculate_rate_and_counts('FLOP Rate (GFLOP/s)', calculate_flops_counts_per_iter, True)
    iop_cnts_per_iter, i_inst_cnts_per_iter = calculate_rate_and_counts('IOP Rate (GIOP/s)', calculate_iops_counts_per_iter, False)
    # Note: enabled global count so CVT insts will be contributing to total inst/op count in evaulating %Inst, %Vec metrics
    cvt_cnts_per_iter, cvt_inst_cnts_per_iter = calculate_rate_and_counts('CVTOP Rate (GCVTOP/s)', calculate_cvtops_counts_per_iter, True)
    memop_cnts_per_iter, mem_inst_cnts_per_iter = calculate_rate_and_counts('MEMOP Rate (GMEMOP/s)', calculate_memops_counts_per_iter, True)

    out_row['%Ops[Vec]'] = 100 * vec_ops / all_ops if all_ops else 0
    out_row['%Inst[Vec]'] = 100 * vec_insts / all_insts if all_insts else 0
    for itype in itypes:
        out_row['%Ops[{}]'.format(itype)] = 100 * ops_dict[itype] / all_ops if all_ops else 0
        out_row['%Inst[{}]'.format(itype)] = 100 * inst_dict[itype] / all_insts if all_insts else 0

    try:
        # Check if CQA metric is available
        cqa_vec_ratio=in_row['Vec._ratio_(%)_all']
        if not math.isclose(cqa_vec_ratio, out_row['%Inst[Vec]'], rel_tol=1e-8):
            warnings.warn("CQA Vec. ration not matching computed: CQA={}, Computed={}, AllIters={}".format \
                          (cqa_vec_ratio, out_row['%Inst[Vec]'], in_row['AllIterations']))
            # Just set to CQA value for now.  (Pending check with Emmanuel)
            out_row['%Inst[Vec]'] = cqa_vec_ratio
    except:
        pass
    out_row['VecType[Ops]']=find_vector_ext(flop_cnts_per_iter, iop_cnts_per_iter)


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
        return Vecinfo(*results, 0.0)

    flops_counts = calculate_flops_counts_with_weights(in_row, 0.5, 1, 2, 4, 8, 2)
    insts_counts = calculate_flops_counts_with_weights(in_row, 1, 1, 1, 1, 1, 1)
    return flops_counts, insts_counts

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
        matchobj = re.search(r'Nb_insn_(.+?)_(.MM)$', cvt_col_name)
        if matchobj:
            inst = matchobj.group(1)
            regtype = matchobj.group(2)
        else:
            # match again to get rid of Nb_insn_
            matchobj = re.search(r'Nb_insn_(.+?)$', cvt_col_name)
            inst = matchobj.group(1)
            regtype = 'SC'
        insts = in_row[cvt_col_name]
        ops = insts * opc_df.loc[opc_df.Inst == inst, regtype].values[0]
        opcount[regtype] += ops
        opcount['SUM'] += ops
        icount[regtype] += insts
        icount['SUM'] += insts
        
    return Vecinfo(opcount['SUM'], opcount['SC'], opcount['XMM'], opcount['YMM'], opcount['ZMM'], 
                   0, 0, 0, 0, 0, opcount['SUM']), \
                       Vecinfo(icount['SUM'], icount['SC'], icount['XMM'], icount['YMM'], icount['ZMM'], 
                               0, 0, 0, 0, 0, icount['SUM'])

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
        return Vecinfo(*results, 0.0)

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
    
def find_vector_ext(flop_counts, iop_counts):
    if iop_counts is None:
        iop_counts = Vecinfo(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    if flop_counts is None:
        flop_counts = Vecinfo(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
    out = zip([ "SC", "XMM", "YMM", "ZMM" ],
              [ (getattr(flop_counts, metric) + getattr(iop_counts, metric)) / (flop_counts.SUM + iop_counts.SUM) \
                  if flop_counts.SUM or iop_counts.SUM else None \
                      for metric in ["SC", "XMM", "YMM", "ZMM"] ])
    return vector_ext_str(out)

def calculate_energy_derived_metrics(out_row, kind, energy, num_ops, ops_per_sec):
    out_row['E[{}]/O (J/GI)'.format(kind)] = energy / num_ops
    out_row['C/E[{}] (GI/Js)'.format(kind)] = ops_per_sec / energy
    out_row['CO/E[{}] (GI2/Js)'.format(kind)] = (ops_per_sec * num_ops) / energy

def getter(in_row, *argv, **kwargs):
    type_ = kwargs.pop('type', float)
    default_ = kwargs.pop('default', 0)
    for arg in argv:
        if (arg.startswith('Nb_insn') and arg not in in_row):
            arg = 'Nb_FP_insn' + arg[7:]
        if (arg in in_row):
            # should use None test because 0 is valid number and considered False in Python.
            return type_(in_row[arg] if in_row[arg] is not None else default_)
    raise IndexError(', '.join(map(str, argv)))
