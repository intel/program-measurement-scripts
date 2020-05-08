#!/usr/bin/python3
import csv, re
import sys
import traceback

from operator import attrgetter
from openpyxl import Workbook
from openpyxl import load_workbook
from capelib import succinctify
from collections import OrderedDict
from collections import namedtuple
from argparse import ArgumentParser
from enum import Enum
import tempfile
import math
import os
import pandas as pd
import warnings

# At least Python version 3.6 is required
assert sys.version_info >= (3,6)

args = None
variants = {}
short_names = {}
field_names = [ 'Name', 'Short Name', 'Variant', 'Num. Cores','DataSet/Size','prefetchers','Repetitions', 'VecType[Ops]', 'Time (s)',
                'O=Inst. Count (GI)', 'C=Inst. Rate (GI/s)',
                'Total PKG Energy (J)', 'Total PKG Power (W)',
                'E[PKG]/O (J/GI)', 'C/E[PKG] (GI/Js)', 'CO/E[PKG] (GI2/Js)',
                'Total DRAM Energy (J)', 'Total DRAM Power (W)',
                'E[DRAM]/O (J/GI)', 'C/E[DRAM] (GI/Js)', 'CO/E[DRAM] (GI2/Js)',
                'Total PKG+DRAM Energy (J)', 'Total PKG+DRAM Power (W)',
                'E[PKG+DRAM]/O (J/GI)', 'C/E[PKG+DRAM] (GI/Js)', 'CO/E[PKG+DRAM] (GI2/Js)',
                '%Misp. Branches', 'Executed/Retired Uops',
                'Register ADDR Rate (GB/s)', 'Register DATA Rate (GB/s)', 'Register SIMD Rate (GB/s)', 'Register Rate (GB/s)',
                'L1 Rate (GB/s)', 'L2 Rate (GB/s)', 'L3 Rate (GB/s)', 'RAM Rate (GB/s)', 'Load+Store Rate (GI/s)',
                'FLOP Rate (GFLOP/s)', 'IOP Rate (GIOP/s)', '%Ops[Vec]', '%Inst[Vec]', '%Inst[FMA]',
                '%PRF','%SB','%PRF','%RS','%LB','%ROB','%LM','%ANY','%FrontEnd' ]
Vecinfo = namedtuple('Vecinfo', ['SUM','SC','XMM','YMM','ZMM', 'FMA'])

L2R_TrafficDict={'SKL': ['L1D_REPLACEMENT'], 'HSW': ['L1D_REPLACEMENT'], 'IVB': ['L1D_REPLACEMENT'], 'SNB': ['L1D_REPLACEMENT'] }
L2W_TrafficDict={'SKL': ['L2_TRANS_L1D_WB'], 'HSW': ['L2_TRANS_L1D_WB', 'L2_DEMAND_RQSTS_WB_MISS'], 'IVB': ['L1D_WB_RQST_ALL'], 'SNB': ['L1D_WB_RQST_ALL'] }
L3R_TrafficDict={'SKL': ['L2_RQSTS_MISS'], 'HSW': ['L2_RQSTS_MISS', 'SQ_MISC_FILL_DROPPED'], 'IVB': ['L2_LINES_ALL', 'SQ_MISC_FILL_DROPPED'], 'SNB': ['L2_LINES_ALL', 'SQ_MISC_FILL_DROPPED'] }
L3W_TrafficDict={'SKL': ['L2_TRANS_L2_WB'], 'HSW': ['L2_TRANS_L2_WB', 'L2_DEMAND_RQSTS_WB_MISS'], 'IVB': ['L2_TRANS_L2_WB', 'L2_L1D_WB_RQSTS_MISS'], 'SNB':  ['L2_TRANS_L2_WB', 'L2_L1D_WB_RQSTS_MISS']}

