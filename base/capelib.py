from collections import namedtuple

# Common routines needed for Cape tool chain

Vecinfo = namedtuple('Vecinfo', ['SUM','SC','XMM','YMM','ZMM', 'FMA'])

def succinctify(value):
    def helper(x):
        x = x[:x.index(')')] if ')' in x else x
        return x.lower().strip().replace(' ', '_').replace('_(', '_').replace('._','_')
    if isinstance(value, str):
        return helper(value)
    else:
        return list(map(helper,value))

# For CQA metrics
def calculate_all_rate_and_counts(out_row, in_row, iterations_per_rep, time):
    vec_ops = all_ops = vec_insts = all_insts = fma_ops = fma_insts = 0
    def calculate_rate_and_counts(rate_name, calculate_counts_per_iter, add_global_count):
        try:
            nonlocal all_ops
            nonlocal all_insts
            nonlocal vec_ops
            nonlocal vec_insts
            nonlocal fma_ops                        
            nonlocal fma_insts            

            cnts_per_iter, inst_cnts_per_iter=calculate_counts_per_iter(in_row)
            out_row[rate_name] = (cnts_per_iter.SUM * iterations_per_rep) / (1E9 * time)

            if add_global_count:
                vec_ops += (cnts_per_iter.XMM + cnts_per_iter.YMM + cnts_per_iter.ZMM)
                fma_ops += cnts_per_iter.FMA
                all_ops += cnts_per_iter.SUM

                vec_insts += (inst_cnts_per_iter.XMM + inst_cnts_per_iter.YMM + inst_cnts_per_iter.ZMM)
                fma_insts += inst_cnts_per_iter.FMA
                all_insts += inst_cnts_per_iter.SUM

            return cnts_per_iter, inst_cnts_per_iter
        except:
            return None, None

    flop_cnts_per_iter, fl_inst_cnts_per_iter = calculate_rate_and_counts('FLOP Rate (GFLOP/s)', calculate_flops_counts_per_iter, True)
    iop_cnts_per_iter, i_inst_cnts_per_iter = calculate_rate_and_counts('IOP Rate (GIOP/s)', calculate_iops_counts_per_iter, False)
    memop_cnts_per_iter, mem_inst_cnts_per_iter = calculate_rate_and_counts('MEMOP Rate (GMEMOP/s)', calculate_memops_counts_per_iter, True)

    out_row['%Ops[Vec]'] = vec_ops / all_ops if all_ops else None
    out_row['%Inst[Vec]'] = vec_insts / all_insts if all_insts else None
    out_row['%Ops[FMA]'] = fma_ops / all_ops if all_insts else None    
    out_row['%Inst[FMA]'] = fma_insts / all_insts if all_insts else None

    try:
        # Check if CQA metric is available
        cqa_vec_ratio=in_row['Vec._ratio_(%)_all']/100
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
            itypes = ['ADD_SUB', 'DIV', 'MUL', 'SQRT', 'RSQRT', 'RCP']
            ans=0
            for itype in itypes:
                ans += (flops_per_sp_inst * getter(in_row, sp_inst_template.format(itype)) + flops_per_dp_inst * getter(in_row, dp_inst_template.format(itype)))
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
            results = (flops, flops_sc, flops_xmm, flops_ymm, flops_zmm, flops_fma)
        except:

            flops_sc = calculate_flops(w_sc_sp, w_sc_dp, 'Nb_FP_insn_{}SS', 'Nb_FP_insn_{}SD')
            flops_xmm = calculate_flops(w_vec_xmm, w_vec_xmm, 'Nb_FP_insn_{}PS_XMM', 'Nb_FP_insn_{}PD_XMM')
            flops_ymm = calculate_flops(w_vec_ymm, w_vec_ymm, 'Nb_FP_insn_{}PS_YMM', 'Nb_FP_insn_{}PD_YMM')
            flops_zmm = calculate_flops(w_vec_zmm, w_vec_zmm, 'Nb_FP_insn_{}PS_ZMM', 'Nb_FP_insn_{}PD_ZMM')
    
    
            # try to add the FMA counts
            flops_fma_sc =  w_fma * (w_sc_sp * getter(in_row, 'Nb_FP_insn_FMASS') + w_sc_dp * getter(in_row, 'Nb_FP_insn_FMASD'))
            flops_sc += flops_fma_sc
            flops_fma_xmm = w_fma * w_vec_xmm*(getter(in_row, 'Nb_FP_insn_FMAPS_XMM') + getter(in_row, 'Nb_FP_insn_FMAPD_XMM'))
            flops_xmm += flops_fma_xmm
            flops_fma_ymm = w_fma * w_vec_ymm*(getter(in_row, 'Nb_FP_insn_FMAPS_YMM')  + getter(in_row, 'Nb_FP_insn_FMAPD_YMM'))
            flops_ymm += flops_fma_ymm
            flops_fma_zmm = w_fma * w_vec_zmm*(getter(in_row, 'Nb_FP_insn_FMAPS_ZMM') + getter(in_row, 'Nb_FP_insn_FMAPD_ZMM'))
            flops_zmm += flops_fma_zmm
            flops_fma = flops_fma_sc + flops_fma_xmm + flops_fma_ymm + flops_fma_zmm

            flops = flops_sc + flops_xmm + flops_ymm + flops_zmm

    