StallDict={'SKL': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_PHT_FULL', 'LM':'RESOURCE_STALLS_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FrontEnd':'Front_end_(cycles)' },
           'HSW': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_ALL_PRF_CONTROL', 'LM':'RESOURCE_STALLS_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FrontEnd':'Front_end_(cycles)' },
           'IVB': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_ALL_PRF_CONTROL', 'LM':'RESOURCE_STALLS_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FrontEnd':'Front_end_(cycles)' },
           'SNB': { 'RS': 'RESOURCE_STALLS_RS', 'LB': 'RESOURCE_STALLS_LB', 'SB': 'RESOURCE_STALLS_SB', 'ROB': 'RESOURCE_STALLS_ROB', 
                    'PRF': 'RESOURCE_STALLS2_ALL_PRF_CONTROL', 'LM':'RESOURCE_STALLS2_LOAD_MATRIX', 'ANY': 'RESOURCE_STALLS_ANY', 'FrontEnd':'Front_end_(cycles)' }}

def find_vector_ext(flop_counts, iop_counts):
    if iop_counts is None:
        iop_counts = Vecinfo(0,0,0,0,0)
    if flop_counts is None:
        flop_counts = Vecinfo(0,0,0,0,0)
        
    out = zip([ "SC", "XMM", "YMM", "ZMM" ],
              [ (getattr(flop_counts, metric) + getattr(iop_counts, metric)) / (flop_counts.SUM + iop_counts.SUM) if flop_counts.SUM or iop_counts.SUM else None \
                for metric in ["SC", "XMM", "YMM", "ZMM"] ])
    return ";".join("%s=%.1f%%" % (x, y * 100) for x, y in out if not (y is None or y < 0.001 or (x == "SC" and y != 1)))

def counter_sum(row, cols):
    sum = 0
    for col in cols:
        sum = sum + getter(row, col)
    return sum

def arch_helper(row):
    arch = row['cpu.generation'].lower()
    if 'skylake' in arch:
        return 'SKL'
    elif 'haswell' in arch:
        return 'HSW'
    elif 'ivy' in arch:
        return 'IVB'
    elif 'sandy' in arch:
        return 'SNB'
    else:
        return None


def calculate_codelet_name(out_row, in_row):
    out_row['Name'] = '{0}: {1}'.format(
        getter(in_row, 'application.name', type=str),
        getter(in_row, 'codelet.name', type=str))
    if out_row['Name'] in short_names:
        out_row['Short Name'] = short_names[out_row['Name']]
    out_row['Variant'] = variants[out_row['Name']] if out_row['Name'] in variants \
        else getter(in_row, 'decan_variant.name', type=str)

def calculate_expr_settings(out_row, in_row):
    out_row['Num. Cores']=getter(in_row, 'decan_experimental_configuration.num_core')
    out_row['DataSet/Size']=getter(in_row, 'decan_experimental_configuration.data_size', type=str)
    try:
        out_row['prefetchers']=getter(in_row, 'prefetchers')
    except:
        out_row['prefetchers']='unknown'
    try:
        out_row['Repetitions']=getter(in_row, 'Repetitions')
    except:        
        out_row['Repetitions']=1

def calculate_iterations_per_rep(in_row):
    try:
        return getter(in_row, 'Iterations') / getter(in_row, 'Repetitions')
    except:
        # For Oneview there is no Repetitions just return Iterations
        return getter(in_row, 'Iterations') 

def print_iterations_per_rep_formula(formula_file):
    formula_file.write('iterations_per_rep = Iterations / Repetitions\n')

def calculate_time(out_row, in_row, iterations_per_rep, use_cpi):
    if use_cpi:
        time = getter(in_row, 'CPI')
    else:
        time = getter(in_row, 'CPU_CLK_UNHALTED_REF_TSC') / getter(in_row, 'decan_experimental_configuration.num_core')
    out_row['Time (s)'] = time * iterations_per_rep/(getter(in_row, 'cpu.nominal_frequency', 'decan_experimental_configuration.frequency') * 1e3)
    return out_row['Time (s)']

def print_time_formula(formula_file):
    formula_file.write('Time (s) = (CPU_CLK_UNHALTED_THREAD * iterations_per_rep) /' +
                                         ' (decan_experimental_configuration.frequency * 1E3)\n')



def print_total_pkg_energy_formula(formula_file):
    formula_file.write('Total PKG Energy (J) = (UNC_PKG_ENERGY_STATUS or FREERUN_PKG_ENERGY_STATUS) * energy.unit *' +
                       ' iterations_per_rep\n')

def print_total_dram_energy_formula(formula_file):
    formula_file.write('Total DRAM Energy (J) = (UNC_DDR_ENERGY_STATUS or FREERUN_DRAM_ENERGY_STATUS) * energy.unit *' +
                                         ' iterations_per_rep\n')

def user_op_to_rate_column_name(user_op_column):
    matchobj = re.search(r'(.+?) \((.+?)\)', user_op_column)
    op_name=matchobj.group(1)
    unit_name=matchobj.group(2)
    return "{} Rate (G{}/s)".format(op_name, unit_name)
        
    
def calculate_user_op_rate(out_row, in_row, time_per_rep, user_op_column_name_dict):
    for user_op_column, rate_column_name in user_op_column_name_dict.items():
        ops_per_rep = in_row[user_op_column]
        out_row[rate_column_name]=ops_per_rep/time_per_rep/1e9


def calculate_num_insts(out_row, in_row, iterations_per_rep, time):
    insts_per_rep = ((getter(in_row, 'INST_RETIRED_ANY') * iterations_per_rep) / (1e9))
    out_row['O=Inst. Count (GI)'] = insts_per_rep
    ops_per_sec = insts_per_rep / time
    out_row['C=Inst. Rate (GI/s)'] = ops_per_sec

    vec_ops = all_ops = vec_insts = all_insts = fma_insts = 0
    def calculate_rate_and_counts(rate_name, calculate_counts_per_iter, add_global_count):
        try:
            nonlocal all_ops
            nonlocal all_insts
            nonlocal vec_ops
            nonlocal vec_insts
            nonlocal fma_insts            

            cnts_per_iter, inst_cnts_per_iter=calculate_counts_per_iter(in_row)

            out_row[rate_name] = (cnts_per_iter.SUM * iterations_per_rep) / (1E9 * time)

            if add_global_count:
                vec_ops += (cnts_per_iter.XMM + cnts_per_iter.YMM + cnts_per_iter.ZMM)
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
    return (insts_per_rep, ops_per_sec)

def print_num_ops_formula(formula_file):
    formula_file.write( \
        'Inst. Count(GI) = (INST_RETIRED_ANY * iterations_per_rep) / 1E9\n')

def getter(in_row, *argv, **kwargs):
    type_ = kwargs.pop('type', float)
    default_ = kwargs.pop('default', 0)
    for arg in argv:
        if (arg.startswith('Nb_insn') and arg not in in_row):
            arg = 'Nb_FP_insn' + arg[7:]
        if (arg in in_row):
            return type_(in_row[arg] if in_row[arg] else default_)
    raise IndexError(', '.join(map(str, argv)))