#            results = (flops, flops_sc, flops_xmm, flops_ymm, flops_zmm)

            # Multiple to get count for all cores
            results = [(ops * getter(in_row, 'decan_experimental_configuration.num_core')) for ops in [flops , flops_sc, flops_xmm, flops_ymm, flops_zmm, flops_fma]]            
        return Vecinfo(*results)

    flops_counts = calculate_flops_counts_with_weights(in_row, 0.5, 1, 2, 4, 8, 2)
    insts_counts = calculate_flops_counts_with_weights(in_row, 1, 1, 1, 1, 1, 1)
    return flops_counts, insts_counts

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
        results = [(ops * getter(in_row, 'decan_experimental_configuration.num_core')) for ops in [iops ,iops_sc, iops_xmm, iops_ymm, iops_zmm, iops_fma]]
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
        memops_fma = 0

        results = (memops, memops_sc, memops_xmm, memops_ymm, memops_zmm, memops_fma)
        return Vecinfo(*results)    
    
    memops_counts = calculate_memops_counts_with_weights(in_row, w_sc_8bit=1/8, w_sc_16bit=1/4, w_sc_32bit=1/2, w_sc_64bit=1, \
                                                         w_vec_xmm=2, w_vec_ymm=4, w_vec_zmm=8)
    insts_counts = calculate_memops_counts_with_weights(in_row, w_sc_8bit=1, w_sc_16bit=1, w_sc_32bit=1, w_sc_64bit=1, \
                                                         w_vec_xmm=1, w_vec_ymm=1, w_vec_zmm=1)
    return memops_counts, insts_counts


def find_vector_ext(flop_counts, iop_counts):
    if iop_counts is None:
        iop_counts = Vecinfo(0,0,0,0,0,0)
    if flop_counts is None:
        flop_counts = Vecinfo(0,0,0,0,0,0)
        
    out = zip([ "SC", "XMM", "YMM", "ZMM" ],
              [ (getattr(flop_counts, metric) + getattr(iop_counts, metric)) / (flop_counts.SUM + iop_counts.SUM) if flop_counts.SUM or iop_counts.SUM else None \
                for metric in ["SC", "XMM", "YMM", "ZMM"] ])
    return ";".join("%s=%.1f%%" % (x, y * 100) for x, y in out if not (y is None or y < 0.001 or (x == "SC" and y != 1)))


def getter(in_row, *argv, **kwargs):
    type_ = kwargs.pop('type', float)
    default_ = kwargs.pop('default', 0)
    for arg in argv:
        if (arg.startswith('Nb_insn') and arg not in in_row):
            arg = 'Nb_FP_insn' + arg[7:]
        if (arg in in_row):
            return type_(in_row[arg] if in_row[arg] else default_)
    raise IndexError(', '.join(map(str, argv)))