def calculate_data_rates(out_row, in_row, iterations_per_rep, time_per_rep):

    def calculate_load_store_rate():
        try:
            load_per_it  = getter(in_row, 'MEM_INST_RETIRED_ALL_LOADS', 'MEM_UOPS_RETIRED_ALL_LOADS')
            store_per_it = getter(in_row, 'MEM_INST_RETIRED_ALL_STORES', 'MEM_UOPS_RETIRED_ALL_STORES')
        except:
            load_per_it  = in_row['Nb_8_bits_loads'] + in_row['Nb_16_bits_loads'] \
                           + in_row['Nb_32_bits_loads'] + in_row['Nb_64_bits_loads'] + in_row['Nb_128_bits_loads'] \
                           + in_row['Nb_256_bits_loads'] + in_row['Nb_MOVH_LPS_D_loads']
            store_per_it = in_row['Nb_8_bits_stores'] + in_row['Nb_16_bits_stores'] \
                           + in_row['Nb_32_bits_stores'] + in_row['Nb_64_bits_stores'] + in_row['Nb_128_bits_stores'] \
                           + in_row['Nb_256_bits_stores'] + in_row['Nb_MOVH_LPS_D_stores']
        return ((load_per_it + store_per_it) * iterations_per_rep) / (1E9 * time_per_rep)

    def calculate_register_bandwidth():
        num_cores = getter(in_row, 'decan_experimental_configuration.num_core')
        reg_gp_addr_rw = getter(in_row, 'Bytes_GP_addr_read') + getter(in_row, 'Bytes_GP_addr_write')
        reg_gp_data_rw = getter(in_row, 'Bytes_GP_data_read') + getter(in_row, 'Bytes_GP_data_write')
        reg_simd_rw = getter(in_row, 'Bytes_SIMD_read') + getter(in_row, 'Bytes_SIMD_write')
        rates = [ num_cores * iterations_per_rep * x / (1E9 * time_per_rep) for x in [ \
                                                                                       reg_gp_addr_rw, reg_gp_data_rw, reg_simd_rw \
                                                                                   ]]
        return rates + [ sum(rates) ]

    try:
        arch = arch_helper(in_row)

        L2_rc_per_it  = counter_sum(in_row, L2R_TrafficDict[arch])
        L2_wc_per_it  = counter_sum(in_row, L2W_TrafficDict[arch])
        L3_rc_per_it  = counter_sum(in_row, L3R_TrafficDict[arch])
        L3_wc_per_it  = counter_sum(in_row, L3W_TrafficDict[arch])

        ram_rc_per_it = getter(in_row, 'UNC_M_CAS_COUNT_RD', 'UNC_IMC_DRAM_DATA_READS')
        ram_wc_per_it = getter(in_row, 'UNC_M_CAS_COUNT_WR', 'UNC_IMC_DRAM_DATA_WRITES')


        L2_rwb_per_it  = (L2_rc_per_it  + L2_wc_per_it) * 64
        L3_rwb_per_it  = (L3_rc_per_it  + L3_wc_per_it) * 64
        ram_rwb_per_it = (ram_rc_per_it + ram_wc_per_it) * 64

        out_row['L2 Rate (GB/s)']  = (L2_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
        out_row['L3 Rate (GB/s)']  = (L3_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
        out_row['RAM Rate (GB/s)'] = (ram_rwb_per_it * iterations_per_rep) / (1E9 * time_per_rep)
        out_row['Load+Store Rate (GI/S)'] = calculate_load_store_rate()
    except:
        pass

    try:
        L1_rb_per_it  = getter(in_row, 'Bytes_loaded') * getter(in_row, 'decan_experimental_configuration.num_core')
        L1_wb_per_it  = getter(in_row, 'Bytes_stored') * getter(in_row, 'decan_experimental_configuration.num_core')
        L1_rwb_per_it  = (L1_rb_per_it  + L1_wb_per_it)
        out_row['L1 Rate (GB/s)']  = (L1_rwb_per_it  * iterations_per_rep) / (1E9 * time_per_rep)
    except:
        # This is just estimation an load if fetching 8B (64 bit)
        warnings.warn("No CQA L1 metrics, use LS instruction rate instead.")
        out_row['L1 Rate (GB/s)']  = out_row['Load+Store Rate (GI/S)'] * 8

    
    try:
        out_row['Register ADDR Rate (GB/s)'], out_row['Register DATA Rate (GB/s)'], \
        out_row['Register SIMD Rate (GB/s)'], out_row['Register Rate (GB/s)'] = calculate_register_bandwidth()
    except:
        pass


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
    


# def shorten_stall_counter(field):
#     if field == 'RESOURCE_STALLS2_ALL_PRF_CONTROL':
#         return '%PRF'
#     field = field[(len('RESOURCE_STALLS') + 1):]
#     if field == '_ALL_PRF_CONTROL':
#         return '%PRF'
#     elif field == '_PHT_FULL':
#         return '%PHT'
#     elif field == 'LOAD_MATRIX':
#         return '%LM'
#     else:
#         return '%' + field.upper()

def calculate_stall_percentages(res, row, skip_stalls):
    if skip_stalls:
        return
    try:
        arch = arch_helper(row)
        unhlt = getter(row, 'CPU_CLK_UNHALTED_THREAD')
        for buf in ['RS', 'LB', 'SB', 'ROB', 'PRF', 'LM']:
            res['%'+buf] = getter(row, StallDict[arch][buf]) / unhlt
        try:
            res['%FrontEnd'] = getter(row, StallDict[arch]['FrontEnd']) / unhlt
        except:
            warnings.warn("No CQA FrontEnd metrics, use unhlt - ANY instead.")
            res['%FrontEnd'] = (unhlt - getter(row, StallDict[arch]['ANY'])) / unhlt
            
    except:
        pass

def calculate_energy(out_row, in_row, iterations_per_rep, time, num_ops, ops_per_sec, skip_energy):
    if skip_energy:
        return
    def calculate_from_counter(counter, alt_counter):
        energy = getter(in_row, counter, alt_counter, default=None)
        return (energy * getter(in_row, 'energy.unit') * iterations_per_rep)

    def calculate_total_pkg_energy():
        return calculate_from_counter('UNC_PKG_ENERGY_STATUS', 'FREERUN_PKG_ENERGY_STATUS')
    def calculate_total_dram_energy():
        return calculate_from_counter('UNC_DDR_ENERGY_STATUS', 'FREERUN_DRAM_ENERGY_STATUS')

    def calculate_derived_metrics(kind, energy):
        out_row['Total {} Energy (J)'.format(kind)] = energy
        out_row['Total {} Power (W)'.format(kind)] = energy / time
        out_row['E[{}]/O (J/GI)'.format(kind)] = energy / num_ops
        out_row['C/E[{}] (GI/Js)'.format(kind)] = ops_per_sec / energy
        out_row['CO/E[{}] (GI2/Js)'.format(kind)] = (ops_per_sec * num_ops) / energy

    # Can extend to report PP0, PP1 but ignore for now.
    total_pkg_energy = calculate_total_pkg_energy()
    calculate_derived_metrics('PKG', total_pkg_energy)

    try:
        total_dram_energy = calculate_total_dram_energy()
        calculate_derived_metrics('DRAM', total_dram_energy)
    except:
        return

    total_energy = total_pkg_energy + total_dram_energy
    calculate_derived_metrics('PKG+DRAM', total_energy)

def calculate_speculation_ratios(out_row, in_row):
    try:
        out_row['%Misp. Branches']=getter(in_row, 'BR_MISP_RETIRED_ALL_BRANCHES') / getter(in_row, 'BR_INST_RETIRED_ALL_BRANCHES')
    except:
        pass
    try:
        out_row['Executed/Retired Uops']=getter(in_row, 'UOPS_EXECUTED_THREAD') / getter(in_row, 'UOPS_RETIRED_ALL')
    except:
        return


def build_row_output(in_row, user_op_column_name_dict, use_cpi, skip_energy, skip_stalls, succinct):
    out_row = {}
    calculate_codelet_name(out_row, in_row)
    calculate_expr_settings(out_row, in_row)
    iterations_per_rep = calculate_iterations_per_rep(in_row)
    time = calculate_time(out_row, in_row, iterations_per_rep, use_cpi)
    num_ops, ops_per_sec = calculate_num_insts(out_row, in_row, iterations_per_rep, time)
    calculate_user_op_rate(out_row, in_row, time, user_op_column_name_dict)
    calculate_speculation_ratios (out_row, in_row)
    calculate_energy(out_row, in_row, iterations_per_rep, time, num_ops, ops_per_sec, skip_energy)
    calculate_data_rates(out_row, in_row, iterations_per_rep, time)
    calculate_stall_percentages(out_row, in_row, skip_stalls)

    if succinct:
        out_row = { succinctify(k): v for k, v in out_row.items() }
    return out_row

def print_formulas(formula_file):
    print_iterations_per_rep_formula(formula_file)
    print_time_formula(formula_file)
    print_num_ops_formula(formula_file)
    formula_file.write('C=Inst. Rate (GI/s) = Inst. Count(GI) / Time(s)\n')
    print_total_pkg_energy_formula(formula_file)
    formula_file.write('Total PKG Power(W) = Total PKG Energy (J)/ Time(s)\n')
    formula_file.write('E[PKG]/O (J/GI) = Total PKG Energy (J) / Inst. Count(GI)\n')
    formula_file.write('C/E[PKG] (GI/Js) = Inst. Rate (GI/s) / Total PKG Energy(J)\n')
    formula_file.write('CO/E[PKG] (GI2/Js) = (Inst. Rate (GI/s) * Inst. Count(GI)) / Total PKG Energy(J)\n')
    print_total_dram_energy_formula(formula_file)
    formula_file.write('Total DRAM Power(W) = Total DRAM Energy (J)/ Time(s)\n')
    formula_file.write('E[DRAM]/O (J/GI) = Total DRAM Energy (J) / Inst. Count(GI)\n')
    formula_file.write('C/E[DRAM] (GI/Js) = Inst. Rate (GI/s) / Total DRAM Energy(J)\n')
    formula_file.write('CO/E[DRAM] (GI2/Js) = (Inst. Rate (GI/s) * Inst. Count(GI)) / Total DRAM Energy(J)\n')
    formula_file.write('Total PKG+DRAM Energy (J) = Total PKG Energy (J) + Total DRAM Energy (J)\n')
    formula_file.write('Total PKG+DRAM Power(W) = Total PKG+DRAM Energy (J)/ Time(s)\n')
    formula_file.write('E[PKG+DRAM]/O (J/GI) = Total PKG+DRAM Energy (J) / Inst. Count(GI)\n')
    formula_file.write('C/E[PKG+DRAM] (GI/Js) = Inst. Rate (GI/s) / Total PKG+DRAM Energy(J)\n')
    formula_file.write('CO/E[PKG+DRAM] (GI2/Js) = (Inst. Rate (GI/s) * Inst. Count(GI)) / Total PKG+DRAM Energy(J)\n')

def field_has_values(rows):
    def tmp_(field):
        return not all(field not in row for row in rows)
    return tmp_

def enforce(d, field_names):
    return { x : d.get(x, None) for x in field_names }

def unify_column_names(colnames):
    return colnames.map(lambda x: x.replace('ADD/SUB','ADD_SUB'))
    
def summary_report(inputfiles, outputfile, input_format, user_op_file, no_cqa, use_cpi, skip_energy,
                   skip_stalls, succinct, name_file):
    print('Inputfile Format: ', input_format, file=sys.stderr)
    print('Inputfiles: ', inputfiles, file=sys.stderr)
    print('Outputfile: ', outputfile, file=sys.stderr)
    print('User Op file: ', user_op_file, file=sys.stderr)
    print('Name file: ', name_file, file=sys.stderr)
    print('Skip Energy: ', skip_energy, file=sys.stderr)

    if name_file:
        read_short_names(name_file)

    df = pd.DataFrame()  # empty df as start and keep appending in loop next
    for inputfile in inputfiles:
        print(inputfile, file=sys.stderr)
        if (input_format == 'csv'):
            input_data_source = sys.stdin if (inputfile == '-') else inputfile
            cur_df = pd.read_csv(input_data_source, delimiter=',')
        else:
            # Very subtle differnce between read_csv and read_excel about input files so need to call read() for stdin
            input_data_source = sys.stdin.buffer.read() if (inputfile == '-') else inputfile
            cur_df = pd.read_excel(input_data_source, sheet_name='QPROF_full')
        df = df.append(cur_df, ignore_index=True)

    df = df.sort_values(by=['codelet.name', 'decan_experimental_configuration.data_size', 'decan_experimental_configuration.num_core'])

    if user_op_file:
        key_columns=['codelet.name', 'decan_experimental_configuration.data_size']
        user_op_df = pd.read_csv(user_op_file, delimiter=',')
        user_op_columns = [col for col in user_op_df.columns if col not in key_columns]
        df = pd.merge(df, user_op_df, on=key_columns, how='left')
    else:
        user_op_columns = []

    user_op_col_name_dict={op_name: user_op_to_rate_column_name(op_name) for op_name in user_op_columns}
    field_names.extend(user_op_col_name_dict.values())

    df.columns = unify_column_names(df.columns)


    # Remove CQA columns if needed
    if no_cqa:
        script_dir=os.path.dirname(os.path.realpath(__file__))
        cqa_metric_file=os.path.join(script_dir, 'metrics_data','STAN')
        with open(cqa_metric_file) as f:
            cqa_metrics = f.read().splitlines()
            # Ignore error if extra CQA metrics in metrics_data/STAN
            df = df.drop(columns=cqa_metrics, errors='ignore')
        
    output_rows = list(df.apply(build_row_output, user_op_column_name_dict=user_op_col_name_dict, use_cpi=use_cpi, axis=1, skip_energy=skip_energy, skip_stalls=skip_stalls, succinct=succinct))

    if (outputfile == '-'):
        output_csvfile = sys.stdout
    else:
        output_csvfile = open (outputfile, 'w', newline='')

    output_fields = succinctify(field_names) if succinct else field_names

    output_fields = list(filter(field_has_values(output_rows), output_fields))
    csvwriter = csv.DictWriter(output_csvfile, fieldnames=output_fields)
    csvwriter.writeheader()
    for output_row in output_rows:
        csvwriter.writerow(enforce(output_row, output_fields))
    if (outputfile != '-'):
        output_csvfile.close()

def summary_formulas(formula_file_name):
    with open (formula_file_name, 'w') as formula_file:
        print_formulas(formula_file)

def read_short_names(filename):
    with open(filename, 'r') as infile:
        rows = list(csv.DictReader(infile, delimiter=','))
        for row in rows:
            if 'short_name' in row:
                short_names[row['name']] = row['short_name']
            if 'variant' in row:
                variants[row['name']] = row['variant']

if __name__ == '__main__':
    parser = ArgumentParser(description='Generate summary sheets from raw CAPE data.')
    parser.add_argument('-i', nargs='+', help='the input csv file', required=True, dest='in_files')
    parser.add_argument('-f', nargs='?', default='csv', help='format of input file (default csv can change to xlsx)', choices=['csv', 'xlsx'], dest='in_file_format')
    parser.add_argument('-o', nargs='?', default='out.csv', help='the output csv file (default out.csv)', dest='out_file')
    parser.add_argument('-x', nargs='?', help='a short-name and/or variant csv file', dest='name_file')
    parser.add_argument('-u', nargs='?', help='a user-defined operation count csv file', dest='user_op_file')
    parser.add_argument('--skip-stalls', action='store_true', help='skips calculating stall-related fields', dest='skip_stalls')
    parser.add_argument('--skip-energy', action='store_true', help='skips calculating power/energy-related fields', dest='skip_energy')
    parser.add_argument('--succinct', action='store_true', help='generate underscored, lowercase column names')
    parser.add_argument('--no-cqa', action='store_true', help='ignore CQA metrics in raw data')
    parser.add_argument('--use-cpi', action='store_true', help='use CPI metrics to compute time')
    args = parser.parse_args()


    summary_report(args.in_files, args.out_file, args.in_file_format, args.user_op_file, args.no_cqa, args.use_cpi, args.skip_energy, args.skip_stalls,
                   args.succinct, args.name_file)
formula_file_name = 'Formulas_used.txt'
summary_formulas(formula_file_name)
